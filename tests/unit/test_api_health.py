from fastapi.testclient import TestClient
from src.api.main import app


def test_health_endpoint_returns_service_metadata() -> None:
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["service"]
    assert payload["status"] == "ok"
    assert "datastores" in payload
