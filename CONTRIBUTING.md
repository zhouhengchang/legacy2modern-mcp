# Contributing

欢迎为 Legacy2Modern 贡献代码、工具、文档或测试用例。

## 开发环境

- Node.js >= 18（MCP Server / VS Code 插件）
- Python 3.11（后端网关 / SDK）
- Docker（可选，本地一键编排）

## 本地启动

```bash
cp .env.example .env
# 方式一：Docker
docker compose up --build
# 方式二：本地进程
python3 -m uvicorn backend.app.main:app --port 8000
node mcp-server/index.js
```

## 提交规范

使用 Conventional Commits：`feat:` / `fix:` / `docs:` / `ci:` / `chore:` / `test:`。

## 新增一个计费工具

1. 在 `mcp-server/src/create-server.js` 注册工具并绑定计费动作。
2. 在 `backend/app/main.py` 的 `TOOL_COSTS` 中登记点数。
3. 在 `mcp-server/README.md` 更新工具清单。
4. 补充端到端测试（参考 `mcp-server/test-client.js`）。

## Pull Request

- 保持改动聚焦，一个 PR 一件事。
- 附上运行验证步骤与结果。
- 不要提交任何 `.env`、Token 或密钥文件（已被 `.gitignore` 排除）。
