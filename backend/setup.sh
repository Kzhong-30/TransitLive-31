#!/usr/bin/env bash
set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$PROJECT_DIR/.venv"
REQUIRED_PYTHON="3.11"
FORCE_CURRENT_PYTHON=0

for arg in "$@"; do
    case "$arg" in
        --force-current-python)
            FORCE_CURRENT_PYTHON=1
            shift
            ;;
        -h|--help)
            cat <<EOF
Usage: $(basename "$0") [OPTIONS]

Options:
  --force-current-python    Use currently available python3 even if < 3.11
                            (for validating setup script flow in constrained envs)
  -h, --help                Show this help
EOF
            exit 0
            ;;
    esac
done

echo "============================================"
echo "Stock Market Data Service - Setup Script"
echo "============================================"

PYTHON_BIN=""
if command -v python3.11 &> /dev/null; then
    PYTHON_BIN="python3.11"
elif command -v python3 &> /dev/null && python3 -c "import sys; exit(0 if sys.version_info >= (3,11) else 1)" 2>/dev/null; then
    PYTHON_BIN="python3"
fi

if [ -z "$PYTHON_BIN" ] && [ "$FORCE_CURRENT_PYTHON" -eq 1 ]; then
    echo "[WARN] Python $REQUIRED_PYTHON+ not found; using current python3 due to --force-current-python"
    echo "       This is for validating setup script flow only. Production requires 3.11+."
    if command -v python3 &> /dev/null; then
        PYTHON_BIN="python3"
    elif command -v python &> /dev/null; then
        PYTHON_BIN="python"
    fi
fi

if [ -z "$PYTHON_BIN" ]; then
    echo "[ERROR] Python $REQUIRED_PYTHON+ is not installed or not in PATH."
    echo "  macOS:   brew install python@3.11"
    echo "  Ubuntu:  sudo apt install python3.11 python3.11-venv"
    echo "  Or install from https://www.python.org/downloads/"
    exit 1
fi

PY_VER="$($PYTHON_BIN -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")')"
echo "[OK] Using Python: $PY_VER (bin=$PYTHON_BIN)"

if [ -d "$VENV_DIR" ]; then
    EXISTING_VER="$("$VENV_DIR/bin/python" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")' 2>/dev/null || echo "unknown")"
    TARGET_VER="$("$PYTHON_BIN" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
    if [ "$EXISTING_VER" != "$TARGET_VER" ]; then
        echo "[WARN] Existing venv uses Python $EXISTING_VER but target is $TARGET_VER; removing stale venv"
        rm -rf "$VENV_DIR"
    fi
fi

if [ ! -d "$VENV_DIR" ]; then
    echo "[1/4] Creating virtual environment in .venv with $PY_VER ..."
    $PYTHON_BIN -m venv "$VENV_DIR"
else
    echo "[1/4] Virtual environment already exists, skipping creation."
fi

source "$VENV_DIR/bin/activate"
echo "[OK] Virtual environment activated."
echo "       venv python=$("$VENV_DIR/bin/python" --version)"

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
if [ "$FORCE_CURRENT_PYTHON" -eq 1 ]; then
    echo "  DEV MODE start:  cd $PROJECT_DIR && python dev_start.py"
    echo "  (Production requires Python 3.11+ via run.py)"
else
    echo "  Start service:   cd $PROJECT_DIR && python run.py"
    echo "  Or directly:     $VENV_DIR/bin/python $PROJECT_DIR/run.py"
fi
echo "  Swagger docs:    http://localhost:8000/docs"
echo "============================================"
