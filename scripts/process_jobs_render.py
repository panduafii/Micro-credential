#!/usr/bin/env python
"""
Process assessment jobs on Render production database.

Usage:
    export RENDER_DATABASE_URL="postgresql+asyncpg://user:pass@host/db"
    poetry run python scripts/process_jobs_render.py <assessment_id>
"""

import asyncio
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from src.domain.services.fusion import FusionService
from src.infrastructure.db.models import AsyncJob, JobStatus, JobType

# Get database URL from environment
RENDER_DB_URL = os.getenv("RENDER_DATABASE_URL")
if not RENDER_DB_URL:
    print("Error: RENDER_DATABASE_URL environment variable not set")
    print("Usage: export RENDER_DATABASE_URL='postgresql://user:pass@host/db'")
    sys.exit(1)

# Convert to async driver format if not already
if not RENDER_DB_URL.startswith("postgresql+asyncpg://"):
    RENDER_DB_URL = RENDER_DB_URL.replace("postgresql://", "postgresql+asyncpg://")


async def process_fusion_job(assessment_id: str) -> None:
    """Process fusion job for an assessment on Render."""
    # Create engine and session
    engine = create_async_engine(RENDER_DB_URL, echo=False)
    session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    print(f"🔄 Processing FUSION job for assessment: {assessment_id}")
    print("   Database: Render Production (Singapore)")
    print()

    async with session_factory() as session:
        # Get fusion job
        stmt = (
            select(AsyncJob)
            .where(AsyncJob.assessment_id == assessment_id, AsyncJob.job_type == JobType.FUSION)
            .order_by(AsyncJob.queued_at.desc())
        )
        result = await session.execute(stmt)
        job = result.scalar_one_or_none()

        if not job:
            print(f"❌ No fusion job found for assessment {assessment_id}")
            await engine.dispose()
            return

        print(f"📋 Job status: {job.status}")

        # Set to in_progress
        job.status = JobStatus.IN_PROGRESS
        await session.commit()
        print("⏳ Processing fusion job...")

        try:
            # Run fusion
            fusion_service = FusionService(session)
            result = await fusion_service.process_fusion_job(assessment_id)

            # Mark completed
            job.status = JobStatus.COMPLETED
            job.completed_at = asyncio.get_event_loop().time()
            await session.commit()

            print("✅ Fusion job completed!")

            # Get recommendation
            from src.infrastructure.db.models import Recommendation

            stmt = select(Recommendation).where(Recommendation.assessment_id == assessment_id)
            result = await session.execute(stmt)
            rec = result.scalar_one_or_none()

            if rec:
                print("\n📊 Results:")
                print(f"   Overall Score: {rec.overall_score:.1f}%")
                print(f"   Degraded: {rec.degraded}")

                # Show score breakdown
                if rec.score_breakdown:
                    print("\n   Score Breakdown:")
                    for section, data in rec.score_breakdown.items():
                        if isinstance(data, dict) and "percentage" in data:
                            pct = data["percentage"]
                            print(f"     {section}: {pct:.1f}%")

                # Show first part of summary
                if rec.summary:
                    print("\n   Summary (first 300 chars):")
                    print(f"   {rec.summary[:300]}...")

        except Exception as e:
            print(f"❌ Error: {e}")
            job.status = JobStatus.FAILED
            await session.commit()
            raise

    await engine.dispose()


async def main():
    if len(sys.argv) < 2:
        print("Usage: poetry run python scripts/process_jobs_render.py <assessment_id>")
        sys.exit(1)

    assessment_id = sys.argv[1]
    await process_fusion_job(assessment_id)


if __name__ == "__main__":
    asyncio.run(main())
