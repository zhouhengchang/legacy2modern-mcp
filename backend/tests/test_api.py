"""端到端测试：覆盖鉴权、计费、MCP 工具、错误处理与边界条件。"""
import uuid
from conftest import register, auth_header


def uid():
    return uuid.uuid4().hex + "@test.com"


# ---------- 健康检查与元数据 ----------

def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    d = r.json()
    assert d["status"] == "ok"
    assert d["mcp_tools"] == 4
    assert d["ai_provider"] == "mock"


def test_openapi_version(client):
    r = client.get("/openapi.json")
    assert r.status_code == 200
    assert r.json()["info"]["version"] == "1.0.0"


# ---------- 注册与鉴权 ----------

def test_register_grants_100_credits(client):
    token = register(client, uid())
    r = client.get("/me", headers=auth_header(token))
    assert r.status_code == 200
    assert r.json()["credits"] == 100


def test_duplicate_email_rejected(client):
    email = uid()
    register(client, email)
    r = client.post("/auth/register", json={"email": email})
    assert r.status_code == 400


def test_missing_token_rejected(client):
    assert client.get("/me").status_code == 401
    assert client.get("/me", headers={"Authorization": "Basic xxx"}).status_code == 401
    assert client.get("/me", headers=auth_header("bad-token")).status_code == 401


# ---------- 代码重构与任务 ----------

def test_refactor_deducts_and_records(client):
    token = register(client, uid())
    r = client.post("/refactor", headers=auth_header(token), json={
        "source_code": "var a = 1;", "from_stack": "java8", "to_stack": "springboot3"})
    assert r.status_code == 200
    d = r.json()
    assert d["status"] == "done"
    assert d["credits_left"] == 90  # 100 - 10

    jobs = client.get("/jobs", headers=auth_header(token)).json()
    assert len(jobs) == 1
    assert jobs[0]["cost"] == 10
    assert jobs[0]["source"] == "var a = 1;"


# ---------- MCP 工具目录 ----------

def test_mcp_tools_catalog(client):
    r = client.get("/mcp/tools")
    assert r.status_code == 200
    tools = r.json()
    assert len(tools) == 4
    costs = {t["name"]: t["cost"] for t in tools}
    assert costs == {
        "legacy-code-audit": 2,
        "java8-to-springboot3": 10,
        "jquery-to-vue3": 8,
        "dependency-risk-scan": 3,
    }


# ---------- MCP 调用计费与分析 ----------

def test_mcp_invoke_deducts_correct_points(client):
    token = register(client, uid())
    r = client.post("/mcp/invoke", headers=auth_header(token), json={
        "tool": "legacy-code-audit", "params": {"code": "var x=1; if(a==b) TODO"}})
    assert r.status_code == 200
    d = r.json()
    assert d["cost"] == 2
    assert d["credits_left"] == 98
    assert d["result"]["risk_score"] < 100


def test_mcp_invoke_all_four_tools(client):
    token = register(client, uid())
    samples = {
        "legacy-code-audit": "var a=1; == TODO",
        "java8-to-springboot3": "javax.servlet web.xml Struts",
        "jquery-to-vue3": "$('#id').on('click'); $.ajax(",
        "dependency-risk-scan": "log4j 1.2 fastjson commons-collections 3.1",
    }
    for tool, code in samples.items():
        r = client.post("/mcp/invoke", headers=auth_header(token), json={
            "tool": tool, "params": {"code": code}})
        assert r.status_code == 200, r.text
        assert r.json()["tool"] == tool
    stats = client.get("/mcp/stats", headers=auth_header(token)).json()
    assert len(stats["by_tool"]) == 4
    assert all(e["calls"] == 1 for e in stats["by_tool"])


def test_mcp_unknown_tool_404(client):
    token = register(client, uid())
    r = client.post("/mcp/invoke", headers=auth_header(token), json={
        "tool": "does-not-exist", "params": {}})
    assert r.status_code == 404


# ---------- 计费边界：402 ----------

