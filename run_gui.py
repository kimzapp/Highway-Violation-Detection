"""
Highway Detection GUI Entry Point
Điểm khởi động giao diện người dùng
"""

import sys
import os
import multiprocessing


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
