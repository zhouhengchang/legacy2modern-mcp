#!/usr/bin/env bash
# 公共函数库：凭证预检 / 日志
require_env(){
  local var="$1" desc="$2"
  if [ -z "${!var}" ]; then
    echo "[缺凭证] 环境变量 $var 未设置 —— $desc"
    return 1
  fi
  echo "[OK] $desc"
}
step(){ echo; echo "---- $* ----"; }
warn_no_auth(){ echo "本平台必须本人账号授权，无法由第三方代登录。请设置所需环境变量后重跑本脚本。"; }
