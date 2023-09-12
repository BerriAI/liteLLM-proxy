import pytest

import litellm
from fastapi.testclient import TestClient

import proxy.main as main


@pytest.fixture
def mock_client():
    client = TestClient(main.app)
    yield client
    client.close()


FASTREPL_API_KEY = "FASTREPL_API_KEY"


@pytest.fixture(autouse=True)
def set_env(monkeypatch):
    monkeypatch.setenv("FASTREPL_API_KEY", "FASTREPL_API_KEY")
    monkeypatch.setattr(
        main,
        "budget_manager",
        litellm.BudgetManager(type="local", project_name="fastrepl_proxy"),
    )


# TODO: consider https://docs.litellm.ai/docs/completion/mock_requests
@pytest.fixture(autouse=True)
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


def test_auth(mock_client):
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
        headers={"Authorization": f"Bearer {FASTREPL_API_KEY}"},
        json={"total_budget": 1},
    )
    assert response.status_code == 200
    key = response.json()["api_key"]

    response = mock_client.post(
        "/chat/completions", headers={"Authorization": f"Bearer {key}"}, json={}
    )
    assert response.status_code == 200


def test_cost(mock_client):
    response = mock_client.post(
        "/key/new",
        headers={"Authorization": f"Bearer {FASTREPL_API_KEY}"},
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
    def test_budget_enough(self, mock_client):
        response = mock_client.post(
            "/key/new",
            headers={"Authorization": f"Bearer {FASTREPL_API_KEY}"},
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

    def test_budget_exceed(self, mock_client):
        response = mock_client.post(
            "/key/new",
            headers={"Authorization": f"Bearer {FASTREPL_API_KEY}"},
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
