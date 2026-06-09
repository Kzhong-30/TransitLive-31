#!/usr/bin/env bash
set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$PROJECT_DIR/.venv"
REQUIRED_PYTHON="3.11"

echo "============================================"
echo "Stock Market Data Service - Setup Script"
echo "============================================"

PYTHON_BIN=""
if command -v python3.11 &> /dev/null; then
    PYTHON_BIN="python3.11"
elif command -v python3 &> /dev/null && python3 -c "import sys; exit(0 if sys.version_info >= (3,11) else 1)" 2>/dev/null; then
    PYTHON_BIN="python3"
fi

if [ -z "$PYTHON_BIN" ]; then
    echo "[ERROR] Python $REQUIRED_PYTHON+ is not installed or not in PATH."
    echo "  macOS:   brew install python@3.11"
    echo "  Ubuntu:  sudo apt install python3.11 python3.11-venv"
    echo "  Or install from https://www.python.org/downloads/"
    exit 1
fi

echo "[OK] Found Python: $($PYTHON_BIN --version)"

if [ ! -d "$VENV_DIR" ]; then
    echo "[1/4] Creating virtual environment in .venv ..."
    $PYTHON_BIN -m venv "$VENV_DIR"
else
    echo "[1/4] Virtual environment already exists, skipping creation."
fi

source "$VENV_DIR/bin/activate"
echo "[OK] Virtual environment activated."

echo "[2/4] Upgrading pip ..."
pip install --upgrade pip -q

echo "[3/4] Installing dependencies from requirements.txt ..."
pip install -r "$PROJECT_DIR/requirements.txt"

if [ ! -f "$PROJECT_DIR/.env" ]; then
    echo "[4/4] Creating .env from .env.example ..."
    cp "$PROJECT_DIR/.env.example" "$PROJECT_DIR/.env"
else
    echo "[4/4] .env already exists, skipping."
fi

echo ""
echo "============================================"
echo "Setup complete! Quick start commands:"
echo "============================================"
echo "  Activate venv:   source $VENV_DIR/bin/activate"
echo "  Start service:   cd $PROJECT_DIR && python run.py"
echo "  Or directly:     $VENV_DIR/bin/python $PROJECT_DIR/run.py"
echo "  Swagger docs:    http://localhost:8000/docs"
echo "============================================"
