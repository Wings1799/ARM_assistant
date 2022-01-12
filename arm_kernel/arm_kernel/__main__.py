from ipykernel.kernelapp import IPKernelApp
from . import ArmKernel

IPKernelApp.launch_instance(kernel_class=ArmKernel)
