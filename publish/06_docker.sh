#!/usr/bin/env bash
# 上架平台：Docker Hub（后端镜像）
# 需凭证：DOCKER_USER / DOCKER_TOKEN / DOCKER_REPO（如 yourname/legacy2modern）
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"; cd "$ROOT"
source publish/00_require.sh
step "Docker Hub 发布后端镜像"
require_env DOCKER_USER "Docker Hub 用户名" || { warn_no_auth; exit 2; }
require_env DOCKER_TOKEN "Docker Hub Access Token" || exit 2
require_env DOCKER_REPO "镜像仓库名 (user/repo)" || exit 2
echo "$DOCKER_TOKEN" | docker login -u "$DOCKER_USER" --password-stdin
docker build -t "$DOCKER_REPO:v0.2.0" -t "$DOCKER_REPO:latest" ./backend
docker push "$DOCKER_REPO:v0.2.0"
docker push "$DOCKER_REPO:latest"
echo "[OK] https://hub.docker.com/r/$DOCKER_REPO"
