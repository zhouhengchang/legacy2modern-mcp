#!/usr/bin/env bash
# 上架平台：GitHub 仓库 + Release
# 方式：REST API（仅需 repo scope，不依赖 gh CLI 的 read:org 要求）
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"; cd "$ROOT"
source publish/00_require.sh
step "GitHub 仓库 + Release 发布"
require_env GH_TOKEN "GitHub Personal Access Token (repo scope)" || { warn_no_auth; exit 2; }
require_env GITHUB_OWNER "GitHub 用户名（namespace）" || { echo "请设置 GITHUB_OWNER"; exit 2; }

REPO="$GITHUB_OWNER/legacy2modern-mcp"
VERSION="${VERSION:-$(node -p 'require("./mcp-server/package.json").version')}"
API="https://api.github.com"
AUTH=(-H "Authorization: token ${GH_TOKEN}" -H "Accept: application/vnd.github+json")

echo "==> 渲染 namespace"
bash publish/render_config.sh "$GITHUB_OWNER" "${WORKER_SUB:-legacy2modern-mcp}" >/dev/null

echo "==> 检查/创建仓库 $REPO"
CODE=$(curl -s -o /tmp/l2m_repo.json -w "%{http_code}" --max-time 20 "${AUTH[@]}" "$API/repos/$REPO")
if [ "$CODE" = "404" ]; then
  curl -s --max-time 30 -X POST "${AUTH[@]}" "$API/user/repos" \
    -d '{"name":"legacy2modern-mcp","description":"MCP server and metered API gateway for legacy code modernization","public":true,"auto_init":false}' \
    | python3 -c "import sys,json;d=json.load(sys.stdin);print('  创建:',d.get('full_name') or d.get('message'))"
else
  echo "  仓库已存在 (HTTP $CODE)"
fi

echo "==> 推送代码"
git config user.name "$GITHUB_OWNER" 2>/dev/null || true
git config user.email "${GITHUB_OWNER}@users.noreply.github.com" 2>/dev/null || true
git add -A 2>/dev/null || true
git diff --cached --quiet 2>/dev/null || git commit -qm "chore: sync publish config $(date +%Y%m%d-%H%M)" 2>/dev/null || true
git branch -M main 2>/dev/null || true
git remote remove origin 2>/dev/null || true
git remote add origin "https://${GITHUB_OWNER}:${GH_TOKEN}@github.com/${REPO}.git"
git push -u origin main 2>&1 | tail -3
git remote set-url origin "https://github.com/${REPO}.git"

echo "==> 创建 tag + Release v$VERSION"
SHA=$(curl -s --max-time 20 "${AUTH[@]}" "$API/repos/$REPO/commits/main" | python3 -c "import sys,json;print(json.load(sys.stdin)['sha'])")
curl -s --max-time 20 -X POST "${AUTH[@]}" "$API/repos/$REPO/git/refs" \
  -d "{\"ref\":\"refs/tags/v${VERSION}\",\"sha\":\"$SHA\"}" >/dev/null 2>&1 || echo "  tag 已存在"
curl -s --max-time 30 -X POST "${AUTH[@]}" "$API/repos/$REPO/releases" \
  -d "{\"tag_name\":\"v${VERSION}\",\"name\":\"Legacy2Modern v${VERSION}\",\"body\":\"MCP server + metered API for legacy code modernization.\",\"draft\":false,\"prerelease\":false}" \
  | python3 -c "import sys,json;d=json.load(sys.stdin);print('  Release:',d.get('html_url') or d.get('message'))"

echo "[OK] https://github.com/$REPO/releases/tag/v$VERSION"
