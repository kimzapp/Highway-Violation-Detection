"""
Run Web Application
Starts the FastAPI backend server with frontend
"""

import os
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))


def main():
    import uvicorn
    
    print("=" * 60)
    print("  Highway Detection System - Web Application")
    print("=" * 60)
    print()
    print("Starting server at: http://localhost:8000")
    print("API documentation: http://localhost:8000/docs")
    print()
    print("Press Ctrl+C to stop the server")
    print("=" * 60)
    
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=[str(PROJECT_ROOT / "backend")]
    )


if __name__ == "__main__":
    main()
