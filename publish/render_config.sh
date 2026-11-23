#!/usr/bin/env bash
# 把占位符 REPLACEUSER / REPLACE_WORKER 渲染成真实账号与公网 URL
# 用法: bash render_config.sh <github-owner> <worker-subdomain>
#   github-owner   : 你的 GitHub 用户名，如 zhangsan
#   worker-subdomain: Cloudflare Worker 正式部署后的子域前缀，如 legacy2modern-mcp
set -e
OWNER="${1:-}"
SUB="${2:-legacy2modern-mcp}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
if [ -z "$OWNER" ]; then
  echo "用法: bash publish/render_config.sh <github-owner> [worker-subdomain]"; exit 1
fi
cd "$ROOT"

echo "==> 渲染 namespace -> io.github.$OWNER/legacy2modern"
for f in mcp-server/package.json mcp-server/server.json mcp-server/README.md \
         mcp-server/configs/*.json mcp-server/.github/workflows/publish.yml; do
  [ -f "$f" ] || continue
  sed -i "s/REPLACEUSER/$OWNER/g" "$f"
  sed -i "s/REPLACE_WORKER/$SUB/g" "$f"
done

echo "==> 渲染完成，校验无残留占位符"
if grep -rl "REPLACE" mcp-server --exclude-dir=node_modules 2>/dev/null | grep -v "render_config" ; then
  echo "[警告] 仍有占位符残留（见上）"
else
  echo "[OK] 无占位符残留"
fi
echo "==> 校验 server.json schema"
python3 - "$OWNER" <<'PY'
import json,sys
owner=sys.argv[1]
d=json.load(open("mcp-server/server.json"))
assert d["name"]==f"io.github.{owner}/legacy2modern", d["name"]
assert len(d["description"])<=100, "description 超过 100 字符"
assert "REPLACE" not in json.dumps(d), "仍有 REPLACE 占位符"
print("[OK] server.json 合法, name="+d["name"]+", desc长度="+str(len(d["description"])))
PY
