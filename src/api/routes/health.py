from __future__ import annotations

from datetime import UTC, datetime

import structlog
from fastapi import APIRouter
from src.core.config import get_settings

router = APIRouter(tags=["Observability"])
logger = structlog.get_logger()


@router.get("/health", summary="Service health probe")
async def health_check() -> dict:
    """Return basic service and datastore status information."""
    settings = get_settings()
    payload = {
        "service": settings.app_name,
        "version": settings.version,
        "status": "ok",
        "timestamp": datetime.now(UTC).isoformat(),
        "datastores": {
            "postgres": {"status": "unverified"},
            "redis": {"status": "unverified"},
        },
    }
    logger.info("health_probe", **payload)
    return payload
