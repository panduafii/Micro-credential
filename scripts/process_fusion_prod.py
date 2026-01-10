#!/usr/bin/env python3
"""Process fusion job directly against production database."""

import asyncio
import os
import sys
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from src.domain.services.fusion import FusionService
from src.infrastructure.db.models import AsyncJob, JobStatus, JobType

sys.path.insert(0, str(Path(__file__).parent.parent))
# Override DATABASE_URL with production
os.environ["DATABASE_URL"] = (
    "postgresql+asyncpg://microcred_user:3i1doEdivimrYo1RaXr6ANlJE7il4Pfb@dpg-d59hv62li9vc73al72ug-a.singapore-postgres.render.com/microcred"
)

ASSESSMENT_ID = "d159d295-87f0-47b7-bb9c-ea3c5420d0e4"


async def process_fusion():
    print("=" * 80)
    print(f"PROCESSING FUSION FOR: {ASSESSMENT_ID}")
    print("=" * 80)

    # Create async engine for production
    engine = create_async_engine(os.environ["DATABASE_URL"])
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # 1. Find pending fusion job
        print("\n1. Finding fusion job...")
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

        if not jobs:
            print("❌ No pending fusion job found!")
            print("   Run queue_fusion_job.py first")
            return

        if len(jobs) > 1:
            print(f"⚠️  Found {len(jobs)} pending fusion jobs, using most recent")

        job = jobs[0]  # Take most recent (already ordered by queued_at desc)

        print(f"✅ Found job: {job.id}")
        print(f"   Status: {job.status}")
        print(f"   Queued at: {job.queued_at}")

        # 2. Process fusion
        print("\n2. Processing fusion...")
        fusion_service = FusionService(session)

        try:
            result = await fusion_service.process_fusion_job(assessment_id=ASSESSMENT_ID)

            print("\n✅ FUSION COMPLETE!")
            print(f"   Degraded: {result.degraded}")

            if result.error:
                print(f"   ⚠️  Error: {result.error}")

        except Exception as e:
            print(f"\n❌ Fusion failed: {e}")
            import traceback

            traceback.print_exc()
            return

        # 3. Verify recommendation
        print("\n3. Verifying recommendation...")
        from src.infrastructure.db.models import Recommendation

        stmt = select(Recommendation).where(Recommendation.assessment_id == ASSESSMENT_ID)
        result_rec = await session.execute(stmt)
        recommendation = result_rec.scalar_one_or_none()

        if recommendation:
            print("✅ Recommendation verified!")

            # Check for tech mentions
            summary = recommendation.summary.lower()
            tech_found = []
            tech_missing = []

            for tech in ["golang", "go ", "microservice", "redis", "postgresql", "mongodb"]:
                if tech in summary:
                    tech_found.append(tech)
                else:
                    tech_missing.append(tech)

            print("\n🔍 Tech mentions in summary:")
            for tech in tech_found:
                print(f"  ✅ {tech}")
            for tech in tech_missing:
                print(f"  ❌ {tech}")

            # Check for problematic messages
            if "haven't specified" in summary or "haven't mentioned" in summary:
                print("\n⚠️  Still contains 'haven't specified' message!")
            else:
                print("\n✅ No 'haven't specified' message found!")
        else:
            print("❌ Recommendation not found!")

    await engine.dispose()


print("\n" + "=" * 80)
print("Starting fusion processing...")
print("=" * 80)

asyncio.run(process_fusion())

print("\n" + "=" * 80)
print("DONE!")
print("=" * 80)
