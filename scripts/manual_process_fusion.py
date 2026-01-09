#!/usr/bin/env python3
"""Manual script to process pending fusion job for an assessment."""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from src.infrastructure.db.models import Assessment, AsyncJob
from src.workers.pipeline import process_assessment_jobs

logger = structlog.get_logger()


async def main():
    """Process fusion job for specific assessment."""
    assessment_id = "b45c3208-1da1-47af-a6a5-129b7a4e9ec3"

    # Create async engine with production DB
    prod_url = "postgresql+asyncpg://microcred_user:3i1doEdivimrYo1RaXr6ANlJE7il4Pfb@dpg-d59hv62li9vc73al72ug-a.singapore-postgres.render.com/microcred"
    engine = create_async_engine(prod_url, echo=True)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # Check assessment exists
        result = await session.execute(select(Assessment).where(Assessment.id == assessment_id))
        assessment = result.scalar_one_or_none()

        if not assessment:
            logger.error(f"Assessment {assessment_id} not found")
            return

        logger.info(f"Processing jobs for assessment {assessment_id}")

        # Process all pending jobs (function handles its own session)
        await process_assessment_jobs(assessment_id)

        # Re-query to verify fusion completed
        result = await session.execute(
            select(AsyncJob)
            .where(AsyncJob.assessment_id == assessment_id)
            .where(AsyncJob.job_type == "fusion")
        )
        fusion_job = result.scalar_one_or_none()

        if fusion_job:
            logger.info(f"Fusion job status: {fusion_job.status}")
        else:
            logger.error("Fusion job not found")


if __name__ == "__main__":
    asyncio.run(main())
