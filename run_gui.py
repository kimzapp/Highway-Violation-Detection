"""
Highway Detection GUI Entry Point
Điểm khởi động giao diện người dùng
"""

import sys
import os
import multiprocessing


# Keep add_dll_directory handles alive for process lifetime.
_DLL_DIRECTORY_HANDLES = []


def get_base_path():
    """
    Get the base path for the application.
    Works for both normal Python execution and PyInstaller frozen executable.
    """
    if getattr(sys, 'frozen', False):
        # Running as compiled executable
        return os.path.dirname(sys.executable)
    else:
        # Running as script
        return os.path.dirname(os.path.abspath(__file__))


def _setup_windows_dll_search_paths(base_path: str):
    """Register DLL directories for bundled dependencies in frozen mode."""
    if os.name != 'nt' or not getattr(sys, 'frozen', False):
        return

    candidate_dirs = [
        base_path,
        os.path.join(base_path, '_internal'),
        os.path.join(base_path, '_internal', 'onnxruntime', 'capi'),
        os.path.join(base_path, '_internal', 'torch', 'lib'),
        os.path.join(base_path, '_internal', 'torch', 'bin'),
        os.path.join(base_path, '_internal', 'numpy.libs'),
        os.path.join(base_path, '_internal', 'scipy.libs'),
    ]

    # One-file mode may extract files to _MEIPASS instead of next to executable.
    meipass = getattr(sys, '_MEIPASS', None)
    if meipass:
        candidate_dirs.extend([
            meipass,
            os.path.join(meipass, 'onnxruntime', 'capi'),
            os.path.join(meipass, 'torch', 'lib'),
            os.path.join(meipass, 'torch', 'bin'),
            os.path.join(meipass, 'numpy.libs'),
            os.path.join(meipass, 'scipy.libs'),
        ])

    existing_dirs = []
    seen = set()
    for d in candidate_dirs:
        norm = os.path.normpath(d)
        if norm in seen:
            continue
        seen.add(norm)
        if os.path.isdir(norm):
            existing_dirs.append(norm)

    if hasattr(os, 'add_dll_directory'):
        for dll_dir in existing_dirs:
            try:
                _DLL_DIRECTORY_HANDLES.append(os.add_dll_directory(dll_dir))
            except OSError:
                # Ignore directories that cannot be registered.
                pass

    # Keep PATH in sync as fallback for subprocesses/older loaders.
    current_path = os.environ.get('PATH', '')
    path_parts = [p for p in current_path.split(os.pathsep) if p]
    for dll_dir in reversed(existing_dirs):
        if dll_dir not in path_parts:
            path_parts.insert(0, dll_dir)
    os.environ['PATH'] = os.pathsep.join(path_parts)


def setup_environment():
    """
    Setup environment for both development and frozen (PyInstaller) mode.
    """
    base_path = get_base_path()
    
    # Add base path to sys.path for module imports
    if base_path not in sys.path:
        sys.path.insert(0, base_path)
    
    # Set working directory to base path
    os.chdir(base_path)
    
    # Disable PyTorch JIT compilation in frozen mode to avoid issues
    if getattr(sys, 'frozen', False):
        os.environ['PYTORCH_JIT'] = '0'
        
        # Set OpenCV to not use GUI threading issues
        os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = ''

        # Ensure bundled runtime DLLs can be found on Windows.
        _setup_windows_dll_search_paths(base_path)
        
    return base_path


def main():
    """Main entry point"""
    # CRITICAL: Must be called at the very beginning for Windows multiprocessing
    # This is required for PyInstaller frozen executables
    multiprocessing.freeze_support()
    
    # Setup paths and environment
    setup_environment()
    
    try:
        from gui.main_window import run_gui
        sys.exit(run_gui())
    except Exception as e:
        # Show error in a message box if GUI is available
        try:
            from PyQt5.QtWidgets import QApplication, QMessageBox
            app = QApplication(sys.argv)
            QMessageBox.critical(
                None, 
                "Lỗi khởi động",
                f"Không thể khởi động ứng dụng:\n\n{str(e)}\n\n"
                "Vui lòng kiểm tra:\n"
                "1. Các file DLL cần thiết\n"
                "2. Model weights có sẵn\n"
                "3. Quyền truy cập thư mục"
            )
        except:
            print(f"Error starting GUI: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
