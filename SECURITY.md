# Security Policy

## 支持的版本

| 版本 | 支持状态 |
|---|---|
| 1.0.x | 支持 |

## 报告漏洞

请勿在公开 Issue 中披露安全漏洞。通过 GitHub 私有漏洞报告（Security Advisories）或仓库所有者邮箱提交，包含：

- 影响的版本与组件
- 复现步骤
- 潜在影响
- 建议的修复（如有）

我们会在确认后尽快响应并发布修复版本。

## 凭据处理约定

- 所有平台 Token（npm / PyPI / Cloudflare / VS Code / Docker Hub）必须由账号本人在对应平台生成，禁止写入仓库或日志文件。
- `publish/.env` 已被 `.gitignore` 排除，仅本地保存，权限 600。
- GitHub Actions 中的密钥通过仓库 Secrets 管理，代码中仅引用 `${{ secrets.* }}`。
- 计费网关的 Bearer Token 仅用于调用鉴权，服务端不记录明文。

## 不计入安全边界的事项

- 平台强制的人机验证（如 npmjs.com Turnstile）与本人登录要求属于平台机制，非本项目缺陷，本项目不绕过。
