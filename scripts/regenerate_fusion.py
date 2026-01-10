#!/usr/bin/env python3
"""Trigger fusion regeneration for assessment d159d295."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from src.domain.services.fusion import FusionService
from src.infrastructure.db.models import Assessment, AsyncJob, JobStatus, JobType

# Production database
PROD_DB_URL = "postgresql+asyncpg://microcred_user:3i1doEdivimrYo1RaXr6ANlJE7il4Pfb@dpg-d59hv62li9vc73al72ug-a.singapore-postgres.render.com/microcred"

ASSESSMENT_ID = "d159d295-87f0-47b7-bb9c-ea3c5420d0e4"


async def regenerate_fusion():
    print("=" * 80)
    print(f"REGENERATING FUSION FOR: {ASSESSMENT_ID}")
    print("=" * 80)

    # Create async engine
    engine = create_async_engine(PROD_DB_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # 1. Check if assessment exists
        print("\n1. Loading assessment...")
        stmt = select(Assessment).where(Assessment.id == ASSESSMENT_ID)
        result = await session.execute(stmt)
        assessment = result.scalar_one_or_none()

        if not assessment:
            print(f"❌ Assessment {ASSESSMENT_ID} not found!")
            return

        print(f"✅ Found assessment for user: {assessment.owner_id}")
        print(f"   Role: {assessment.role_slug}")
        print(f"   Status: {assessment.status}")

        # 2. Check for existing fusion job
        print("\n2. Checking existing fusion jobs...")
        stmt = (
            select(AsyncJob)
            .where(AsyncJob.assessment_id == ASSESSMENT_ID, AsyncJob.job_type == JobType.FUSION)
            .order_by(AsyncJob.queued_at.desc())
        )
        result = await session.execute(stmt)
        existing_jobs = result.scalars().all()

        if existing_jobs:
            print(f"Found {len(existing_jobs)} existing fusion jobs:")
            for job in existing_jobs[:3]:
                print(f"  - {job.id}: {job.status} (queued: {job.queued_at})")
        else:
            print("No existing fusion jobs found")

        # 3. Create new fusion job
        print("\n3. Creating new fusion job...")
        import uuid
        from datetime import UTC, datetime

        new_job = AsyncJob(
            id=str(uuid.uuid4()),
            assessment_id=ASSESSMENT_ID,
            job_type=JobType.FUSION,
            status=JobStatus.QUEUED,
            queued_at=datetime.now(UTC),
        )
        session.add(new_job)
        await session.commit()
        print(f"✅ Created fusion job: {new_job.id}")

        # 4. Process fusion immediately
        print("\n4. Processing fusion...")
        fusion_service = FusionService(session)

        try:
            result = await fusion_service.process_fusion_job(job_id=new_job.id)

            print("\n✅ FUSION COMPLETE!")
            print(f"   Recommendation ID: {result.recommendation_id}")
            print(f"   Degraded: {result.degraded}")

            if result.error:
                print(f"   ⚠️  Error: {result.error}")

            # Show summary preview
            if result.summary_preview:
                print("\n📝 Summary Preview:")
                print("-" * 80)
                print(result.summary_preview[:500])
                print("...")

        except Exception as e:
            print(f"\n❌ Fusion failed: {e}")
            import traceback

            traceback.print_exc()
            return

        # 5. Verify recommendation
        print("\n5. Verifying new recommendation...")
        from src.infrastructure.db.models import Recommendation

        stmt = (
            select(Recommendation)
            .where(Recommendation.assessment_id == ASSESSMENT_ID)
            .order_by(Recommendation.id.desc())
        )
        result = await session.execute(stmt)
        recommendation = result.scalar_one_or_none()

        if recommendation:
            print(f"✅ Recommendation created: {recommendation.id}")
            print(f"   Created at: {recommendation.created_at}")

            # Check for tech mentions
            summary = recommendation.summary.lower()
            tech_found = []
            tech_missing = []

            for tech in ["golang", "microservices", "redis", "postgresql", "mongodb"]:
                if tech in summary or tech.replace("golang", "go") in summary:
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
            print("❌ No recommendation found!")


print("\n" + "=" * 80)
print("Starting fusion regeneration...")
print("=" * 80)

asyncio.run(regenerate_fusion())

print("\n" + "=" * 80)
print("DONE!")
print("=" * 80)
