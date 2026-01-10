#!/usr/bin/env python3
"""Trigger fusion job directly in production."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import uuid

from sqlalchemy import create_engine, text

# Production database
PROD_DB_URL = "postgresql://microcred_user:3i1doEdivimrYo1RaXr6ANlJE7il4Pfb@dpg-d59hv62li9vc73al72ug-a.singapore-postgres.render.com/microcred"

engine = create_engine(PROD_DB_URL)

ASSESSMENT_ID = "d159d295-87f0-47b7-bb9c-ea3c5420d0e4"

print("=" * 80)
print(f"CREATING FUSION JOB FOR: {ASSESSMENT_ID}")
print("=" * 80)

with engine.connect() as conn:
    # 1. Create fusion job
    print("\n1. Creating fusion job...")
    job_id = str(uuid.uuid4())

    conn.execute(
        text("""
        INSERT INTO async_jobs (
            id,
            assessment_id,
            job_type,
            status,
            attempts,
            max_attempts,
            queued_at
        ) VALUES (
            :job_id,
            :assessment_id,
            'fusion',
            'queued',
            0,
            3,
            NOW()
        )
    """),
        {"job_id": job_id, "assessment_id": ASSESSMENT_ID},
    )

    conn.commit()

    print(f"✅ Created fusion job: {job_id}")
    print("   Status: queued")
    print("\n⚠️  Job created but NOT processed yet!")
    print("   You need to run the worker to process this job:")
    print("   poetry run python scripts/process_jobs.py")
    print("\n   Or process it directly via API/worker service in production")

print("\n" + "=" * 80)
print("DONE - Job queued, waiting for worker to process")
print("=" * 80)
