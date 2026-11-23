#!/usr/bin/env bash
# 上架平台：PyPI（Python 客户端 SDK —— 供 Python Agent 调用 L2M）
# 需凭证：PYPI_TOKEN
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
source "$ROOT/publish/00_require.sh"
step "PyPI 发布 Python SDK"
require_env PYPI_TOKEN "PyPI API Token" || { warn_no_auth; exit 2; }
cd "$ROOT/sdk-python"
python3 -m pip install -q build twine
python3 -m build
TWINE_USERNAME=__token__ TWINE_PASSWORD="$PYPI_TOKEN" python3 -m twine upload dist/*
echo "[OK] https://pypi.org/project/legacy2modern/"
