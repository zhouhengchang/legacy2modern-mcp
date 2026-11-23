"""并发正确性测试：验证计费扣点在竞争条件下不会超扣 / 穿透。"""
import uuid
from concurrent.futures import ThreadPoolExecutor
from conftest import register, auth_header


def uid():
    return uuid.uuid4().hex + "@test.com"


def test_concurrent_invoke_no_overspend(client):
    """100 点、每次扣 10 点 → 最多 10 次成功，且点数不得为负。"""
    token = register(client, uid())

    def call(_):
        return client.post("/mcp/invoke", headers=auth_header(token), json={
            "tool": "java8-to-springboot3", "params": {"code": "javax.servlet web.xml"}})

    with ThreadPoolExecutor(max_workers=12) as ex:
        results = list(ex.map(call, range(24)))

    ok = sum(1 for r in results if r.status_code == 200)
    final = client.get("/me", headers=auth_header(token)).json()["credits"]
    assert ok <= 10, f"并发下成功 {ok} 次，超过 100 点应允许的上限 10"
    assert final >= 0, f"点数被扣成负数: {final}"
    assert final == 100 - ok * 10, f"扣点不一致: 成功 {ok} 次但剩余 {final}"


def test_concurrent_refactor_no_overspend(client):
    token = register(client, uid())

    def call(_):
        return client.post("/refactor", headers=auth_header(token), json={
            "source_code": "var a=1;", "from_stack": "java8", "to_stack": "springboot3"})

    with ThreadPoolExecutor(max_workers=10) as ex:
        results = list(ex.map(call, range(15)))

    ok = sum(1 for r in results if r.status_code == 200)
    final = client.get("/me", headers=auth_header(token)).json()["credits"]
    assert final >= 0 and final == 100 - ok * 10
