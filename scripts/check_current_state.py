#!/usr/bin/env python3
"""Simple check - verify response data and see current recommendation."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


from sqlalchemy import create_engine, text

# Production database
PROD_DB_URL = "postgresql://microcred_user:3i1doEdivimrYo1RaXr6ANlJE7il4Pfb@dpg-d59hv62li9vc73al72ug-a.singapore-postgres.render.com/microcred"

engine = create_engine(PROD_DB_URL)

ASSESSMENT_ID = "d159d295-87f0-47b7-bb9c-ea3c5420d0e4"

print("=" * 80)
print(f"CHECKING ASSESSMENT: {ASSESSMENT_ID}")
print("=" * 80)

with engine.connect() as conn:
    # 1. Check response data
    print("\n1. RESPONSE DATA (Q7-Q10):")
    print("-" * 80)

    result = conn.execute(
        text("""
        SELECT
            aqs.sequence,
            aqs.question_type,
            ar.response_data
        FROM assessment_responses ar
        JOIN assessment_question_snapshots aqs ON ar.question_snapshot_id = aqs.id
        WHERE ar.assessment_id = :assessment_id
        AND aqs.sequence BETWEEN 7 AND 10
        ORDER BY aqs.sequence
    """),
        {"assessment_id": ASSESSMENT_ID},
    )

    for row in result:
        data = row.response_data
        value = data.get("value", "EMPTY") if data else "NULL"
        print(f"  Q{row.sequence} ({row.question_type}): {value}")

    # 2. Check recommendation
    print("\n2. CURRENT RECOMMENDATION:")
    print("-" * 80)

    result = conn.execute(
        text("""
        SELECT
            id,
            created_at,
            overall_score,
            degraded,
            summary
        FROM recommendations
        WHERE assessment_id = :assessment_id
        ORDER BY created_at DESC
        LIMIT 1
    """),
        {"assessment_id": ASSESSMENT_ID},
    )

    rec = result.fetchone()

    if rec:
        print(f"ID: {rec.id}")
        print(f"Created: {rec.created_at}")
        print(f"Score: {rec.overall_score}")
        print(f"Degraded: {rec.degraded}")
        print("\nSummary (first 800 chars):")
        print("-" * 80)
        print(rec.summary[:800])
        print("...")

        # Check tech mentions
        summary_lower = rec.summary.lower()
        print("\n" + "-" * 80)
        print("TECH MENTIONS:")
        for tech in ["golang", "go ", "microservice", "redis", "postgresql", "mongodb"]:
            if tech in summary_lower:
                print(f"  ✅ {tech}")
            else:
                print(f"  ❌ {tech}")

        if "haven't specified" in summary_lower or "haven't mentioned" in summary_lower:
            print("\n⚠️  Contains 'haven't specified' message")
        else:
            print("\n✅ No 'haven't specified' message")
    else:
        print("❌ No recommendation found!")

    # 3. Check recommendation items (top 5)
    print("\n3. TOP 5 RECOMMENDATION ITEMS:")
    print("-" * 80)

    if rec:
        result = conn.execute(
            text("""
            SELECT
                rank,
                course_title,
                relevance_score,
                match_explanation
            FROM recommendation_items
            WHERE recommendation_id = :rec_id
            ORDER BY rank
            LIMIT 5
        """),
            {"rec_id": rec.id},
        )

        items = result.fetchall()
        if items:
            for item in items:
                print(f"\n#{item.rank}. {item.course_title}")
                print(f"    Score: {item.relevance_score}")
                print(f"    Reason: {item.match_explanation[:100]}...")
        else:
            print("No items found")

print("\n" + "=" * 80)
print("DONE")
print("=" * 80)
