from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_root():
    response = client.get("/")

    assert response.status_code == 200

    body = response.json()

    assert body["service"] == "ci-cd-demo"


def test_health():
    response = client.get("/health")

    assert response.status_code == 200

    body = response.json()

    assert body["status"] == "healthy"


def test_ready():
    response = client.get("/ready")

    assert response.status_code == 200

    assert body["ready"] is True
