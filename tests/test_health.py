import pytest
from fastapi.testclient import TestClient

from proxy.main import app


@pytest.fixture
def client():
    client = TestClient(app)
    yield client
    client.close()


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
