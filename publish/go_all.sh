#!/usr/bin/env bash
# Legacy2Modern 全平台上架总入口
#   bash publish/go_all.sh preflight   —— 无凭证全量体检
#   bash publish/go_all.sh all         —— 依次发布所有平台（缺凭证的自动跳过并提示）
#   bash publish/go_all.sh <平台名>     —— 单独发布某平台
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"; cd "$ROOT"

# 自动加载本地凭据文件（若存在），无需手动 export
ENV_FILE="$ROOT/publish/.env"
if [ -f "$ENV_FILE" ]; then
  set -a; . "$ENV_FILE"; set +a
  echo "[i] 已加载凭据文件 publish/.env"
else
  echo "[i] 未找到 publish/.env（可从 .env.example 复制），将只使用当前环境变量"
fi

CMD="${1:-preflight}"
case "$CMD" in
  preflight)
    bash publish/preflight.sh ;;
  cloudflare) bash publish/01_cloudflare.sh ;;
  npm)        bash publish/02_npm.sh ;;
  github)     bash publish/03_github.sh ;;
  registry)   bash publish/04_mcp_registry.sh ;;
  vscode)     bash publish/05_vscode.sh ;;
  docker)     bash publish/06_docker.sh ;;
  pypi)       bash publish/07_pypi.sh ;;
  all)
    echo "############ Legacy2Modern 全平台上架 ############"
    for s in 01_cloudflare 02_npm 03_github 04_mcp_registry 05_vscode 06_docker 07_pypi; do
      echo
      echo "########## $s ##########"
      bash "publish/$s.sh" || echo ">>> $s 跳过（凭证缺失或服务暂不可达）"
    done
    ;;
  *)
    echo "用法: bash publish/go_all.sh [preflight|all|cloudflare|npm|github|registry|vscode|docker|pypi]"
    ;;
esac
