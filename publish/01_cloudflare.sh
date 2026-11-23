#!/usr/bin/env bash
# 上架平台：Cloudflare Workers（计费后端公网网关，正式版带持久化 KV）
# 需凭证：CLOUDFLARE_API_TOKEN（含 Workers Scripts:Edit + Workers KV Storage:Edit）
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"; cd "$ROOT"
source publish/00_require.sh
step "Cloudflare Workers 正式部署（持久化 KV）"
require_env CLOUDFLARE_API_TOKEN "Cloudflare API Token" || { warn_no_auth; exit 2; }
# 创建 KV namespace（幂等：已存在则复用 ID）
echo "==> 确保 KV namespace 存在"
KV_ID=$(npx wrangler kv namespace list 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print(next((x['id'] for x in d if x['title']=='legacy2modern-kv'),''))" 2>/dev/null || true)
if [ -z "$KV_ID" ]; then
  KV_ID=$(npx wrangler kv namespace create legacy2modern-kv 2>/dev/null | grep -oP 'id = "\K[^"]+' | head -1)
fi
echo "KV_ID=$KV_ID"
cat > cloudflare/wrangler.toml <<EOF
name = "legacy2modern-mcp"
main = "src/worker.js"
compatibility_date = "2026-01-01"

[[kv_namespaces]]
binding = "L2M"
id = "$KV_ID"
EOF
step "部署"
cd cloudflare && npx wrangler deploy 2>&1 | tee "$ROOT/publish/.cloudflare.url"
URL=$(grep -oP 'https://\S+\.workers\.dev' "$ROOT/publish/.cloudflare.url" | head -1)
echo "公网 URL: $URL"
echo "$URL" > "$ROOT/publish/.public_url"
step "固化公网 URL 到配置"
cd "$ROOT"
bash publish/render_config.sh "${GITHUB_OWNER:-REPLACEUSER}" "$(echo "$URL" | sed -E 's#https://([^.]+).*#\1#')" || true
step "公网自检"
curl -s "$URL/health"; echo
