#!/usr/bin/env bash
# 上架平台：npm Registry（MCP Server 安装包）
# 需凭证：NPM_TOKEN（publish 权限）
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"; cd "$ROOT"
source publish/00_require.sh
step "npm Registry 发布 MCP Server"
require_env NPM_TOKEN "npm Access Token" || { warn_no_auth; exit 2; }
echo "//registry.npmjs.org/:_authToken=${NPM_TOKEN}" > ~/.npmrc
cd mcp-server
echo "==> 版本: $(node -p 'require(\"./package.json\").version')"
npm publish --access public
echo "[OK] 已发布 https://www.npmjs.com/package/@legacy2modern/mcp-server"
