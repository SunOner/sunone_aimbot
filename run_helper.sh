#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

if [ ! -d ".venv" ]; then
  python3 -m venv .venv
fi

source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

if command -v npm >/dev/null 2>&1; then
  npm --prefix helper_ui install
  npm --prefix helper_ui run build
fi

python -m uvicorn helper_api:app --host 127.0.0.1 --port 8501
