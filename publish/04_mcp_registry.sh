#!/usr/bin/env bash
# 上架平台：MCP 官方 Registry（modelcontextprotocol.io/registry）
# 前置：npm 包已发布 + GitHub 仓库存在；需 GitHub OIDC 登录
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"; cd "$ROOT/mcp-server"
source "$ROOT/publish/00_require.sh"
step "MCP 官方 Registry 发布"
echo "前置校验：server.json 必须符合官方 schema"
python3 - <<'PY'
import json
d=json.load(open("server.json"))
assert len(d["description"])<=100
assert "REPLACE" not in json.dumps(d), "请先运行 render_config.sh 渲染 namespace"
print("[OK] server.json 通过")
PY
echo "==> 安装 mcp-publisher"
curl -L --max-time 60 "https://github.com/modelcontextprotocol/registry/releases/latest/download/mcp-publisher_Linux_x86_64.tar.gz" | tar xz mcp-publisher 2>/dev/null && chmod +x mcp-publisher || echo "下载失败，可手动从 GitHub Releases 下载"
echo "==> 用 GitHub OIDC 登录并发布（会打开浏览器授权）"
./mcp-publisher login github --github-oidc
./mcp-publisher publish
echo "[OK] 已提交至官方 Registry（审核合并后上线）"
