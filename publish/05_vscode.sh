#!/usr/bin/env bash
# 上架平台：VS Code Marketplace（IDE 插件）
# 需凭证：VSCE_PAT（Azure DevOps Personal Access Token）
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"; cd "$ROOT/extension"
source "$ROOT/publish/00_require.sh"
step "VS Code Marketplace 发布插件"
require_env VSCE_PAT "Azure DevOps PAT (Marketplace publish)" || { warn_no_auth; exit 2; }
npm install --no-audit --no-fund >/dev/null 2>&1 || true
npx tsc -p ./ 2>&1 | head -5 || echo "编译提示（继续）"
npx @vscode/vsce package -o legacy2modern.vsix
npx @vscode/vsce publish --pat "$VSCE_PAT"
echo "[OK] https://marketplace.visualstudio.com/items?itemName=legacy2modern.legacy2modern"
