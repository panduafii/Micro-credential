from __future__ import annotations

from tests.utils import auth_headers


def test_assessment_start_creates_payload(test_client) -> None:
    response = test_client.post(
        "/assessments/start",
        json={"role_slug": "backend-engineer"},
        headers=auth_headers(),
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["role"]["slug"] == "backend-engineer"
    assert len(payload["questions"]) == 10


def test_assessment_start_resumes_existing(test_client) -> None:
    first = test_client.post(
        "/assessments/start",
        json={"role_slug": "backend-engineer"},
        headers=auth_headers(),
    )
    second = test_client.post(
        "/assessments/start",
        json={"role_slug": "backend-engineer"},
        headers=auth_headers(),
    )
    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["assessment_id"] == second.json()["assessment_id"]


def test_assessment_start_unknown_role_returns_404(test_client) -> None:
    response = test_client.post(
        "/assessments/start",
        json={"role_slug": "unknown"},
        headers=auth_headers(),
    )
    assert response.status_code == 404
