# Legacy2Modern — AI 遗留代码现代化 SaaS（MVP 骨架）

> 遗留代码现代化 AI 智能体平台的最小可运行闭环。包含：AI 重构后端 + VS Code 插件 + Web 控制台 + Docker 部署配置。
> 当前为 **MVP 骨架**：AI 调用默认走 mock，配置密钥后自动切换真实模型；支付/Web3 为后续扩展点。

## 一、项目结构

```
Legacy2Modern/
├── backend/            # FastAPI 后端
│   ├── app/main.py     # 用户体系 / 点数计费 / 重构 Agent 接口
│   ├── requirements.txt
│   └── Dockerfile
├── extension/          # VS Code 插件（TypeScript）
│   ├── package.json
│   ├── tsconfig.json
│   └── src/extension.ts
├── mcp-server/         # MCP Server（被调用即变现，v0.2 新增）
│   ├── index.js        # 4 个计费工具 + 1 个免费发现工具
│   ├── test-client.js  # 端到端验证客户端
│   ├── README.md       # 接入各 Agent 平台说明
│   └── configs/        # Claude/Cursor/Gemini 接入配置样例
├── web/                # Web 控制台（单文件，无需构建）
│   └── index.html
├── docker-compose.yml  # 一键编排 backend + web
├── .env.example        # 环境变量样例
└── README.md
```

## 二、快速启动（Docker 一键）

```bash
cd Legacy2Modern
cp .env.example .env
docker compose up --build
# 后端 API: http://localhost:8000  (文档 http://localhost:8000/docs)
# Web 控制台: http://localhost:8080
```

## 三、本地开发启动（不用 Docker）

```bash
# 1) 后端
python3 -m venv .venv && source .venv/bin/activate
pip install -r backend/requirements.txt
cd backend && python -m uvicorn app.main:app --reload --port 8000

# 2) Web 控制台：直接浏览器打开 web/index.html
#    （需先启动后端，控制台默认连 8000 端口）
```

## 四、核心 API

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/auth/register` | 邮箱注册，返回 token 并赠 100 点数 |
| POST | `/refactor` | 提交代码 + 源/目标栈，消耗点数，返回重构结果 |
| GET | `/me` | 当前用户信息与点数 |
| GET | `/jobs` | 重构历史任务 |
| GET | `/mcp/tools` | MCP 工具目录（免费发现，v0.2） |
| POST | `/mcp/invoke` | MCP 工具统一调用入口（校验 token → 扣点 → 返回结果） |
| GET | `/mcp/stats` | 当前账户 MCP 调用统计与累计消耗（v0.2） |
| GET | `/health` | 健康检查 |

调用示例：

```bash
# 注册拿 token
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" -d '{"email":"me@example.com"}'

# 重构（把 <TOKEN> 换成上一步返回的 token）
curl -X POST http://localhost:8000/refactor \
  -H "Authorization: Bearer <TOKEN>" -H "Content-Type: application/json" \
  -d '{"source_code":"public class A {}","from_stack":"java8","to_stack":"springboot3"}'
```

## 五、接入真实 AI 模型

复制 `.env.example` 为 `.env`，按需修改：

- `AI_PROVIDER=ollama`：需本地运行 Ollama 并拉取 `deepseek-coder` 模型；
- `AI_PROVIDER=deepseek`：填入 `DEEPSEEK_API_KEY`，走 DeepSeek-Coder 云端 API；
- `AI_PROVIDER=mock`（默认）：不调用模型，返回带标注的原代码，用于演示与联调。

## 六、VS Code 插件安装

```bash
cd extension
npm install
npm run compile
# 调试：VS Code 打开 extension 目录，F5 启动扩展开发宿主
# 打包：npx @vscode/vsce package （生成 .vsix）
```

插件命令（Ctrl+Shift+P）：
- `Legacy2Modern: 登录` — 输入邮箱获取 token
- `Legacy2Modern: 重构选中代码` — 选中代码 → 选目标栈 → 结果在新标签页打开

## 六（附）、MCP Server —— 被调用即变现

```bash
cd mcp-server && npm install
# 注册后端拿 token 后：
L2M_TOKEN=<TOKEN> npm test
# 把 index.js 配入 Claude Code / Cursor / Gemini CLI（见 mcp-server/README.md）
```

已实现 4 个计费工具（`legacy-code-audit` 2 点 / `java8-to-springboot3` 10 点 / `jquery-to-vue3` 8 点 / `dependency-risk-scan` 3 点）+ 1 个免费发现工具。每次调用经后端 `/mcp/invoke` 自动扣点并落库——**一次构建，被所有支持 MCP 的 Agent 平台调用，调用一次赚一次**。

## 七、商业化扩展点（ roadmap ）

- [x] MCP 被调用变现网关（`/mcp/tools` `/mcp/invoke` `/mcp/stats` + 4 个计费工具，已实现并验证）
- [ ] 支付：接入 USDC/USDT 链上支付、点数充值订单
- [ ] Web3 登录：钱包签名鉴权（ERC-4361 / SIWE）、账户抽象 ERC-4337
- [ ] 计费：Stripe / 微信支付订阅，团队席位管理
- [ ] Agent 增强：多智能体协作（审计→迁移→测试→回归）、RAG 迁移知识库
- [ ] 私有化部署：企业离线镜像 + 本地模型（Ollama）一键脚本
- [ ] 可观测：任务成功率、点数消耗、Token 成本监控

## 八、技术说明

- 后端使用 SQLite（零配置），生产可切 PostgreSQL（改 `db()` 连接即可）；
- `/refactor` 为同步演示接口，生产建议改为任务队列（Celery/RQ）+ 轮询；
- 默认开放 CORS 便于本地联调，生产需收敛为白名单域名。

---
*Generated as MVP skeleton — 可运行、可扩展、可商业化。*
