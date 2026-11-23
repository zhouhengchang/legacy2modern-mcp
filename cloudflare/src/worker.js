/**
 * Legacy2Modern 计费后端 — Cloudflare Workers 版
 * ------------------------------------------------------------------
 * 免费额度：10 万请求/天。用 KV 存用户/点数/调用记录，替代本地 SQLite。
 * 与 Python 后端 API 完全兼容（/auth/register /mcp/tools /mcp/invoke /mcp/stats /me /health），
 * 让全球 Agent 通过公网 URL 调用并自动计费。
 *
 * 部署：wrangler deploy  （需 Cloudflare 账号，用户授权）
 */
const MCP_TOOLS = {
  "legacy-code-audit": { title: "遗留代码技术债务审计", description: "输出风险评分、问题清单与改进建议", cost: 2 },
  "java8-to-springboot3": { title: "Java8→Spring Boot 3 迁移路线图", description: "生成分阶段迁移步骤与改造清单", cost: 10 },
  "jquery-to-vue3": { title: "jQuery→Vue3 前端现代化", description: "输出组合式 API 迁移建议骨架", cost: 8 },
  "dependency-risk-scan": { title: "依赖升级风险扫描", description: "识别过时与高危依赖并给出风险等级", cost: 3 },
};

const json = (data, status = 200) =>
  new Response(JSON.stringify(data), { status, headers: { "Content-Type": "application/json", "Access-Control-Allow-Origin": "*" } });

function tokenOf(req) {
  const h = req.headers.get("Authorization") || "";
  return h.startsWith("Bearer ") ? h.slice(7).trim() : "";
}
const hex = () => crypto.randomUUID().replace(/-/g, "");

