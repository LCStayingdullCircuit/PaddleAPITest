import torch
import paddle
import numpy
import time

device = torch.device("cuda:0")
torch.set_default_device(device)

# paddle.device.set_device('cpu')

def init_input(numpy_tensor):
    paddle_x = paddle.to_tensor(numpy_tensor)
    torch_x = torch.tensor(numpy_tensor, requires_grad=True)
    paddle_x.stop_gradient = False

    numpy.testing.assert_allclose(
        paddle_x.numpy(),
        torch_x.cpu().detach().numpy(),
        1e-10,
        1e-10,
        err_msg='intput diff'
    )
    return paddle_x, torch_x

test_loop = 34591
#  paddle.sum(Tensor([6017, 32, 896],"bfloat16"), axis=1, keepdim=False, ) 
numpy_tensor = (numpy.random.random([6017, 32, 896]) - 0.5).astype("float32")
paddle_x, torch_x = init_input(numpy_tensor)
paddle_x = paddle.cast(paddle_x, dtype="uint16")
torch_x = torch_x.to(dtype=torch.bfloat16)

paddle_out = paddle.sum(paddle_x, axis=1, keepdim=False, ) 

with paddle.no_grad():
    paddle.base.core._cuda_synchronize(paddle.CUDAPlace(0))
    start = time.time()
    for i in range(test_loop):
        paddle.sum(paddle_x, axis=1, keepdim=False, )
    paddle.base.core._cuda_synchronize(paddle.CUDAPlace(0))
    end = time.time()
    timeused = end - start
    print("paddle forward", timeused)

numpy_tensor = (numpy.random.random(paddle_out.shape) - 0.5).astype("float32")
paddle_grad, torch_grad = init_input(numpy_tensor)
paddle_grad = paddle.cast(paddle_grad, dtype="uint16")
torch_grad = torch_grad.to(dtype=torch.bfloat16)

paddle.base.core._cuda_synchronize(paddle.CUDAPlace(0))
start = time.time()
for i in range(test_loop):
    paddle.grad([paddle_out], [paddle_x], grad_outputs=paddle_grad, allow_unused=True)
paddle.base.core._cuda_synchronize(paddle.CUDAPlace(0))
end = time.time()
timeused = end - start
print("paddle backward", timeused)

torch_out = torch.sum(torch_x, dim=1, keepdim=False)

with torch.no_grad():
    torch.cuda.synchronize()
    start = time.time()
    for i in range(test_loop):
        torch.sum(torch_x, dim=1, keepdim=False)
    torch.cuda.synchronize()
    end = time.time()
    timeused = end - start
    print("torch forward", timeused)

torch.cuda.synchronize()
start = time.time()
for i in range(test_loop):
    torch.autograd.grad([torch_out], [torch_x], grad_outputs=torch_grad, retain_graph=True)
torch.cuda.synchronize()
end = time.time()
timeused = end - start
print("torch backward", timeused)