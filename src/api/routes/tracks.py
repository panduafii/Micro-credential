from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_db_session
from src.api.schemas.tracks import TrackItem, TracksResponse
from src.infrastructure.db.models import QuestionTemplate, RoleCatalog

router = APIRouter(prefix="/tracks", tags=["Tracks"])


@router.get("", response_model=TracksResponse)
async def list_tracks(session: AsyncSession = Depends(get_db_session)) -> TracksResponse:
    """Return available planning tracks/roles along with question counts."""
    role_stmt: Select[tuple[RoleCatalog]] = select(RoleCatalog).order_by(RoleCatalog.name)
    roles = (await session.execute(role_stmt)).scalars().all()

    count_stmt = (
        select(QuestionTemplate.role_slug, func.count(QuestionTemplate.id))
        .group_by(QuestionTemplate.role_slug)
    )
    count_pairs = (await session.execute(count_stmt)).all()
    question_count_map = {slug: count for slug, count in count_pairs}

    items = [
        TrackItem(
            slug=role.slug,
            name=role.name,
            description=role.description,
            question_count=question_count_map.get(role.slug, 0),
        )
        for role in roles
    ]
    return TracksResponse(tracks=items)
