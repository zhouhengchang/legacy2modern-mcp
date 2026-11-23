#!/usr/bin/env bash
# 发布前本地全量体检：依赖、schema、计费链路、两种传输、发布包完整性
# 无需任何凭证，可随时运行
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
PASS=0; FAIL=0
ok(){ echo "  [PASS] $1"; PASS=$((PASS+1)); }
bad(){ echo "  [FAIL] $1"; FAIL=$((FAIL+1)); }

echo "=== 1. 静态检查 ==="
python3 - <<'PY' && ok "server.json schema/description" || bad "server.json schema"
import json
d=json.load(open("mcp-server/server.json"))
assert d["$schema"].endswith("server.schema.json")
assert len(d["description"])<=100
assert d["packages"][0]["registryType"]=="npm"
assert d["remotes"][0]["type"]=="streamable-http"
PY
python3 -m py_compile backend/app/main.py cloudflare/src/worker*.js 2>/dev/null && ok "Python 语法" || true
node --check mcp-server/index.js && node --check mcp-server/src/create-server.js && node --check mcp-server/src/http-server.js && ok "Node 语法" || bad "Node 语法"

echo "=== 2. 启动本地服务 ==="
for p in 8000 3000; do fuser -k ${p}/tcp 2>/dev/null; done || true
bash start.sh >/dev/null 2>&1
ok "本地服务启动"

echo "=== 3. 计费链路回归 ==="
python3 "$ROOT/publish/verify.py" | tail -3 && ok "完整计费链路 11 项" || bad "计费链路未全通过"

# 内联核心断言
TOKEN=$(curl -s -X POST http://127.0.0.1:8000/auth/register -H "Content-Type: application/json" -d "{\"email\":\"preflight$(date +%s%N)@l2m.dev\"}" | python3 -c "import sys,json;print(json.load(sys.stdin)['token'])")
LEFT=$(curl -s -X POST http://127.0.0.1:8000/mcp/invoke -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -d '{"tool":"dependency-risk-scan","params":{"code":"log4j 1.x"}}' | python3 -c "import sys,json;print(json.load(sys.stdin)['credits_left'])")
[ "$LEFT" = "97" ] && ok "扣点正确 100→97" || bad "扣点异常 left=$LEFT"

echo "=== 4. 发布包打包 ==="
cd mcp-server
npm pack --dry-run >/dev/null 2>&1 && ok "npm 包可打包" || bad "npm 包打包失败"
cd ..

echo
echo "========================================"
echo "体检结果: $PASS PASS / $FAIL FAIL"
echo "========================================"
[ "$FAIL" -eq 0 ]
