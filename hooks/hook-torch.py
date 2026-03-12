"""
Custom PyInstaller hook for torch
Ensures all torch DLLs and binaries are properly collected
"""

import os
import sys
from PyInstaller.utils.hooks import collect_dynamic_libs, collect_data_files

# Collect all dynamic libraries from torch
binaries = collect_dynamic_libs('torch')

# Collect data files
datas = collect_data_files('torch')

# Additional hidden imports that might be missed
hiddenimports = [
    'torch',
    'torch._C',
    'torch._utils',
    'torch.utils',
    'torch.utils.data',
    'torch.cuda',
    'torch.cuda.amp',
    'torch.backends',
    'torch.backends.cudnn',
    'torch.nn',
    'torch.nn.functional',
    'torch.autograd',
    'torch.jit',
    'torch.onnx',
    'torch.distributions',
]

# Try to find and add torch lib directory explicitly
try:
    import torch
    torch_path = os.path.dirname(torch.__file__)
    lib_path = os.path.join(torch_path, 'lib')
    
    if os.path.exists(lib_path):
        for file in os.listdir(lib_path):
            if file.endswith(('.dll', '.pyd', '.so')):
                full_path = os.path.join(lib_path, file)
                binaries.append((full_path, 'torch/lib'))
except Exception as e:
    print(f"Warning: Could not collect torch libs: {e}")
