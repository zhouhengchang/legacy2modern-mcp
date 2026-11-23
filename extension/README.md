# Legacy2Modern — AI 遗留代码重构助手

在 VS Code 中选中遗留代码，一键调用 Legacy2Modern Agent 迁移到现代技术栈（Spring Boot 3 / Vue 3 / Python 3）。

## 功能

- **Legacy2Modern: 登录** — 输入邮箱注册/登录，自动赠送 100 点数并保存 token。
- **Legacy2Modern: 重构选中代码** — 选中代码 → 选择目标栈 → 在新标签页打开重构结果。

## 配置

| 配置项 | 默认值 | 说明 |
|---|---|---|
| `legacy2modern.apiBase` | `http://localhost:8000` | 后端 API 地址 |
| `legacy2modern.token` | 空 | 登录 token（登录后自动填入） |

## 前置条件

需先启动 Legacy2Modern 后端（见仓库根目录 README）。默认连接 `http://localhost:8000`。

## 打包

```bash
npm install
npm run compile
npx @vscode/vsce package
# 生成 legacy2modern-1.0.0.vsix
```

> 正式发布到 VS Code Marketplace 需账号本人的 Publisher 身份（替换 `package.json` 中的 `publisher` 字段）与 `VSCE_PAT`。
