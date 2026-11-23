#!/usr/bin/env bash
# 上架平台：GitHub（源码仓库 + Release + tag 触发 npm/MCP Registry 自动发布）
# 需凭证：GH_TOKEN（repo 权限）
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"; cd "$ROOT"
source publish/00_require.sh
step "GitHub 仓库 + Release 发布"
require_env GH_TOKEN "GitHub Personal Access Token" || { warn_no_auth; exit 2; }
require_env GITHUB_OWNER "GitHub 用户名（namespace）" || { echo "请设置 GITHUB_OWNER=你的用户名"; exit 2; }
echo "$GH_TOKEN" | gh auth login --with-token
bash publish/render_config.sh "$GITHUB_OWNER" "${WORKER_SUB:-legacy2modern-mcp}"
REPO="$GITHUB_OWNER/legacy2modern-mcp"
gh repo create "$REPO" --public --source=. --remote=origin --push 2>/dev/null || echo "仓库已存在，走更新"
git add -A && git commit -m "release: v0.2.0 MCP server + publish kit" 2>/dev/null || true
git push -u origin HEAD 2>/dev/null || true
VERSION=$(node -p 'require("./mcp-server/package.json").version')
gh release create "v$VERSION" \
  Legacy2Modern-MCP上架包.zip \
  --title "Legacy2Modern v$VERSION" \
  --generate-notes 2>/dev/null || echo "Release 已存在"
echo "[OK] https://github.com/$REPO/releases/tag/v$VERSION"
echo "[i] tag 推送后 .github/workflows/publish.yml 将自动发布 npm + MCP Registry"
