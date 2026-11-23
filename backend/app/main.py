"""
Legacy2Modern Backend — 遗留代码现代化 AI Agent SaaS 后端
技术栈: Python FastAPI + SQLite(可切 PostgreSQL) + Ollama/DeepSeek(可降级 mock)

v0.2: 新增 MCP 网关 —— 工具目录 / 按次计费调用 / 调用统计，
      让任意 MCP 客户端（Claude Code / Cursor / Gemini CLI / 火山方舟 / 阿里百炼）
      调用工具时自动扣点，实现「被调用即变现」。
"""
from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sqlite3, os, uuid, time, json, re

app = FastAPI(title="Legacy2Modern API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)

DB_PATH = os.getenv("DB_PATH", "legacy2modern.db")
AI_PROVIDER = os.getenv("AI_PROVIDER", "mock")  # mock | ollama | deepseek
COST_PER_REFACTOR = int(os.getenv("COST_PER_REFACTOR", "10"))

# MCP 工具目录：cost 为每次调用消耗的点数（1 点 ≈ ¥0.01 参考）
MCP_TOOLS = {
    "legacy-code-audit": {
        "title": "遗留代码技术债务审计",
        "description": "输入代码，输出技术债务/风险报告：过时写法、安全痕迹、可维护性评分。任何 Coding Agent 接到老项目时高频调用。",
        "cost": 2,
    },
    "java8-to-springboot3": {
        "title": "Java8 → Spring Boot 3 迁移路线图",
        "description": "检测 javax.*、Struts、XML 配置等遗留痕迹，生成分阶段迁移步骤与改造清单。企业 AI 交付/FDE 驻场场景。",
        "cost": 10,
    },
    "jquery-to-vue3": {
        "title": "jQuery → Vue3 前端现代化",
        "description": "识别 jQuery 选择器与事件写法，输出组合式 API 迁移建议骨架。前端重构类 Agent 调用。",
        "cost": 8,
    },
    "dependency-risk-scan": {
        "title": "依赖升级风险扫描",
        "description": "输入 pom.xml / package.json 片段，识别过时与高危依赖模式，输出风险等级与升级建议。CI/CD、DevOps Agent 调用。",
        "cost": 3,
    },
}


def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with db() as c:
        c.execute("""CREATE TABLE IF NOT EXISTS users(
            id TEXT PRIMARY KEY, email TEXT UNIQUE, token TEXT UNIQUE,
            credits INTEGER DEFAULT 100, created_at REAL)""")
        c.execute("""CREATE TABLE IF NOT EXISTS jobs(
            id TEXT PRIMARY KEY, user_id TEXT, source TEXT, target TEXT,
            status TEXT, result TEXT, cost INTEGER, created_at REAL)""")
        c.execute("""CREATE TABLE IF NOT EXISTS mcp_calls(
            id TEXT PRIMARY KEY, user_id TEXT, tool TEXT, cost INTEGER,
            result TEXT, created_at REAL)""")
        c.commit()


@app.on_event("startup")
def _startup():
    init_db()


def auth(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Missing bearer token")
    token = authorization.split(" ", 1)[1]
    with db() as c:
        row = c.execute("SELECT * FROM users WHERE token=?", (token,)).fetchone()
    if not row:
        raise HTTPException(401, "Invalid token")
    return dict(row)


class RegisterIn(BaseModel):
    email: str


@app.post("/auth/register")
def register(body: RegisterIn):
    uid, token = uuid.uuid4().hex, uuid.uuid4().hex
    try:
        with db() as c:
            c.execute("INSERT INTO users VALUES(?,?,?,?,?)",
                      (uid, body.email, token, 100, time.time()))
            c.commit()
    except sqlite3.IntegrityError:
        raise HTTPException(400, "Email already registered")
    return {"user_id": uid, "token": token, "credits": 100}


class RefactorIn(BaseModel):
    source_code: str
    from_stack: str = "java8"
    to_stack: str = "springboot3"


def call_ai(code: str, from_stack: str, to_stack: str) -> str:
    """按配置调用 AI；未配置密钥时自动降级为 mock，保证本地可运行。"""
    if AI_PROVIDER == "ollama":
        try:
            import requests
            prompt = f"将以下 {from_stack} 代码迁移到 {to_stack}，仅输出代码:\n{code}"
            r = requests.post("http://localhost:11434/api/generate",
                              json={"model": "deepseek-coder", "prompt": prompt,
                                    "stream": False}, timeout=120)
            return r.json().get("response", code)
        except Exception as e:
            return f"// [ollama fallback] {e}\n" + code
    if AI_PROVIDER == "deepseek":
        key = os.getenv("DEEPSEEK_API_KEY")
        if key:
            try:
                import requests
                r = requests.post("https://api.deepseek.com/v1/chat/completions",
                    headers={"Authorization": f"Bearer {key}"},
                    json={"model": "deepseek-coder", "messages": [
                        {"role": "user", "content": f"迁移{from_stack}->{to_stack}:\n{code}"}]},
                    timeout=120)
                return r.json()["choices"][0]["message"]["content"]
            except Exception as e:
                return f"// [deepseek fallback] {e}\n" + code
    # mock：演示用，标注清晰
    return (f"// [MOCK Refactor {from_stack}->{to_stack}]\n"
            f"// 生产环境请配置 AI_PROVIDER=ollama 或 deepseek\n"
            f"// 原代码行数: {len(code.splitlines())}\n\n{code}")


@app.post("/refactor")
def refactor(body: RefactorIn, user: dict = Depends(auth)):
    if user["credits"] < COST_PER_REFACTOR:
        raise HTTPException(402, "Insufficient credits")
    jid = uuid.uuid4().hex
    result = call_ai(body.source_code, body.from_stack, body.to_stack)
    with db() as c:
        c.execute("INSERT INTO jobs VALUES(?,?,?,?,?,?,?,?)",
                  (jid, user["id"], body.source_code, body.to_stack,
                   "done", result, COST_PER_REFACTOR, time.time()))
        c.execute("UPDATE users SET credits=credits-? WHERE id=?",
                  (COST_PER_REFACTOR, user["id"]))
        c.commit()
        left = c.execute("SELECT credits FROM users WHERE id=?", (user["id"],)).fetchone()[0]
    return {"job_id": jid, "status": "done", "result": result, "credits_left": left}


# ------------------------- MCP 网关：被调用即变现 -------------------------

def _code_stats(code: str) -> dict:
    lines = code.splitlines()
    nloc = len([l for l in lines
                if l.strip() and not l.strip().startswith(("//", "#", "/*", "*", "<!--"))])
    return {"lines": len(lines), "nloc": nloc}


def _analyze(tool: str, code: str, params: dict) -> dict:
    """四个 MCP 工具的分析逻辑（无密钥也能给出真实可用的静态结果）。"""
    stats = _code_stats(code)
    base = {"tool": tool, "engine": "static-analysis", **stats}

    if tool == "legacy-code-audit":
        checks = [
            (r"\bvar\s+", "遗留 var 声明（建议 let/const 或强类型）"),
            (r"==(?!=)", "松散相等 ==（潜在类型强制转换问题）"),
            (r"TODO|FIXME|HACK|XXX", "遗留待办/临时标记"),
            (r"System\.out\.print", "控制台输出未清理"),
            (r"printStackTrace", "异常仅打印堆栈，缺少处理"),
            (r"(?i)(password|passwd|secret)\s*[=:]\s*[\"'][^\"']+", "疑似硬编码凭据"),
            (r"\beval\s*\(", "使用 eval（安全风险）"),
            (r"new\s+Date\s*\(", "旧日期 API（建议 java.time / dayjs）"),
        ]
        issues = []
        for pat, desc in checks:
            hits = len(re.findall(pat, code))
            if hits:
                issues.append({"issue": desc, "hits": hits})
        score = max(0, 100 - sum(i["hits"] * 8 for i in issues))
        level = "高" if score < 60 else "中" if score < 85 else "低"
        return {**base, "summary": "遗留代码技术债务审计完成",
                "risk_score": score, "risk_level": level,
                "issues": issues,
                "recommendation": "优先处理安全类问题（硬编码凭据/eval），再分模块替换过时写法。"}

    if tool == "java8-to-springboot3":
        checks = [
            (r"javax\.", "javax.* 命名空间 → 需改 jakarta.*"),
            (r"org\.apache\.struts|struts", "Struts 遗留框架痕迹"),
            (r"web\.xml", "XML 配置 → 建议改为 Java Config / 注解"),
            (r"extends\s+HttpServlet", "Servlet 直接继承 → 建议 Spring MVC Controller"),
            (r"new\s+Date\s*\(|SimpleDateFormat", "旧日期 API → java.time"),
            (r"@RequestMapping", "检查是否需拆分为 @GetMapping/@PostMapping"),
        ]
        found = []
        for pat, desc in checks:
            hits = len(re.findall(pat, code))
            if hits:
                found.append({"pattern": desc, "hits": hits})
        roadmap = [
            {"phase": 1, "name": "依赖与命名空间", "action": "升级 pom.xml 至 Spring Boot 3，全局替换 javax→jakarta"},
            {"phase": 2, "name": "配置迁移", "action": "web.xml 迁移为 application.yml + Java Config"},
            {"phase": 3, "name": "框架替换", "action": "Struts/Servlet 改为 Spring MVC，统一异常与返回值"},
            {"phase": 4, "name": "回归验证", "action": "补集成测试，容器化后灰度发布"},
        ]
        return {**base, "summary": "Java8→Spring Boot 3 迁移路线图生成完成",
                "detected": found, "roadmap": roadmap,
                "estimated_phases": len(roadmap)}

    if tool == "jquery-to-vue3":
        checks = [
            (r"\$\(\s*[\"']#", "ID 选择器 $(#id) → ref / computed"),
            (r"\$\(\s*[\"']\.", "类选择器 $(.cls) → 模板绑定"),
            (r"\$\(document\)\.ready", "ready 回调 → onMounted"),
            (r"\.ajax\s*\(", "$.ajax → fetch / axios"),
            (r"\.on\s*\(\s*[\"']click", "事件绑定 → @click"),
        ]
        found = []
        for pat, desc in checks:
            hits = len(re.findall(pat, code))
            if hits:
                found.append({"pattern": desc, "hits": hits})
        skeleton = ("<script setup>\nimport { ref, onMounted } from 'vue'\n"
                    "const state = ref(null)\nonMounted(async () => { /* 迁移原 ready 逻辑 */ })\n"
                    "</script>\n<template><!-- 迁移原 DOM 操作为声明式模板 --></template>")
        return {**base, "summary": "jQuery→Vue3 前端现代化建议生成完成",
                "detected": found, "vue3_skeleton": skeleton}

    if tool == "dependency-risk-scan":
        risky = [
            (r"(?i)log4j[^<\n]*1\.", "Log4j 1.x（EOL，存在已知漏洞）", "高"),
            (r"(?i)fastjson", "Fastjson 反序列化风险", "高"),
            (r"(?i)commons-collections[^<\n]*3\.", "commons-collections 3.x 反序列化链", "高"),
            (r"(?i)struts", "Struts 2 历史高危 CVE", "高"),
            (r"(?i)jquery[^<\n]*1\.", "jQuery 1.x（过时且存在 XSS 风险）", "中"),
            (r"(?i)\"lodash\"\s*:\s*\"[~^]?4\.17\.[0-3]", "lodash 旧版原型污染风险", "中"),
        ]
        findings = []
        for pat, desc, level in risky:
            if re.search(pat, code):
                findings.append({"risk": level, "item": desc})
        level = "高" if any(f["risk"] == "高" for f in findings) else "中" if findings else "低"
        return {**base, "summary": "依赖升级风险扫描完成",
                "risk_level": level, "findings": findings,
                "recommendation": "优先升级高危项并锁定版本；接入 SCA 工具持续监控。"}

    return {**base, "summary": "未知工具", "error": f"unsupported tool: {tool}"}


@app.get("/mcp/tools")
def mcp_tools():
    """公开工具目录：供「免费发现」与各平台登记使用。"""
    return [
        {"name": name, "title": meta["title"],
         "description": meta["description"], "cost": meta["cost"]}
        for name, meta in MCP_TOOLS.items()
    ]


class McpInvokeIn(BaseModel):
    tool: str
    params: dict = {}


@app.post("/mcp/invoke")
def mcp_invoke(body: McpInvokeIn, user: dict = Depends(auth)):
    """MCP 工具统一计费入口：每次调用校验点数 → 分析 → 扣点 → 落调用记录。"""
    if body.tool not in MCP_TOOLS:
        raise HTTPException(404, f"Unknown MCP tool: {body.tool}")
    cost = MCP_TOOLS[body.tool]["cost"]
    if user["credits"] < cost:
        raise HTTPException(402, f"Insufficient credits: need {cost}, have {user['credits']}")
    code = str(body.params.get("code", ""))
    result = _analyze(body.tool, code, body.params)
    call_id = uuid.uuid4().hex
    with db() as c:
        c.execute("INSERT INTO mcp_calls VALUES(?,?,?,?,?,?)",
                  (call_id, user["id"], body.tool, cost,
                   json.dumps(result, ensure_ascii=False), time.time()))
        c.execute("UPDATE users SET credits=credits-? WHERE id=?",
                  (cost, user["id"]))
        c.commit()
        left = c.execute("SELECT credits FROM users WHERE id=?", (user["id"],)).fetchone()[0]
    return {"call_id": call_id, "tool": body.tool, "result": result,
            "cost": cost, "credits_left": left}


@app.get("/mcp/stats")
def mcp_stats(user: dict = Depends(auth)):
    """当前账户的 MCP 调用统计与累计消耗。"""
    with db() as c:
        rows = c.execute(
            "SELECT tool, COUNT(*) AS calls, SUM(cost) AS spent "
            "FROM mcp_calls WHERE user_id=? GROUP BY tool", (user["id"],)).fetchall()
    return {"by_tool": [dict(r) for r in rows], "credits_left": user["credits"]}


@app.get("/me")
def me(user: dict = Depends(auth)):
    return user


@app.get("/jobs")
def jobs(user: dict = Depends(auth)):
    with db() as c:
        rows = c.execute("SELECT id,source,target,status,cost,created_at FROM jobs WHERE user_id=? ORDER BY created_at DESC",
                         (user["id"],)).fetchall()
    return [dict(r) for r in rows]


@app.get("/health")
def health():
    return {"status": "ok", "ai_provider": AI_PROVIDER, "mcp_tools": len(MCP_TOOLS)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
