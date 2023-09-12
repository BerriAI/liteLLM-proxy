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


# TODO: consider https://docs.litellm.ai/docs/completion/mock_requests
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

    response = mock_client.post(
        "/key/new",
        headers={"Authorization": "NONE"},
        json={"total_budget": 1},
    )
    assert response.status_code == 401

    response = mock_client.post(
        "/key/new",
        headers={"Authorization": "Bearer FASTREPL_INITIAL_KEY"},
        json={"total_budget": 1},
    )
    assert response.status_code == 200
    key = response.json()["api_key"]

    response = mock_client.post(
        "/chat/completions", headers={"Authorization": f"Bearer {key}"}, json={}
    )
    assert response.status_code == 200


def test_cost(mock_client, mock_llm, use_valid_api_key):
    response = mock_client.post(
        "/key/new",
        headers={"Authorization": "Bearer FASTREPL_INITIAL_KEY"},
        json={"total_budget": 100},
    )
    assert response.status_code == 200
    key = response.json()["api_key"]

    # once
    response = mock_client.post(
        "/chat/completions",
        headers={"Authorization": f"Bearer {key}"},
        json={},
    )
    response = mock_client.get(
        "/cost/current", headers={"Authorization": f"Bearer {key}"}
    )
    costs = response.json()
    assert costs["gpt-3.5-turbo"] == pytest.approx(2.7499e-05, abs=1e10)

    # twice
    response = mock_client.post(
        "/chat/completions",
        headers={"Authorization": f"Bearer {key}"},
        json={},
    )
    response = mock_client.get(
        "/cost/current", headers={"Authorization": f"Bearer {key}"}
    )
    costs = response.json()
    assert costs["gpt-3.5-turbo"] == pytest.approx(2 * 2.7499e-05, abs=1e10)

    # reset
    mock_client.get("/cost/reset", headers={"Authorization": f"Bearer {key}"})
    response = mock_client.get(
        "/cost/current", headers={"Authorization": f"Bearer {key}"}
    )
    costs = response.json()
    assert costs == {}


class TestBudgetManager:
    def test_budget_enough(self, mock_client, mock_llm, use_valid_api_key):
        response = mock_client.post(
            "/key/new",
            headers={"Authorization": "Bearer FASTREPL_INITIAL_KEY"},
            json={"total_budget": 2.7499e-05 + 1},
        )
        assert response.status_code == 200
        key = response.json()["api_key"]

        # once
        response = mock_client.post(
            "/chat/completions",
            headers={"Authorization": f"Bearer {key}"},
            json={},
        )
        response = mock_client.get(
            "/cost/current", headers={"Authorization": f"Bearer {key}"}
        )
        costs = response.json()
        assert costs["gpt-3.5-turbo"] == pytest.approx(2.7499e-05, abs=1e10)

    def test_budget_exceed(self, mock_client, mock_llm, use_valid_api_key):
        response = mock_client.post(
            "/key/new",
            headers={"Authorization": "Bearer FASTREPL_INITIAL_KEY"},
            json={"total_budget": 1.7499e-05},
        )
        assert response.status_code == 200
        key = response.json()["api_key"]

        # once (pass)
        response = mock_client.post(
            "/chat/completions",
            headers={"Authorization": f"Bearer {key}"},
            json={},
        )
        response = mock_client.get(
            "/cost/current", headers={"Authorization": f"Bearer {key}"}
        )
        costs = response.json()
        assert costs["gpt-3.5-turbo"] == pytest.approx(2.7499e-05, abs=1e10)

        # twice (fail)
        with pytest.raises(Exception):
            mock_client.post(
                "/chat/completions",
                headers={"Authorization": f"Bearer {key}"},
                json={},
            )
