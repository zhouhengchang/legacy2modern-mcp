"""Legacy2Modern Python SDK —— 让 Python Agent 一行调用计费工具。

安装: pip install legacy2modern
用法:
    from legacy2modern import L2MClient
    c = L2MClient(token="...")            # 或 base_url 指向公网 Worker
    reg = c.register("me@example.com")     # 注册领 100 点
    r = c.audit("var a=1; if(a==b) TODO")  # 调用审计工具（自动扣点）
    print(r["credits_left"])
"""
import json
import urllib.request

__version__ = "1.0.0"

TOOLS = {
    "legacy-code-audit": 2,
    "java8-to-springboot3": 10,
    "jquery-to-vue3": 8,
    "dependency-risk-scan": 3,
}

class L2MError(Exception):
    pass

class L2MClient:
    def __init__(self, token="", base_url="http://127.0.0.1:8000"):
        self.token = token
        self.base_url = base_url.rstrip("/")

    def _req(self, method, path, body=None):
        data = json.dumps(body).encode() if body is not None else None
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = "Bearer " + self.token
        req = urllib.request.Request(self.base_url + path, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read())
        except urllib.error.HTTPError as e:
            raise L2MError(f"HTTP {e.code}: {e.read().decode(errors='ignore')}")

    def register(self, email):
        d = self._req("POST", "/auth/register", {"email": email})
        self.token = d["token"]
        return d

    def invoke(self, tool, **params):
        if tool not in TOOLS:
            raise L2MError(f"Unknown tool: {tool}")
        key = "manifest" if tool == "dependency-risk-scan" else "code"
        return self._req("POST", "/mcp/invoke", {"tool": tool, "params": {key: params.get(key, params.get("code", ""))}})

    def audit(self, code):
        return self.invoke("legacy-code-audit", code=code)

    def java_to_spring(self, code):
        return self.invoke("java8-to-springboot3", code=code)

    def jquery_to_vue(self, code):
        return self.invoke("jquery-to-vue3", code=code)

    def dependency_scan(self, manifest):
        return self.invoke("dependency-risk-scan", manifest=manifest)

    def stats(self):
        return self._req("GET", "/mcp/stats")

    def me(self):
        return self._req("GET", "/me")
