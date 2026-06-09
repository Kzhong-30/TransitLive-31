#!/usr/bin/env python3
import sys
import os

MIN_PYTHON = (3, 11)
if sys.version_info < MIN_PYTHON:
    sys.stderr.write(
        f"[ERROR] Python {MIN_PYTHON[0]}.{MIN_PYTHON[1]} or higher is required. "
        f"Current version: {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}\n"
    )
    sys.stderr.write("Please install Python 3.11+ and create a virtual environment first.\n")
    sys.exit(1)

import uvicorn

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
