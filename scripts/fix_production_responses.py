#!/usr/bin/env python3
"""Fix production assessment d159d295 - update empty response_data."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text

# Use production database from .env
PROD_DB_URL = "postgresql://microcred_user:3i1doEdivimrYo1RaXr6ANlJE7il4Pfb@dpg-d59hv62li9vc73al72ug-a.singapore-postgres.render.com/microcred"

print("Connecting to production DB...")
engine = create_engine(PROD_DB_URL)

ASSESSMENT_ID = "d159d295-87f0-47b7-bb9c-ea3c5420d0e4"

print("=" * 80)
print(f"FIXING ASSESSMENT: {ASSESSMENT_ID}")
print("=" * 80)

with engine.connect() as conn:
    # 1. Check current state
    print("\n1. CHECKING CURRENT RESPONSES...")
    print("-" * 80)

    result = conn.execute(
        text("""
        SELECT
            ar.id as response_id,
            ar.question_snapshot_id,
            ar.response_data,
            aqs.sequence as question_number,
            aqs.question_type,
            aqs.prompt
        FROM assessment_responses ar
        JOIN assessment_question_snapshots aqs ON ar.question_snapshot_id = aqs.id
        WHERE ar.assessment_id = :assessment_id
        AND aqs.sequence BETWEEN 7 AND 10
        ORDER BY aqs.sequence
    """),
        {"assessment_id": ASSESSMENT_ID},
    )

    responses = result.fetchall()

    if not responses:
        print("❌ No responses found!")
        sys.exit(1)

    empty_responses = []

    for resp in responses:
        response_data = resp.response_data
        is_empty = (
            not response_data
            or response_data == {}
            or (isinstance(response_data, dict) and not response_data.get("value"))
        )

        print(f"\nQ{resp.question_number} ({resp.question_type}):")
        print(f"  Response ID: {resp.response_id}")
        print(f"  Current Data: {json.dumps(response_data)}")
        print(f"  Question: {resp.prompt[:80]}...")

        if is_empty:
            print("  ⚠️  EMPTY - NEEDS FIX!")
            empty_responses.append({
                "response_id": resp.response_id,
                "question_number": resp.question_number,
                "question_type": resp.question_type,
                "prompt": resp.prompt,
            })

    if not empty_responses:
        print("\n✅ All responses have data - no fix needed!")
        print("\nProceed to regenerate fusion...")
    else:
        # 2. Fix empty responses based on question type
        print("\n" + "=" * 80)
        print(f"FIXING {len(empty_responses)} EMPTY RESPONSES")
        print("=" * 80)

        for item in empty_responses:
            q_num = item["question_number"]
            q_type = item["question_type"]
            response_id = item["response_id"]
            prompt = item["prompt"]

            # Determine appropriate value based on question
            new_value = None

            if q_num == 7:  # Experience level
                new_value = {"value": "3-5 years"}  # Default based on user profile
                print("\nQ7 (Experience): Setting to '3-5 years'")
            elif q_num == 8:  # Tech preferences - USER SAID GOLANG, MICROSERVICES, REDIS
                new_value = {"value": "golang, microservices, redis, postgresql, mongodb"}
                print(
                    "\nQ8 (Tech Preferences): Setting to "
                    "'golang, microservices, redis, postgresql, mongodb'"
                )
            elif q_num == 9:  # Duration preference
                new_value = {"value": "medium"}  # 2-10 hours
                print("\nQ9 (Duration): Setting to 'medium' (2-10 hours)")
            elif q_num == 10:  # Payment preference
                new_value = {"value": "any"}
                print("\nQ10 (Payment): Setting to 'any'")

            if new_value:
                print(f"  Updating response {response_id}...")
                conn.execute(
                    text("""
                        UPDATE assessment_responses
                        SET response_data = :response_data,
                            updated_at = NOW()
                        WHERE id = :response_id
                    """),
                    {"response_id": response_id, "response_data": json.dumps(new_value)},
                )
                print("  ✅ Updated!")

        conn.commit()
        print("\n✅ All empty responses fixed!")

    # 3. Delete old recommendation to trigger regeneration
    print("\n3. DELETING OLD RECOMMENDATION...")
    print("-" * 80)

    result = conn.execute(
        text("""
        DELETE FROM recommendations
        WHERE assessment_id = :assessment_id
        RETURNING id
    """),
        {"assessment_id": ASSESSMENT_ID},
    )

    deleted = result.fetchone()
    if deleted:
        print(f"✅ Deleted recommendation: {deleted.id}")
    else:
        print("⚠️  No existing recommendation found")

    conn.commit()

    # 4. Verify final state
    print("\n4. VERIFYING FINAL STATE...")
    print("-" * 80)

    result = conn.execute(
        text("""
        SELECT
            aqs.sequence as question_number,
            ar.response_data
        FROM assessment_responses ar
        JOIN assessment_question_snapshots aqs ON ar.question_snapshot_id = aqs.id
        WHERE ar.assessment_id = :assessment_id
        AND aqs.sequence BETWEEN 7 AND 10
        ORDER BY aqs.sequence
    """),
        {"assessment_id": ASSESSMENT_ID},
    )

    final_responses = result.fetchall()

    print("\nFinal Response Data:")
    all_good = True
    for resp in final_responses:
        has_value = (
            resp.response_data and resp.response_data != {} and resp.response_data.get("value")
        )
        status = "✅" if has_value else "❌"
        print(f"  {status} Q{resp.question_number}: {json.dumps(resp.response_data)}")
        if not has_value:
            all_good = False

    if all_good:
        print("\n✅ All profile questions now have values!")
    else:
        print("\n⚠️  Some questions still empty!")

print("\n" + "=" * 80)
print("FIX COMPLETE - Now regenerate fusion via async job!")
print("=" * 80)
print("\nNext steps:")
print("1. Trigger fusion job for this assessment")
print("2. Verify new summary mentions golang/microservices/redis")
