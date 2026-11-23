import json, urllib.request, urllib.error, time

_NONCE = str(int(time.time() * 1000))
BASE = "http://127.0.0.1:8000"
MCP  = "http://127.0.0.1:3000"

def req(method, path, body=None, token=None, base=BASE):
    data = json.dumps(body).encode() if body is not None else None
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = "Bearer " + token
    r = urllib.request.Request(base + path, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(r, timeout=10) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        raw = e.read()
        try: return e.code, json.loads(raw)
        except Exception: return e.code, raw.decode(errors="ignore")

def mcp(method, params, id=1, token=None):
    body = {"jsonrpc": "2.0", "id": id, "method": method, "params": params}
    headers = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream"}
    if token:
        headers["Authorization"] = "Bearer " + token
    r = urllib.request.Request(MCP + "/mcp", data=json.dumps(body).encode(), headers=headers, method="POST")
    try:
        with urllib.request.urlopen(r, timeout=15) as resp:
            raw = resp.read().decode()
            return resp.status, raw
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode(errors="ignore")

results = []
def check(name, ok, detail=""):
    results.append((name, ok, detail))
    print(("PASS" if ok else "FAIL"), "|", name, "|", detail)

# ---- 1. 后端注册 ----
st, d = req("POST", "/auth/register", {"email": f"verify{_NONCE}@legacy2modern.dev"})
token = d.get("token", "")
check("注册返回token与100点", st == 200 and d.get("credits") == 100 and bool(token), f"status={st} credits={d.get('credits')}")

# ---- 2. 连续扣点 ----
expect = 100
for tool, params, cost in [
    ("legacy-code-audit", {"code": "var a=1; if(a==b) TODO eval(a)"}, 2),
    ("dependency-risk-scan", {"code": "log4j 1.x fastjson"}, 3),
    ("java8-to-springboot3", {"code": "javax.servlet Struts web.xml"}, 10),
    ("jquery-to-vue3", {"code": "$('#x').ready(function(){$.ajax({})})"}, 8),
]:
    expect -= cost
    st, d = req("POST", "/mcp/invoke", {"tool": tool, "params": params}, token=token)
    check(f"扣点 {tool} -{cost}", st == 200 and d.get("credits_left") == expect, f"left={d.get('credits_left')} expect={expect}")

# ---- 3. 统计 ----
st, d = req("GET", "/mcp/stats", token=token)
total = sum(x["spent"] for x in d.get("by_tool", []))
check("stats累计消耗=23", st == 200 and total == 23, f"spent={total} credits_left={d.get('credits_left')}")

# ---- 4. 点数不足 402 ----
st, d = req("POST", "/mcp/invoke", {"tool": "java8-to-springboot3", "params": {"code": "x"}}, token=token)
# 77 credits left, need 10 -> still ok; drain via repeated 8-point calls
st2, d2 = None, None
for _ in range(12):
    st2, d2 = req("POST", "/mcp/invoke", {"tool": "jquery-to-vue3", "params": {"code": "x"}}, token=token)
    if st2 == 402: break
check("点数不足返回402", st2 == 402, f"status={st2} detail={str(d2)[:80]}")

# ---- 5. MCP Streamable HTTP 协议 ----
st, raw = mcp("initialize", {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "verify", "version": "1.0"}}, id=1, token=token)
init_ok = st == 200 and ("serverInfo" in raw or "result" in raw)
check("HTTP initialize", init_ok, f"status={st} raw={raw[:120]}")

st, raw = mcp("tools/list", {}, id=2, token=token)
listed = all(t in raw for t in ["legacy-code-audit", "java8-to-springboot3", "jquery-to-vue3", "dependency-risk-scan", "l2m-list-tools"])
check("HTTP tools/list 含5工具", st == 200 and listed, f"status={st}")

# new token for http call
st, d = req("POST", "/auth/register", {"email": f"http{_NONCE}@legacy2modern.dev"})
htoken = d.get("token", "")
st, raw = mcp("tools/call", {"name": "dependency-risk-scan", "arguments": {"manifest": "log4j 1.x"}}, id=3, token=htoken)
call_ok = st == 200 and "risk_level" in raw and "credits_left" in raw
check("HTTP tools/call 计费调用", call_ok, f"status={st} raw={raw[:160]}")
st, d = req("GET", "/me", token=htoken)
check("HTTP调用后余额=97", d.get("credits") == 97, f"credits={d.get('credits')}")

passed = sum(1 for _, ok, _ in results if ok)
print(f"\n===== {passed}/{len(results)} PASSED =====")
