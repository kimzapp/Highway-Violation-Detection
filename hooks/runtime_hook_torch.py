"""
PyInstaller runtime hook for torch
Sets up the environment before torch is imported
"""

import os
import sys


def _setup_torch_paths():
    """
    Setup DLL search paths for torch when running from PyInstaller bundle.
    This is critical for c10.dll and other torch dependencies.
    """
    if not getattr(sys, 'frozen', False):
        return
    
    # Get the directory where the executable is located
    if hasattr(sys, '_MEIPASS'):
        # Running from PyInstaller bundle
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(sys.executable)
    
    # Add torch lib directories to DLL search path
    torch_lib_paths = [
        os.path.join(base_path, 'torch', 'lib'),
        os.path.join(base_path, 'torch'),
        os.path.join(base_path),
    ]
    
    # On Windows, use os.add_dll_directory (Python 3.8+)
    if sys.platform == 'win32' and hasattr(os, 'add_dll_directory'):
        for path in torch_lib_paths:
            if os.path.exists(path):
                try:
                    os.add_dll_directory(path)
                except Exception:
                    pass
    
    # Also add to PATH environment variable as fallback
    env_path = os.environ.get('PATH', '')
    for path in torch_lib_paths:
        if os.path.exists(path) and path not in env_path:
            os.environ['PATH'] = path + os.pathsep + env_path
            env_path = os.environ['PATH']


# Run setup when this hook is loaded
_setup_torch_paths()
