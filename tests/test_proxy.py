import pytest
import os, dotenv

import proxy.llm as llm
from fastapi.testclient import TestClient
from proxy.main import app


@pytest.fixture
def mock_client():
    client = TestClient(app)
    yield client
    client.close()


@pytest.fixture
def mock_env(monkeypatch):
    kv = {}

    def getenv(k, v=0):
        return kv[k] if k in kv else v

    def set_key(path: str, k: str, v: str):
        kv[k] = v

    def load_dotenv(*args, **kwargs):
        return

    monkeypatch.setattr(os, "environ", kv)
    monkeypatch.setattr(os, "getenv", getenv)
    monkeypatch.setattr(dotenv, "set_key", set_key)
    monkeypatch.setattr(dotenv, "load_dotenv", load_dotenv)


@pytest.fixture
def mock_llm(monkeypatch):
    def _completion(**kwargs):
        return kwargs

    monkeypatch.setattr(llm, "completion", _completion)


def test_health(mock_client):
    response = mock_client.get("/health")
    assert response.status_code == 200


def test_auth(mock_client, mock_env, mock_llm):
    assert os.getenv("AUTH_TOKEN", "") == ""

    response = mock_client.post(
        "/chat/completions", headers={"Authorization": "NONE"}, json={}
    )
    assert response.status_code == 401

    response = mock_client.get(
        "/key/new"
    )
    assert response.status_code == 200

    new_api_key: str = response.json()["api_key"]
    assert new_api_key.startswith("sk-fastrepl-")

    response = mock_client.post(
        "/chat/completions", headers={"Authorization": new_api_key}, json={}
    )
    assert response.status_code == 200
