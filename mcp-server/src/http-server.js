/**
 * Node HTTP 入口：Streamable HTTP 传输，可被远程客户端 / Claude 网页连接器调用。
 * 每个请求的 token 从 Authorization 头注入 —— 谁调用谁付费。
 *
 * 启动: node src/http-server.js
 * 端点: POST/GET/DELETE http://host:3000/mcp
 */
import http from "node:http";
import { StreamableHTTPServerTransport } from "@modelcontextprotocol/sdk/server/streamableHttp.js";
import { createServer } from "./create-server.js";

const PORT = process.env.PORT || 3000;

/** 从请求头提取 Bearer token。 */
function tokenFromReq(req) {
  const h = req.headers.authorization || "";
  return h.startsWith("Bearer ") ? h.slice(7).trim() : "";
}

function readBody(req) {
  return new Promise((resolve, reject) => {
    let data = "";
    req.on("data", (c) => (data += c));
    req.on("end", () => resolve(data));
    req.on("error", reject);
  });
}

const server = http.createServer(async (req, res) => {
  // 健康检查
  if (req.url === "/health") {
    res.writeHead(200, { "Content-Type": "application/json" });
    res.end(JSON.stringify({ status: "ok", transport: "streamable-http" }));
    return;
  }
  if (req.url !== "/mcp") {
    res.writeHead(404); res.end("Not found"); return;
  }

  // CORS（远程客户端需要）
  res.setHeader("Access-Control-Allow-Origin", "*");
  res.setHeader("Access-Control-Allow-Methods", "GET,POST,DELETE,OPTIONS");
  res.setHeader("Access-Control-Allow-Headers", "Content-Type, Authorization, Mcp-Session-Id");
  if (req.method === "OPTIONS") { res.writeHead(204); res.end(); return; }

  try {
    const token = tokenFromReq(req);
    let body;
    if (req.method === "POST") body = JSON.parse((await readBody(req)) || "{}");

    // 无状态模式：每个请求创建独立 server + transport，token 注入到该请求闭包
    const mcp = createServer(() => token);
    const transport = new StreamableHTTPServerTransport({
      sessionIdGenerator: undefined, // stateless
      enableJsonResponse: true,
    });
    res.on("close", () => transport.close());
    await mcp.connect(transport);
    await transport.handleRequest(req, res, body);
  } catch (e) {
    if (!res.headersSent) {
      res.writeHead(500, { "Content-Type": "application/json" });
      res.end(JSON.stringify({ error: e.message }));
    }
    process.stderr.write(`[http-server] error: ${e.message}\n`);
  }
});

server.listen(PORT, () => {
  process.stderr.write(`Legacy2Modern MCP (Streamable HTTP) listening on :${PORT}/mcp\n`);
});
