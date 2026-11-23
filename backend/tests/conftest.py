"""pytest 共享夹具：使用临时 SQLite 数据库，隔离测试数据。"""
import os
import sys
import importlib
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


@pytest.fixture
def client(tmp_path, monkeypatch):
    """返回 TestClient，每个测试独享一个临时数据库。"""
    monkeypatch.setenv("DB_PATH", str(tmp_path / "test.db"))
    monkeypatch.setenv("AI_PROVIDER", "mock")

    import app.main as main
    importlib.reload(main)  # 让模块读取新的 DB_PATH 环境变量
    main.init_db()

    from fastapi.testclient import TestClient
    with TestClient(main.app) as c:
        yield c


def register(client, email):
    """辅助：注册一个用户，返回 token。"""
    r = client.post("/auth/register", json={"email": email})
    assert r.status_code == 200, r.text
    return r.json()["token"]


def auth_header(token):
    return {"Authorization": f"Bearer {token}"}
