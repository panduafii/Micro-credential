#!/usr/bin/env python3
"""Manual script to process pending fusion job for an assessment.

Usage:
    export RENDER_DATABASE_URL="postgresql+asyncpg://user:pass@host/db"
    poetry run python scripts/manual_process_fusion.py
"""

import asyncio
import os
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

    # Get database URL from environment
    prod_url = os.getenv("RENDER_DATABASE_URL")
    if not prod_url:
        print("Error: RENDER_DATABASE_URL environment variable not set")
        print("Usage: export RENDER_DATABASE_URL='postgresql+asyncpg://user:pass@host/db'")
        sys.exit(1)

    # Create async engine with production DB
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
