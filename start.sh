#!/usr/bin/env bash
# Legacy2Modern 一键启动：计费后端 + MCP HTTP 端点（本地常驻，可对外）
# 用法: bash start.sh [--public]
set -e
ROOT="$(cd "$(dirname "$0")" && pwd)"
BACKEND="$ROOT/backend"
MCP="$ROOT/mcp-server"
LOG_DIR="$ROOT/.logs"
mkdir -p "$LOG_DIR"

echo "==> 检查 Python 依赖"
python3 -c "import fastapi,uvicorn,pydantic" 2>/dev/null || pip3 install -q -r "$BACKEND/requirements.txt"

echo "==> 启动计费后端 :8000"
cd "$BACKEND"
AI_PROVIDER="${AI_PROVIDER:-mock}" nohup python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 > "$LOG_DIR/backend.log" 2>&1 &
echo $! > "$LOG_DIR/backend.pid"

echo "==> 启动 MCP Streamable HTTP 端点 :3000"
cd "$MCP"
[ -d node_modules ] || npm install --no-audit --no-fund >/dev/null 2>&1
L2M_API_URL="${L2M_API_URL:-http://127.0.0.1:8000}" PORT="${PORT:-3000}" \
  nohup node src/http-server.js > "$LOG_DIR/mcp-http.log" 2>&1 &
echo $! > "$LOG_DIR/mcp-http.pid"

sleep 3
echo "==> 健康检查"
curl -s http://127.0.0.1:8000/health && echo
curl -s http://127.0.0.1:3000/health && echo

echo "==> 对外暴露（可选）"
if [ "${1:-}" = "--public" ]; then
  if command -v cloudflared >/dev/null 2>&1; then
    echo "cloudflared 已安装，启动隧道："
    cloudflared tunnel --url http://127.0.0.1:3000
  else
    echo "未安装 cloudflared。安装后执行: cloudflared tunnel --url http://127.0.0.1:3000"
    echo "或: npx localtunnel --port 3000 / ngrok http 3000"
  fi
else
  echo "本地模式。需要公网 URL 时: bash start.sh --public"
fi
echo "停止服务: kill \$(cat $LOG_DIR/backend.pid) \$(cat $LOG_DIR/mcp-http.pid)"
