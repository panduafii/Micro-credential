#!/usr/bin/env python3
"""Clean up duplicate fusion jobs."""

import asyncio
import os
import sys
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from src.infrastructure.db.models import AsyncJob, JobStatus, JobType

sys.path.insert(0, str(Path(__file__).parent.parent))
# Override DATABASE_URL with production
os.environ["DATABASE_URL"] = (
    "postgresql+asyncpg://microcred_user:3i1doEdivimrYo1RaXr6ANlJE7il4Pfb@dpg-d59hv62li9vc73al72ug-a.singapore-postgres.render.com/microcred"
)

ASSESSMENT_ID = "d159d295-87f0-47b7-bb9c-ea3c5420d0e4"


async def cleanup_jobs():
    engine = create_async_engine(os.environ["DATABASE_URL"])
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # Find all fusion jobs for this assessment
        stmt = (
            select(AsyncJob)
            .where(
                AsyncJob.assessment_id == ASSESSMENT_ID,
                AsyncJob.job_type == JobType.FUSION,
                AsyncJob.status == JobStatus.QUEUED,
            )
            .order_by(AsyncJob.queued_at.desc())
        )

        result = await session.execute(stmt)
        jobs = result.scalars().all()

        print(f"Found {len(jobs)} queued fusion jobs:")
        for i, job in enumerate(jobs):
            print(f"  {i + 1}. {job.id} - queued at {job.queued_at}")

        if len(jobs) > 1:
            print("\nMarking old jobs as failed, keeping most recent...")
            keep_job = jobs[0]
            old_jobs = jobs[1:]

            for job in old_jobs:
                job.status = JobStatus.FAILED
                job.error = "Superseded by newer fusion job"
                job.failed_at = datetime.now(UTC)
                session.add(job)
                print(f"  ❌ Marked {job.id} as FAILED")

            await session.commit()
            print(f"\n✅ Keeping job: {keep_job.id}")
        elif len(jobs) == 1:
            print("\n✅ Only one job found, nothing to clean up")
        else:
            print("\n❌ No jobs found")

    await engine.dispose()


asyncio.run(cleanup_jobs())
