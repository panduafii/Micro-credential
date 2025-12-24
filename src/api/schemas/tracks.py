from __future__ import annotations

from pydantic import BaseModel


class TrackItem(BaseModel):
    slug: str
    name: str
    description: str | None = None
    question_count: int


class TracksResponse(BaseModel):
    tracks: list[TrackItem]