function analyze(tool, code = "") {
  const lines = code.split("\n");
  const nloc = lines.filter((l) => l.trim() && !/^\s*(\/\/|#|\*|\/\*)/.test(l)).length;
  const base = { tool, engine: "static-analysis", lines: lines.length, nloc };
  const hits = (re) => (code.match(re) || []).length;
  if (tool === "legacy-code-audit") {
    const checks = [[/\bvar\s+/g, "遗留 var 声明"], [/==(?!=)/g, "松散相等 =="], [/TODO|FIXME|HACK/g, "遗留待办标记"],
      [/System\.out\.print/g, "控制台输出未清理"], [/printStackTrace/g, "异常仅打印堆栈"],
      [/(password|secret)\s*[=:]\s*["'][^"']+/gi, "疑似硬编码凭据"], [/\beval\s*\(/g, "使用 eval"]];
    const issues = checks.map(([re, d]) => ({ issue: d, hits: hits(re) })).filter((x) => x.hits);
    const score = Math.max(0, 100 - issues.reduce((s, x) => s + x.hits * 8, 0));
    return { ...base, summary: "遗留代码技术债务审计完成", risk_score: score, risk_level: score < 60 ? "高" : score < 85 ? "中" : "低", issues };
  }
  if (tool === "java8-to-springboot3") {
    const detected = [[/javax\./g, "javax.*→jakarta.*"], [/struts/gi, "Struts 遗留框架"], [/web\.xml/g, "XML 配置迁移"]]
      .map(([re, p]) => ({ pattern: p, hits: hits(re) })).filter((x) => x.hits);
    const roadmap = [1, 2, 3, 4].map((phase) => ({ phase, name: ["依赖与命名空间", "配置迁移", "框架替换", "回归验证"][phase - 1] }));
    return { ...base, summary: "Java8→Spring Boot 3 迁移路线图生成完成", detected, roadmap, estimated_phases: 4 };
  }
  if (tool === "jquery-to-vue3") {
    const detected = [[/\$\(\s*["']#/g, "ID 选择器→ref"], [/\$\(document\)\.ready/g, "ready→onMounted"], [/\.ajax\s*\(/g, "$.ajax→fetch"]]
      .map(([re, p]) => ({ pattern: p, hits: hits(re) })).filter((x) => x.hits);
    return { ...base, summary: "jQuery→Vue3 建议生成完成", detected, vue3_skeleton: "<script setup>\nimport { ref, onMounted } from 'vue'\n</script>" };
  }
  if (tool === "dependency-risk-scan") {
    const findings = [];
    if (/log4j.*1\./i.test(code)) findings.push({ risk: "高", item: "Log4j 1.x (EOL)" });
    if (/fastjson/i.test(code)) findings.push({ risk: "高", item: "Fastjson 反序列化风险" });
    if (/jquery.*1\./i.test(code)) findings.push({ risk: "中", item: "jQuery 1.x 过时" });
    const level = findings.some((f) => f.risk === "高") ? "高" : findings.length ? "中" : "低";
    return { ...base, summary: "依赖升级风险扫描完成", risk_level: level, findings };
  }
  return { ...base, summary: "未知工具" };
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const KV = env.L2M;
    // 健康检查
    if (url.pathname === "/health") return json({ status: "ok", ai_provider: "worker", mcp_tools: Object.keys(MCP_TOOLS).length });
    // 工具目录（免费发现）
    if (url.pathname === "/mcp/tools" && request.method === "GET") {
      return json(Object.entries(MCP_TOOLS).map(([name, m]) => ({ name, ...m })));
    }
    // 注册
    if (url.pathname === "/auth/register" && request.method === "POST") {
      const { email } = await request.json();
      const token = hex(), uid = hex();
      await KV.put(`token:${token}`, JSON.stringify({ id: uid, email, token, credits: 100 }));
      return json({ user_id: uid, token, credits: 100 });
    }
    // 鉴权辅助
    const authed = async () => {
      const t = tokenOf(request);
      const raw = t && await KV.get(`token:${t}`);
      return raw ? JSON.parse(raw) : null;
    };
    // 当前用户
    if (url.pathname === "/me") {
      const u = await authed(); return u ? json(u) : json({ detail: "Invalid token" }, 401);
    }
    // 统一计费调用
    if (url.pathname === "/mcp/invoke" && request.method === "POST") {
      const u = await authed();
      if (!u) return json({ detail: "Invalid token" }, 401);
      const { tool, params = {} } = await request.json();
      const meta = MCP_TOOLS[tool];
      if (!meta) return json({ detail: `Unknown tool: ${tool}` }, 404);
      if (u.credits < meta.cost) return json({ detail: `Insufficient credits: need ${meta.cost}, have ${u.credits}` }, 402);
      const result = analyze(tool, String(params.code || ""));
      const callId = hex();
      u.credits -= meta.cost;
      await KV.put(`token:${u.token}`, JSON.stringify(u));
      await KV.put(`call:${u.id}:${callId}`, JSON.stringify({ tool, cost: meta.cost, result, ts: Date.now() }));
      return json({ call_id: callId, tool, result, cost: meta.cost, credits_left: u.credits });
    }
    // 统计
    if (url.pathname === "/mcp/stats") {
      const u = await authed();
      if (!u) return json({ detail: "Invalid token" }, 401);
      const list = await KV.list({ prefix: `call:${u.id}:` });
      const byTool = {};
      for (const k of list.keys) {
        const c = JSON.parse(await KV.get(k.name));
        byTool[c.tool] = byTool[c.tool] || { tool: c.tool, calls: 0, spent: 0 };
        byTool[c.tool].calls++; byTool[c.tool].spent += c.cost;
      }
      return json({ by_tool: Object.values(byTool), credits_left: u.credits });
    }
    // CORS 预检
    if (request.method === "OPTIONS") return new Response(null, { headers: { "Access-Control-Allow-Origin": "*", "Access-Control-Allow-Headers": "Content-Type, Authorization", "Access-Control-Allow-Methods": "GET,POST,OPTIONS" } });
    return json({ detail: "Not found" }, 404);
  },
};
