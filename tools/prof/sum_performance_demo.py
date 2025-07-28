import torch
import paddle
import numpy
import time

device = torch.device("cuda:0")
torch.set_default_device(device)
paddle.device.set_device('gpu:0')

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

# paddle.Tensor.sum(Tensor([16660, 28],"float32"), axis=1, )

m = 16660
n = 28
test_loop = 240662
numpy_tensor = (numpy.random.random([m, n]) - 0.5).astype("float32")
paddle_x, torch_x = init_input(numpy_tensor)
numel = (numpy_tensor.size)
test_loop = 2147483647 * 20 // numel
print("numel=", numel , "test_loop=", test_loop)


paddle_out = paddle.Tensor.sum(paddle_x, axis=1)

with paddle.no_grad():
    paddle.base.core._cuda_synchronize(paddle.CUDAPlace(0))
    start = time.time()
    for i in range(test_loop):
        paddle.Tensor.sum(paddle_x, axis=1)
    paddle.base.core._cuda_synchronize(paddle.CUDAPlace(0))
    end = time.time()
    timeused = end - start
    print("paddle forward", timeused)

numpy_tensor = (numpy.random.random([m]) - 0.5).astype("float32")
paddle_grad, torch_grad = init_input(numpy_tensor)

try:
    paddle.base.core._cuda_synchronize(paddle.CUDAPlace(0))
    start = time.time()
    for i in range(test_loop):
        paddle.grad([paddle_out], [paddle_x], grad_outputs=paddle_grad, allow_unused=True)
    paddle.base.core._cuda_synchronize(paddle.CUDAPlace(0))
    end = time.time()
    timeused = end - start
    print("paddle backward", timeused)
except Exception as e:
    print(f"paddle 反向失败")



torch_out = torch.Tensor.sum(torch_x, axis=1)
print(torch_out.shape)
with torch.no_grad():
    torch.cuda.synchronize()
    start = time.time()
    for i in range(test_loop):
        torch.Tensor.sum(torch_x, axis=1)
    torch.cuda.synchronize()
    end = time.time()
    timeused = end - start
    print("torch forward", timeused)
try:
    torch.cuda.synchronize()
    start = time.time()
    for i in range(test_loop):
        torch.autograd.grad([torch_out], [torch_x], grad_outputs=torch_grad, retain_graph=True)
    torch.cuda.synchronize()
    end = time.time()
    timeused = end - start
    print("torch backward", timeused)
except Exception as e:
    print(f"torch 反向失败")
