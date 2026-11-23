/**
 * Legacy2Modern MCP Server — 工厂核心
 * ------------------------------------------------------------------
 * 导出 createServer(resolveToken) —— 每次工具调用时通过 resolveToken()
 * 取当前调用者的 token，实现「谁调用、谁付费」。stdio 从环境变量取，
 * HTTP/Worker 从请求头取。工具注册逻辑集中于此，供各传输入口复用。
 */
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { z } from "zod";

const API_URL = process.env.L2M_API_URL || "http://127.0.0.1:8000";

/** 通过后端统一计费入口调用工具。 */
async function invoke(resolveToken, tool, params) {
  const token = await resolveToken();
  if (!token) {
    throw new Error(
      "缺少调用凭证：请在请求头提供 Authorization: Bearer <TOKEN>（HTTP 模式），或设置 L2M_TOKEN 环境变量（stdio 模式）。注册：POST /auth/register"
    );
  }
  let resp;
  try {
    resp = await fetch(`${API_URL}/mcp/invoke`, {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${token}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ tool, params }),
    });
  } catch (e) {
    throw new Error(`无法连接计费后端 ${API_URL}: ${e.message}`);
  }
  const data = await resp.json().catch(() => ({}));
  if (!resp.ok) {
    throw new Error(`调用失败 (HTTP ${resp.status}): ${data.detail || JSON.stringify(data)}`);
  }
  return data;
}

const asText = (data) => ({
  content: [{ type: "text", text: JSON.stringify(data, null, 2) }],
});

/** 创建一个已注册全部工具的 MCP Server 实例。
 *  @param {() => string|Promise<string>} resolveToken 返回本次调用的 token
 */
export function createServer(resolveToken) {
  const server = new McpServer({ name: "legacy2modern", version: "0.2.0" });
  const call = (tool, params) => invoke(resolveToken, tool, params);

  server.tool(
    "legacy-code-audit",
    "遗留代码技术债务审计：输入代码，输出风险评分、问题清单与改进建议。Coding Agent 接到老项目时高频调用。（2 点/次）",
    { code: z.string().describe("待分析的源代码文本") },
    async ({ code }) => asText(await call("legacy-code-audit", { code }))
  );

  server.tool(
    "java8-to-springboot3",
    "检测 javax.*、Struts、XML 配置等遗留痕迹，生成 Java8→Spring Boot 3 分阶段迁移路线图。（10 点/次）",
    { code: z.string().describe("待分析的 Java 源代码") },
    async ({ code }) => asText(await call("java8-to-springboot3", { code }))
  );

  server.tool(
    "jquery-to-vue3",
    "识别 jQuery 选择器与事件写法，输出 Vue3 组合式 API 迁移建议骨架。（8 点/次）",
    { code: z.string().describe("待分析的 jQuery/JS 源代码") },
    async ({ code }) => asText(await call("jquery-to-vue3", { code }))
  );

  server.tool(
    "dependency-risk-scan",
    "输入 pom.xml / package.json 片段，识别过时与高危依赖，输出风险等级与升级建议。（3 点/次）",
    { manifest: z.string().describe("pom.xml 或 package.json 等依赖清单文本") },
    async ({ manifest }) => asText(await call("dependency-risk-scan", { code: manifest }))
  );

  server.tool(
    "l2m-list-tools",
    "免费：列出 Legacy2Modern 所有可调用工具及其点数价格与说明。",
    {},
    async () => {
      try {
        const resp = await fetch(`${API_URL}/mcp/tools`);
        return asText({ tools: await resp.json() });
      } catch (e) {
        return asText({ error: `无法连接 ${API_URL}: ${e.message}` });
      }
    }
  );

  return server;
}

export const getApiUrl = () => API_URL;
