import pytest

import litellm
from fastapi.testclient import TestClient

import proxy.llm as llm
from proxy.main import app, valid_api_keys


@pytest.fixture
def mock_client():
    client = TestClient(app)
    yield client
    client.close()


@pytest.fixture
def mock_llm(monkeypatch):
    def _completion(**kwargs):
        return {
            "model": "gpt-3.5-turbo",
            "usage": {
                "prompt_tokens": 5,
                "completion_tokens": 10,
            },
        }

    monkeypatch.setattr(litellm, "completion", _completion)


@pytest.fixture
def use_valid_api_key():
    valid_api_keys.clear()
    valid_api_keys.add("FASTREPL_INITIAL_KEY")
    yield
    valid_api_keys.clear()


def test_health(mock_client):
    response = mock_client.get("/health")
    assert response.status_code == 200


def test_auth(mock_client, mock_llm, use_valid_api_key):
    response = mock_client.post(
        "/chat/completions", headers={"Authorization": "NONE"}, json={}
    )
    assert response.status_code == 401

    response = mock_client.get("/key/new", headers={"Authorization": "NONE"})
    assert response.status_code == 401

    response = mock_client.get(
        "/key/new", headers={"Authorization": "Bearer FASTREPL_INITIAL_KEY"}
    )
    assert response.status_code == 200
    key = response.json()["api_key"]

    response = mock_client.post(
        "/chat/completions", headers={"Authorization": f"Bearer {key}"}, json={}
    )
    assert response.status_code == 200


def test_cost(mock_client, mock_llm, use_valid_api_key):
    response = mock_client.post(
        "/chat/completions",
        headers={"Authorization": "Bearer FASTREPL_INITIAL_KEY"},
        json={},
    )

    response = mock_client.get(
        "/cost/current", headers={"Authorization": "Bearer FASTREPL_INITIAL_KEY"}
    )
    costs = response.json()
    assert costs["gpt-3.5-turbo"] == pytest.approx(2.7499e-05, abs=1e10)

    response = mock_client.post(
        "/chat/completions",
        headers={"Authorization": "Bearer FASTREPL_INITIAL_KEY"},
        json={},
    )

    response = mock_client.get(
        "/cost/current", headers={"Authorization": "Bearer FASTREPL_INITIAL_KEY"}
    )
    costs = response.json()
    assert costs["gpt-3.5-turbo"] == pytest.approx(2 * 2.7499e-05, abs=1e10)

    mock_client.get(
        "/cost/reset", headers={"Authorization": "Bearer FASTREPL_INITIAL_KEY"}
    )
    response = mock_client.get(
        "/cost/current", headers={"Authorization": "Bearer FASTREPL_INITIAL_KEY"}
    )
    costs = response.json()
    assert costs == {}
