"""
Highway Detection GUI Entry Point
Điểm khởi động giao diện người dùng
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gui.main_window import run_gui


def main():
    """Main entry point"""
    try:
        sys.exit(run_gui())
    except Exception as e:
        print(f"Error starting GUI: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
