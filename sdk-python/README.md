# Legacy2Modern Python SDK

让 Python Agent 一行调用遗留代码现代化计费工具。

```bash
pip install legacy2modern
```

```python
from legacy2modern import L2MClient

c = L2MClient(base_url="https://legacy2modern-mcp.lilac-restaurant.workers.dev")
c.register("me@example.com")           # 领 100 点
r = c.audit("var a=1; if(a==b) TODO")  # 审计（扣 2 点）
print(r["credits_left"])
print(c.stats())
```

工具与价格：`legacy-code-audit` 2 / `java8-to-springboot3` 10 / `jquery-to-vue3` 8 / `dependency-risk-scan` 3。