def test_mcp_insufficient_credits_402(client):
    """消耗至不足后，再次调用应返回 402 而非扣成负数。"""
    token = register(client, uid())
    # java8-to-springboot3 每次 10 点，调用 10 次用尽 100 点
    for _ in range(10):
        r = client.post("/mcp/invoke", headers=auth_header(token), json={
            "tool": "java8-to-springboot3", "params": {"code": "javax.servlet"}})
        assert r.status_code == 200
    assert client.get("/me", headers=auth_header(token)).json()["credits"] == 0

    r = client.post("/mcp/invoke", headers=auth_header(token), json={
        "tool": "legacy-code-audit", "params": {"code": "var a=1"}})
    assert r.status_code == 402


def test_refactor_insufficient_credits_402(client):
    token = register(client, uid())
    for _ in range(10):
        client.post("/mcp/invoke", headers=auth_header(token), json={
            "tool": "java8-to-springboot3", "params": {"code": "x"}})
    r = client.post("/refactor", headers=auth_header(token), json={
        "source_code": "x", "from_stack": "java8", "to_stack": "springboot3"})
    assert r.status_code == 402


# ---------- 分析结果正确性 ----------

def test_audit_detects_hardcoded_secret(client):
    token = register(client, uid())
    r = client.post("/mcp/invoke", headers=auth_header(token), json={
        "tool": "legacy-code-audit",
        "params": {"code": 'String password = "admin123"; eval(x);'}})
    issues = [i["issue"] for i in r.json()["result"]["issues"]]
    assert any("硬编码凭据" in i for i in issues)
    assert any("eval" in i for i in issues)


def test_dependency_scan_flags_high_risk(client):
    token = register(client, uid())
    r = client.post("/mcp/invoke", headers=auth_header(token), json={
        "tool": "dependency-risk-scan",
        "params": {"code": "log4j 1.2.17, fastjson"}})
    assert r.json()["result"]["risk_level"] == "高"


# ---------- 输入校验 ----------

def test_invalid_email_rejected(client):
    for bad in ["", "notanemail", "a@", "a@b", "x" * 300 + "@a.com"]:
        r = client.post("/auth/register", json={"email": bad})
        assert r.status_code == 422, f"应拒绝非法邮箱: {bad}"


def test_invalid_tool_name_rejected(client):
    token = register(client, uid())
    r = client.post("/mcp/invoke", headers=auth_header(token), json={
        "tool": "BAD NAME!", "params": {}})
    assert r.status_code == 422


def test_oversized_code_rejected(client):
    token = register(client, uid())
    r = client.post("/refactor", headers=auth_header(token), json={
        "source_code": "x" * 200001, "from_stack": "java8", "to_stack": "springboot3"})
    assert r.status_code == 422


# ---------- 安全：token 存储与 CORS ----------

def test_token_not_stored_in_plaintext(client):
    import os
    token = register(client, uid())
    # 直接读取测试库，确认不含明文 token
    from app import main as main
    with main.db() as c:
        row = c.execute("SELECT token FROM users WHERE token=?",
                        (main.token_digest(token),)).fetchone()
    assert row is not None, "应存摘要"
    assert row["token"] != token, "数据库不得存明文 token"
    assert len(row["token"]) == 64, "SHA-256 摘要应为 64 字符"


def test_me_does_not_leak_token(client):
    token = register(client, uid())
    me = client.get("/me", headers=auth_header(token)).json()
    assert "token" not in me
    assert me["credits"] == 100


def test_cors_allows_whitelisted_origin(client):
    r = client.get("/health", headers={"Origin": "http://localhost:8080"})
    assert r.headers.get("access-control-allow-origin") == "http://localhost:8080"


def test_cors_rejects_unknown_origin(client):
    r = client.get("/health", headers={"Origin": "https://evil.example"})
    assert "access-control-allow-origin" not in r.headers


def test_db_parent_dir_auto_created(client, tmp_path):
    """DB 父目录不存在时应自动创建而非启动失败。"""
    import os, importlib
    from app import main as main
    nested = tmp_path / "a" / "b" / "deep.db"
    os.environ["DB_PATH"] = str(nested)
    importlib.reload(main)
    main.init_db()
    assert nested.exists(), "应自动创建嵌套目录并建库"
