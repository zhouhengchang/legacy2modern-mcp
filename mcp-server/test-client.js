/**
 * 端到端验证：用 MCP 客户端通过 stdio 连接本 Server，调用工具。
 * 用法：
 *   L2M_TOKEN=<你的token> node test-client.js
 */
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";

const API_URL = process.env.L2M_API_URL || "http://127.0.0.1:8000";
const TOKEN = process.env.L2M_TOKEN || "";

const transport = new StdioClientTransport({
  command: "node",
  args: ["index.js"],
  cwd: process.cwd(),
  env: { ...process.env, L2M_API_URL: API_URL, L2M_TOKEN: TOKEN },
  stderr: "inherit",
});

const client = new Client({ name: "l2m-verifier", version: "1.0.0" });
await client.connect(transport);

console.log("=== 1. 工具列表 ===");
const listed = await client.listTools();
for (const t of listed.tools) {
  console.log(` - ${t.name}: ${t.description.slice(0, 52)}…`);
}

const sample = [
  "var x = 1;",
  "if (x == '1') { eval('x++'); }",
  "// TODO fix this",
  'password = "123456";',
  "System.out.println(x);",
].join("\n");

console.log("\n=== 2. 调用 legacy-code-audit（应扣 2 点）===");
const r1 = await client.callTool({
  name: "legacy-code-audit",
  arguments: { code: sample },
});
console.log(JSON.stringify(JSON.parse(r1.content[0].text), null, 2));

console.log("\n=== 3. 调用 l2m-list-tools（免费发现）===");
const r2 = await client.callTool({ name: "l2m-list-tools", arguments: {} });
console.log(JSON.stringify(JSON.parse(r2.content[0].text), null, 2));

console.log("\n=== 4. 再次查询账户，核对点数 ===");
const r3 = await fetch(`${API_URL}/me`, {
  headers: { Authorization: `Bearer ${TOKEN}` },
}).then((r) => r.json());
console.log(JSON.stringify(r3, null, 2));

await client.close();
console.log("\n验证完成。");
