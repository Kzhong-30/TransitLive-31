#!/usr/bin/env python3
"""Development launch script - skips Python 3.11 version gate for local testing.

Intended for contributors who want to run the service on older Python versions
during feature development. Production deployments MUST use `python run.py`
with Python 3.11+ to ensure compatibility with target environments.

The 3.11 syntax upgrade path: once CI and local environments have Python 3.11,
all if/elif chains marked with `# py311-upgrade: match-case` can be upgraded
automatically via `pyupgrade --py311-plus`.
"""
import sys
import os
import warnings

DEVELOPMENT_WARNING = (
    "Running in DEVELOPMENT mode with Python {ver}. "
    "Production requires Python 3.11+ via `run.py`. "
    "Some 3.11 syntax features are backported via typing_extensions "
    "and exceptiongroup for compatibility."
)

warnings.warn(
    DEVELOPMENT_WARNING.format(
        ver=f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    ),
    stacklevel=1,
)

import uvicorn

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
