# Legacy2Modern

> **遗留代码现代化 AI Agent / MCP 计费网关** — 把代码审计与框架迁移做成任意 AI Agent 都能调用的付费能力，按调用计费，一次构建、全生态变现。

[![version](https://img.shields.io/badge/version-1.0.0-blue)](https://github.com/zhouhengchang/legacy2modern-mcp/releases/tag/v1.0.0)
[![license](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![tests](https://github.com/zhouhengchang/legacy2modern-mcp/actions/workflows/test.yml/badge.svg)](https://github.com/zhouhengchang/legacy2modern-mcp/actions/workflows/test.yml)

- 🌐 **产品官网**：https://zhouhengchang.github.io/legacy2modern-mcp/
- 📖 **在线 API 文档**：https://zhouhengchang.github.io/legacy2modern-mcp/api.html
- 🐳 **容器镜像**：`ghcr.io/zhouhengchang/legacy2modern-backend:latest`
- 📦 **源码 / Release**：https://github.com/zhouhengchang/legacy2modern-mcp

## 核心能力

| 能力 | 说明 |
|---|---|
| MCP 计费网关 | 4 个计费工具 + 1 个免费发现工具，调用经 `/mcp/invoke` 校验点数→分析→扣点→落库 |
| 双传输 | stdio（本地编辑器直连）+ Streamable HTTP（云端 Agent 远程调用） |
| 静态分析引擎 | 无需 AI 密钥即可给出技术债务、迁移路线、依赖风险的可执行结果 |
| AI 可插拔 | mock / Ollama / DeepSeek，配置即切换；未配置密钥自动降级 mock |
| 统一账本 | 注册发 token、调用扣点、任务留痕，MCP 与 Web 共用 SQLite 账本 |

### 计费工具

| 工具 | 点数 | 用途 |
|---|---|---|
| `legacy-code-audit` | 2 | 遗留代码技术债务审计 |
| `java8-to-springboot3` | 10 | Java8 → Spring Boot 3 迁移路线图 |
| `jquery-to-vue3` | 8 | jQuery → Vue3 现代化建议 |
| `dependency-risk-scan` | 3 | 依赖升级风险扫描 |
| `l2m-list-tools` | 免费 | 工具发现 |

点数不足返回 `HTTP 402 Payment Required`。

## 目录结构

```
Legacy2Modern/
├── backend/               # FastAPI 计费网关 + SQLite
│   ├── app/main.py        # 鉴权 / 计费 / MCP 工具 / AI 可插拔
│   ├── tests/             # 19 个自动化测试（pytest，含并发竞态）
│   ├── requirements*.txt  # 运行 / 开发依赖
│   └── Dockerfile
├── mcp-server/            # MCP Server（stdio + HTTP）
│   ├── index.js
│   ├── src/create-server.js
│   ├── test-client.js
│   └── configs/           # Claude / Cursor / Gemini 接入样例
├── extension/             # VS Code 插件（TypeScript）
├── web/                   # Web 控制台（单文件）
├── sdk-python/            # Python SDK（legacy2modern）
├── docs/                  # GitHub Pages 官网 + api.html + openapi.json
├── publish/               # 多平台上架脚本（凭证预检 + 幂等）
└── .github/workflows/     # publish / docker-publish / ghpackages / test
```

## 快速启动

```bash
cp .env.example .env
docker compose up --build
# API: http://localhost:8000  (Swagger: /docs)
# Web 控制台: http://localhost:8080
```

或本地开发：

```bash
pip install -r backend/requirements.txt
cd backend && python -m uvicorn app.main:app --reload --port 8000
```

## MCP 接入

```bash
cd mcp-server && npm install
L2M_TOKEN=<TOKEN> npm test
# 把 index.js 配入 Claude Code / Cursor / Gemini CLI（见 mcp-server/README.md）
```

stdio 配置示例：

```json
{
  "mcpServers": {
    "legacy2modern": {
      "command": "node",
      "args": ["path/to/l2m-mcp/index.js"],
      "env": { "L2M_API_URL": "http://localhost:8000", "L2M_TOKEN": "<token>" }
    }
  }
}
```

## Python SDK

```bash
pip install legacy2modern
```

```python
from legacy2modern import L2MClient
c = L2MClient(token="...")          # 或 base_url 指向公网网关
c.register("me@example.com")        # 注册领 100 点
r = c.audit("var a=1; if(a==b) TODO")
print(r["credits_left"])
```

## 测试

```bash
pip install -r backend/requirements-dev.txt
cd backend && python -m pytest tests/ -q   # 19 passed
```

CI（`.github/workflows/test.yml`）在每次 push 自动运行同一套测试。

## 发布状态

| 平台 | 状态 |
|---|---|
| GitHub 仓库 / Release v1.0.0 / Actions | ✅ 已上线 |
| GitHub Pages 官网 + API 文档 | ✅ 已上线 |
| GitHub Container Registry 镜像 | ✅ 已上线（Public） |
| GitHub Packages npm 包 | ✅ 已上线（Public） |
| npmjs.org / MCP 官方 Registry | ◐ 待 `NPM_TOKEN` |
| Cloudflare / PyPI / VS Code / Docker Hub | ◐ 待各自本人 Token |

补齐任一 Token 到 `publish/.env` 后执行对应脚本即可上架；全部填好后 `bash publish/go_all.sh all` 一次跑通。拿到 `NPM_TOKEN` 后 `NPM_TOKEN=npm_xxx bash publish/auto_complete.sh` 可自动完成 npmjs.org + MCP Registry。详见 `publish/.env.example`。

## 商业化路线图

- [x] MCP 被调用变现网关 + 4 个计费工具
- [x] 双传输 / Web 控制台 / VS Code 插件 / Python SDK
- [x] 自动化测试 + CI + 在线文档
- [ ] 支付：USDC/USDT 链上充值、订阅与团队席位
- [ ] Web3 登录：SIWE（ERC-4361）、账户抽象 ERC-4337
- [ ] Agent 增强：多智能体协作（审计→迁移→测试→回归）、RAG 迁移知识库
- [ ] 私有化部署：企业离线镜像 + 本地模型

## 许可

MIT © 2026 zhouhengchang
