#!/usr/bin/env bash
# 全自动补齐上架：给定 NPM_TOKEN，自动写入 GitHub Secret → 触发发布 → 轮询结果
# 用法: NPM_TOKEN=npm_xxx bash publish/auto_complete.sh
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"; cd "$ROOT"
set -a; [ -f publish/.env ] && . publish/.env; set +a
GH_TOKEN="${GH_TOKEN:-}"; OWNER="${GITHUB_OWNER:-zhouhengchang}"
REPO="${OWNER}/legacy2modern-mcp"
NPM_TOKEN="${NPM_TOKEN:-}"
[ -z "$GH_TOKEN" ] && { echo "缺 GH_TOKEN"; exit 1; }
[ -z "$NPM_TOKEN" ] && { echo "用法: NPM_TOKEN=npm_xxx bash publish/auto_complete.sh"; exit 1; }
AUTH=(-H "Authorization: token ${GH_TOKEN}" -H "Accept: application/vnd.github+json")
API="https://api.github.com"

echo "==> 1. 获取仓库 public key"
PK=$(curl -s --max-time 20 "${AUTH[@]}" "$API/repos/$REPO/actions/secrets/public-key")
KEY_ID=$(echo "$PK" | python3 -c "import sys,json;print(json.load(sys.stdin)['key_id'])")
PUBKEY=$(echo "$PK" | python3 -c "import sys,json;print(json.load(sys.stdin)['key'])")

echo "==> 2. 加密 NPM_TOKEN（libsodium sealed box）"
ENC=$(python3 - "$PUBKEY" "$NPM_TOKEN" <<'PY'
import sys,base64
try:
    from nacl.public import PublicKey, SealedBox
except ImportError:
    print("需要 pynacl: pip install pynacl"); sys.exit(3)
pk=PublicKey(base64.b64decode(sys.argv[1]))
ct=SealedBox(pk).encrypt(sys.argv[2].encode())
print(base64.b64encode(ct).decode())
PY
)
[ -z "$ENC" ] && { echo "加密失败，请安装 pynacl"; exit 3; }

echo "==> 3. 写入 NPM_TOKEN secret"
curl -s --max-time 20 -X PUT "${AUTH[@]}" \
  "$API/repos/$REPO/actions/secrets/NPM_TOKEN" \
  -d "{\"encrypted_value\":\"$ENC\",\"key_id\":\"$KEY_ID\"}" -w "  HTTP:%{http_code}\n"

echo "==> 4. 触发发布 workflow"
curl -s -o /dev/null -w "  dispatch HTTP:%{http_code}\n" --max-time 20 -X POST "${AUTH[@]}" \
  "$API/repos/$REPO/actions/workflows/publish.yml/dispatches" -d '{"ref":"main"}'
sleep 10
RID=$(curl -s --max-time 20 "${AUTH[@]}" "$API/repos/$REPO/actions/runs?per_page=1" | python3 -c "import sys,json;print(json.load(sys.stdin)['workflow_runs'][0]['id'])")
echo "==> 5. 轮询结果 (run $RID)"
for i in $(seq 1 20); do
  ST=$(curl -s --max-time 15 "${AUTH[@]}" "$API/repos/$REPO/actions/runs/$RID" | python3 -c "import sys,json;d=json.load(sys.stdin);print(d['status'],d.get('conclusion') or '')")
  echo "  [$i] $ST"
  case "$ST" in *completed*) break;; esac
  sleep 15
done
echo "==> 完成。日志: https://github.com/$REPO/actions/runs/$RID"
