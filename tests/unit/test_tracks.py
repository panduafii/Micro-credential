from __future__ import annotations


def test_tracks_endpoint_returns_seeded_roles(test_client) -> None:
    response = test_client.get("/tracks")
    assert response.status_code == 200
    payload = response.json()
    assert len(payload["tracks"]) >= 2
    backend = next(track for track in payload["tracks"] if track["slug"] == "backend-engineer")
    assert backend["question_count"] == 10
