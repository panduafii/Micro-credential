#!/usr/bin/env python
"""
Process pending assessment jobs sequentially.

This script runs GPT, RAG, and Fusion jobs for a given assessment to complete the full flow.
Useful for testing and development without running full worker infrastructure.

Usage:
    poetry run python scripts/process_jobs.py <assessment_id>
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from src.core.config import get_settings
from src.domain.services.fusion import FusionService
from src.domain.services.gpt_scoring import GPTEssayScoringService
from src.domain.services.rag import RAGService
from src.infrastructure.db.models import AsyncJob, JobStatus, JobType
from src.infrastructure.db.session import get_session_factory


async def process_assessment_jobs(assessment_id: str) -> None:
    """Process all jobs for an assessment: GPT -> RAG -> Fusion."""
    settings = get_settings()
    session_factory = get_session_factory()

    print(f"🔄 Processing jobs for assessment: {assessment_id}")
    print(f"   Database: {settings.database_url.split('@')[1] if '@' in settings.database_url else 'local'}")
    print()

    async with session_factory() as session:
        # Get all jobs for this assessment
        stmt = (
            select(AsyncJob)
            .where(AsyncJob.assessment_id == assessment_id)
            .order_by(AsyncJob.job_type)
        )
        result = await session.execute(stmt)
        jobs = list(result.scalars().all())

        if not jobs:
            print(f"❌ No jobs found for assessment {assessment_id}")
            return

        print(f"📋 Found {len(jobs)} jobs:")
        for job in jobs:
            print(f"   - {job.job_type}: {job.status}")
        print()

        # Process jobs in order: GPT -> RAG -> Fusion
        job_order = [JobType.GPT.value, JobType.RAG.value, JobType.FUSION.value]

        for job_type in job_order:
            job = next((j for j in jobs if j.job_type == job_type), None)
            if not job:
                print(f"⏭️  Skipping {job_type} (no job found)")
                continue

            if job.status == JobStatus.COMPLETED.value:
                print(f"✅ {job_type} already completed")
                continue

            print(f"⚙️  Processing {job_type}...")

            try:
                if job_type == JobType.GPT.value:
                    # GPT Essay Scoring
                    service = GPTEssayScoringService(session=session)
                    result = await service.score_assessment_essays(
                        assessment_id=assessment_id,
                        job_id=job.id,
                    )
                    print(f"   ✓ Scored {len(result.essay_scores)} essays")
                    print(f"   ✓ Total score: {result.total_score}/{result.max_score}")

                elif job_type == JobType.RAG.value:
                    # RAG Recommendations
                    service = RAGService(session=session)
                    result = await service.process_rag_job(assessment_id)
                    print(f"   ✓ Found {len(result.matches)} recommendations")
                    if result.degraded:
                        print(f"   ⚠️  Degraded mode (fallback courses)")

                elif job_type == JobType.FUSION.value:
                    # Fusion Summary
                    service = FusionService(session=session)
                    result = await service.process_fusion_job(assessment_id)
                    print(f"   ✓ Generated summary")
                    print(f"   ✓ Overall score: {result.overall_score:.1f}%")
                    print(f"   ✓ Processing time: {result.processing_duration_ms}ms")

                print(f"✅ {job_type} completed successfully\n")

            except Exception as e:
                print(f"❌ {job_type} failed: {e}\n")
                # Continue with next job even if one fails
                continue

    print("=" * 60)
    print("🎉 All jobs processed!")
    print()
    print("You can now:")
    print(f"  • Check status: GET /assessments/{assessment_id}/status")
    print(f"  • Get results:  GET /assessments/{assessment_id}/result")
    print(f"  • Add feedback: POST /assessments/{assessment_id}/feedback")


async def main() -> None:
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: poetry run python scripts/process_jobs.py <assessment_id>")
        print()
        print("Example:")
        print("  poetry run python scripts/process_jobs.py 0867f90f-2d15-4df0-b3ff-00ce2c88a1d1")
        sys.exit(1)

    assessment_id = sys.argv[1]
    await process_assessment_jobs(assessment_id)


if __name__ == "__main__":
    asyncio.run(main())
