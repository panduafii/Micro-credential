#!/usr/bin/env python3
"""Fix assessment d159d295 - check and fix empty response_data."""

import json
import os
import sys
from pathlib import Path

from sqlalchemy import create_engine, text

sys.path.insert(0, str(Path(__file__).parent.parent))

# This script assumes you have DATABASE_URL_PRODUCTION in .env
# Run: echo "DATABASE_URL_PRODUCTION=postgresql://..." >> .env
#
# OR run with:
# DATABASE_URL_PRODUCTION="postgresql://..." poetry run python scripts/fix_empty_responses.py

DATABASE_URL = os.getenv("DATABASE_URL_PRODUCTION")
if not DATABASE_URL:
    print("❌ DATABASE_URL_PRODUCTION not set!")
    print("\nUsage:")
    print(
        '  DATABASE_URL_PRODUCTION="postgresql://user:pass@host/db" '
        "poetry run python scripts/fix_empty_responses.py"
    )
    print("\nOR add to .env:")
    print("  DATABASE_URL_PRODUCTION=postgresql://...")
    sys.exit(1)

# Handle async pg
if "asyncpg" in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")

engine = create_engine(DATABASE_URL)

ASSESSMENT_ID = "d159d295-87f0-47b7-bb9c-ea3c5420d0e4"

print("=" * 80)
print(f"ANALYZING & FIXING ASSESSMENT: {ASSESSMENT_ID}")
print("=" * 80)

with engine.connect() as conn:
    # 1. Check all responses
    print("\n1. CHECKING RESPONSES...")
    print("-" * 80)

    result = conn.execute(
        text("""
        SELECT
            ar.id as response_id,
            ar.question_snapshot_id,
            ar.response_data,
            aqs.sequence as question_number,
            aqs.question_type,
            aqs.metadata as snapshot_metadata
        FROM assessment_responses ar
        JOIN assessment_question_snapshots aqs ON ar.question_snapshot_id = aqs.id
        WHERE ar.assessment_id = :assessment_id
        ORDER BY aqs.sequence
    """),
        {"assessment_id": ASSESSMENT_ID},
    )

    responses = result.fetchall()

    if not responses:
        print("❌ No responses found! Assessment might not exist.")
        sys.exit(1)

    print(f"Found {len(responses)} responses\n")

    empty_responses = []

    for resp in responses:
        response_data = resp.response_data
        is_empty = not response_data or response_data == {}

        print(f"Q{resp.question_number} ({resp.question_type}):")
        print(f"  Response ID: {resp.response_id}")
        print(f"  Response Data: {json.dumps(response_data)}")

        if is_empty:
            print("  ⚠️  EMPTY RESPONSE!")
            empty_responses.append({
                "response_id": resp.response_id,
                "snapshot_id": resp.question_snapshot_id,
                "question_number": resp.question_number,
                "question_type": resp.question_type,
                "snapshot_metadata": resp.snapshot_metadata,
            })
        print()

    # 2. Fix empty responses
    if not empty_responses:
        print("✅ All responses have data - nothing to fix!")
        sys.exit(0)

    print("=" * 80)
    print(f"FOUND {len(empty_responses)} EMPTY RESPONSES")
    print("=" * 80)

    for item in empty_responses:
        print(f"\nQ{item["question_number"]} ({item["question_type"]})")
        print(f"  Response ID: {item["response_id"]}")

    print("\n" + "-" * 80)
    print("RECOMMENDATION:")
    print("-" * 80)

    print("""
The issue is that responses were submitted with empty data {}.
This usually happens when:
1. Frontend sent empty payload
2. Normalization logic filtered out the values
3. Client-side validation failed

To fix this, you need to either:
A) Re-submit the assessment with proper answers
B) Manually update response_data in DB (not recommended)

The root cause is in src/domain/services/submission.py:_normalize_response_payload()
Lines 256-259 only set response["value"] IF value is truthy.

If user sent:
  {"question_id": "...", "value": ""}

Then response_data becomes {} because empty string is falsy!

Fix: Update _normalize_response_payload to handle empty strings properly.
""")

    # 3. Check if this is truly the issue
    print("\n3. ANALYZING ROOT CAUSE...")
    print("-" * 80)

    for item in empty_responses:
        if item["question_type"] in ["profile", "essay"]:
            metadata = item.get("snapshot_metadata") or {}
            dimension = metadata.get("dimension")
            print(f"\nQ{item["question_number"]}:")
            print(f"  Type: {item["question_type"]}")
            print(f"  Dimension: {dimension or "N/A"}")
            print("  ⚠️  Empty response_data will cause FusionService to fail!")
            print("      Fix: User must re-answer or we update response_data manually")

print("\n" + "=" * 80)
print("ANALYSIS COMPLETE")
print("=" * 80)
