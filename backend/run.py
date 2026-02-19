# run.py - run from the backend folder: py run.py
import os
import sys
from pathlib import Path

# Ensure we're in the backend directory so "app" and db imports resolve
backend_dir = Path(__file__).resolve().parent
if os.getcwd() != str(backend_dir):
    os.chdir(backend_dir)
    sys.path.insert(0, str(backend_dir))

import uvicorn
from app.config import settings

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=False  # Set True for dev auto-reload; False avoids subprocess 404 issues
    )