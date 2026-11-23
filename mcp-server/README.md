# Legacy2Modern MCP Server —— 被调用即变现

> 一次构建，被所有支持 MCP 的 Agent 平台调用；每次调用自动扣点计费。
> 这是把「遗留代码现代化」能力变成 **Tool-as-a-Service** 的载体：巨头/Agent 调用一次，你赚一次。

## 零、两种传输入口 + 云部署

| 入口 | 命令 | 适用场景 |
|---|---|---|
| **stdio**（本地） | `node index.js` | Claude Code / Cursor / Gemini CLI 本机 IDE |
| **Streamable HTTP**（远程） | `node src/http-server.js` | Claude 网页版 / 远程 Agent，token 从请求头注入，谁调用谁付费 |
| **Cloudflare Workers**（公网免费） | 见 `../cloudflare/` | 全球边缘 10 万次/天免费，公网 URL 供各平台目录登记 |

令牌注入：stdio 用环境变量 `L2M_TOKEN`；HTTP/Worker 用 `Authorization: Bearer <TOKEN>` 请求头——每个调用者用自己的 token，后端按 token 精确扣点。

## 一、它解决什么问题

传统 API 要一家一家谈接入；MCP 是 AI 工具界的 USB-C——**一次发布，处处可调用**：

- 海外：Claude Code、Cursor、Gemini CLI、OpenCode、Cline、Windsurf 原生支持 MCP；
- 国内：火山方舟已支持 MCP 云部署（接入 200+ 工具），阿里魔搭开放 1.2 万个 MCP；
- 计费挂在后端账户体系上（MCP 协议本身不含计费），实现「免费发现 → 付费账户 → 按次扣点」。

## 二、工具清单与价格

| 工具名 | 功能 | 每次点数 | 谁会调用 |
|---|---|---:|---|
| `legacy-code-audit` | 技术债务/风险审计报告 | 2 | 所有 Coding Agent 接到老项目时 |
| `java8-to-springboot3` | 迁移路线图与改造清单 | 10 | 企业 AI 交付、FDE 驻场 |
| `jquery-to-vue3` | 前端现代化建议骨架 | 8 | 前端重构类 Agent |
| `dependency-risk-scan` | 依赖升级风险扫描 | 3 | CI/CD、DevOps Agent |
| `l2m-list-tools` | 免费列出工具目录与价格 | 0 | 任意 Agent 发现能力 |

> 参考换算：1 点 ≈ ¥0.01（可在后端 `MCP_TOOLS` 调整 cost）。注册赠送 100 点用于试用。

## 三、本地跑通（3 分钟）

### 前置：启动计费后端

```bash
cd Legacy2Modern/backend
pip install -r requirements.txt
AI_PROVIDER=mock python3 -m uvicorn app.main:app --port 8000
```

### 注册拿 token

```bash
curl -X POST http://127.0.0.1:8000/auth/register \
  -H "Content-Type: application/json" -d '{"email":"me@example.com"}'
# 返回 {"token":"<TOKEN>", "credits":100, ...} —— 复制 token
```

### 安装并验证 MCP Server

```bash
cd Legacy2Modern/mcp-server
npm install
L2M_TOKEN=<TOKEN> npm test
```

验证脚本会通过 stdio 连接 Server、列出工具、真实调用审计工具，并打印扣点后的账户余额。

## 四、接入各 Agent 平台

所有平台的配置本质相同：**用 node 启动 `index.js`，并注入 `L2M_TOKEN`（及可选 `L2M_API_URL`）环境变量**。把 `<绝对路径>` 替换为实际路径，`<TOKEN>` 替换为你的 token。

### Claude Code（CLI）

```bash
claude mcp add legacy2modern \
  --env L2M_TOKEN=<TOKEN> \
  --env L2M_API_URL=http://127.0.0.1:8000 \
  -- node /绝对路径/Legacy2Modern/mcp-server/index.js
```

### Cursor

`Settings → MCP → Add New Global MCP Server`，或编辑 `~/.cursor/mcp.json`：

```json
{
  "mcpServers": {
    "legacy2modern": {
      "command": "node",
      "args": ["/绝对路径/Legacy2Modern/mcp-server/index.js"],
      "env": { "L2M_TOKEN": "<TOKEN>", "L2M_API_URL": "http://127.0.0.1:8000" }
    }
  }
}
```

### Gemini CLI

编辑 `~/.gemini/settings.json`（结构与上面 `mcpServers` 相同）。

### Claude Desktop

编辑 `claude_desktop_config.json`（macOS: `~/Library/Application Support/Claude/`，Windows: `%APPDATA%\Claude\`），结构与 Cursor 相同。

> 更多平台配置样例见 `configs/` 目录。云部署（火山方舟/阿里百炼）时，把 stdio 换成 SSE/HTTP 传输，后端地址改为公网域名即可。

## 五、计费与结算链路

```
Agent 调用工具
   └─ MCP Server (stdio)
        └─ POST /mcp/invoke  { tool, params } + Bearer token
             ├─ 校验 token 与点数
             ├─ 执行分析（静态引擎 / 可切 AI 模型）
             ├─ 扣点 + 写入 mcp_calls 表
             └─ 返回结果 + credits_left
```

- **免费发现**：`l2m-list-tools` 不扣点，让 Agent 先知道你有什么能力；
- **按次扣点**：每次真实工具调用在后端原子扣点，支持点数不足时返回 HTTP 402；
- **结算升级**：点数可用 Stripe/微信支付充值，或接 x402 用 USDC 微支付（发挥 Web3 优势）。

## 六、目录结构

```
mcp-server/
├── index.js          # MCP Server 主体（4 个计费工具 + 1 个免费发现工具）
├── test-client.js     # 端到端验证客户端
├── package.json
├── README.md
└── configs/           # 各平台接入配置样例
```

## 七、从「调用」到「赚钱」的分发提醒

行业追踪显示 **不到 5% 的 MCP Server 真正赚到钱**——瓶颈不是技术，是分发。发布后务必：

1. 上架免费目录：MCP Registry、mcp.so、Smithery、PulseMCP、Glama（一次上架，跨平台可用）；
2. 内容获客：写「我如何让 Claude 自动审计 Java8 老系统」类文章，并做 GEO 让 AI 引用；
3. 企业授权：把高频调用客户转成万元级私有化/定制授权，小额调用赚广度、企业单赚深度。
