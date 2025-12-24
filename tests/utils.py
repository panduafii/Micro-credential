from __future__ import annotations

from src.api.deps import issue_smoke_token
from src.core.auth import Role


def auth_headers(user_id: str = "student-1", role: Role = Role.STUDENT) -> dict[str, str]:
    token = issue_smoke_token(user_id, role=role, email="student@example.com")
    return {"Authorization": f"Bearer {token}"}
