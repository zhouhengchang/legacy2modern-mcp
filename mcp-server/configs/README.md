# 平台接入配置样例说明

本目录提供主流 Agent 平台的 MCP 接入配置样例：

| 文件 | 适用平台 | 放置位置 |
|------|---------|---------|
| `cursor-mcp.json` | Cursor | `~/.cursor/mcp.json` |
| `claude-desktop-config.json` | Claude Desktop | macOS `~/Library/Application Support/Claude/claude_desktop_config.json`；Windows `%APPDATA%\Claude\claude_desktop_config.json` |
| `gemini-cli-settings.json` | Gemini CLI / OpenCode / Cline / Windsurf（结构通用） | `~/.gemini/settings.json` 等 |

Claude Code 用 CLI 命令接入（见主 README）：

```bash
claude mcp add legacy2modern \
  --env L2M_TOKEN=<TOKEN> \
  --env L2M_API_URL=http://127.0.0.1:8000 \
  -- node /绝对路径/Legacy2Modern/mcp-server/index.js
```

**两个必改项**：
1. `/绝对路径/...` → 替换为本机 `index.js` 的真实绝对路径；
2. `<TOKEN>` → 替换为 `POST /auth/register` 返回的 token。

**云部署**（火山方舟 / 阿里百炼 MCP 广场）：把 stdio 传输改为 SSE / HTTP 传输，`L2M_API_URL` 指向公网后端域名，即可让平台侧云端 Agent 调用。
