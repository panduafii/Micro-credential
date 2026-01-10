#!/usr/bin/env python3
"""Deep debug assessment d159d295 - check all responses and metadata."""

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

# Get the actual Render production URL
DATABASE_URL = os.getenv("DATABASE_URL_PRODUCTION") or os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("❌ No DATABASE_URL found. Please set DATABASE_URL_PRODUCTION in .env")
    print("Expected format: postgresql://user:pass@host/db")
    sys.exit(1)

# Handle asyncpg -> psycopg2
if "asyncpg" in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")

print(f"Connecting to: {DATABASE_URL.split("@")[1] if "@" in DATABASE_URL else "local"}")

engine = create_engine(DATABASE_URL)

ASSESSMENT_ID = "d159d295-87f0-47b7-bb9c-ea3c5420d0e4"

print("=" * 80)
print(f"DEEP DEBUG ASSESSMENT: {ASSESSMENT_ID}")
print("=" * 80)

with engine.connect() as conn:
    # 1. Basic assessment info
    print("\n1. BASIC INFO")
    print("-" * 80)

    result = conn.execute(
        text("""
        SELECT
            id,
            user_id,
            role_slug,
            status,
            created_at,
            updated_at,
            completed_at
        FROM assessments
        WHERE id = :assessment_id
    """),
        {"assessment_id": ASSESSMENT_ID},
    )

    assessment = result.fetchone()
    if not assessment:
        print(f"❌ Assessment {ASSESSMENT_ID} not found!")
        sys.exit(1)

    print(f"User ID: {assessment.user_id}")
    print(f"Role: {assessment.role_slug}")
    print(f"Status: {assessment.status}")
    print(f"Created: {assessment.created_at}")
    print(f"Completed: {assessment.completed_at}")

    # 2. ALL question snapshots with detailed info
    print("\n2. ALL QUESTION SNAPSHOTS (Q1-Q10)")
    print("-" * 80)

    result = conn.execute(
        text("""
        SELECT
            question_number,
            question_template_id,
            question_text,
            response_text,
            metadata_json,
            score,
            max_score,
            created_at
        FROM assessment_question_snapshots
        WHERE assessment_id = :assessment_id
        ORDER BY question_number
    """),
        {"assessment_id": ASSESSMENT_ID},
    )

    snapshots = result.fetchall()

    empty_responses = []

    for snap in snapshots:
        print(f"\n{"=" * 80}")
        print(f"Q{snap.question_number} - Template ID: {snap.question_template_id}")
        print(f"{"=" * 80}")
        print(f"Question: {snap.question_text[:100]}...")
        print(f"\nResponse Text: {snap.response_text}")

        # Check if response is empty
        if snap.response_text in ["{}", None, ""] or snap.response_text.strip() in ["{}", ""]:
            empty_responses.append(snap.question_number)
            print("⚠️  EMPTY/NULL RESPONSE!")

        # Parse metadata
        if snap.metadata_json:
            metadata = json.loads(snap.metadata_json)
            print("\nMetadata:")
            print(json.dumps(metadata, indent=2))

            # Check dimension field
            dimension = metadata.get("dimension")
            if dimension:
                print(f"✅ Dimension: {dimension}")
            else:
                print("❌ No dimension field in metadata!")
        else:
            print("\n❌ Metadata is NULL!")

        print(f"\nScore: {snap.score}/{snap.max_score}")
        print(f"Created: {snap.created_at}")

    # 3. Summary of issues
    print("\n" + "=" * 80)
    print("ISSUE SUMMARY")
    print("=" * 80)

    if empty_responses:
        print(f"\n⚠️  FOUND {len(empty_responses)} EMPTY RESPONSES:")
        for q_num in empty_responses:
            print(f"  - Q{q_num}")
    else:
        print("\n✅ All questions have responses")

    # 4. Check the specific question templates mentioned by user
    print("\n3. CHECKING QUESTION TEMPLATES")
    print("-" * 80)

    template_ids = [
        "b56adda6-c443-4ecd-af94-9d05622289d0",
        "bb692efc-c489-487e-800e-7ebaaf666044",
        "14777c5d-53bc-4b4a-acee-48fbd91c4508",
        "9b6a6b36-8229-43a6-b792-f1f921390ba9",
        "134aacfe-92e1-46e7-874e-ddd4c7e7be2c",
        "f536ef49-00eb-4f14-ae84-41fd4d8a3e71",
        "f1b956c2-a407-43b2-bee8-e481af153868",
        "41927e4b-7f03-480c-ad54-8a95963a3209",
        "c74d3903-9007-4f8a-b7e0-4d218c3fc83f",
        "bd54cfe6-05e7-45d5-babc-eebf624eb14a",
    ]

    for _idx, tid in enumerate(template_ids, 1):
        result = conn.execute(
            text("""
            SELECT
                id,
                role_slug,
                question_number,
                question_text,
                metadata_json
            FROM question_templates
            WHERE id = :template_id
        """),
            {"template_id": tid},
        )

        template = result.fetchone()
        if template:
            metadata = json.loads(template.metadata_json) if template.metadata_json else {}
            dimension = metadata.get("dimension", "N/A")
            print(f"\nQ{template.question_number}: {template.id}")
            print(f"  Role: {template.role_slug}")
            print(f"  Dimension: {dimension}")
            print(f"  Text: {template.question_text[:60]}...")
        else:
            print(f"\n❌ Template {tid} not found")

    # 5. Check scores
    print("\n4. SCORES")
    print("-" * 80)

    result = conn.execute(
        text("""
        SELECT
            profile_score,
            theory_score,
            essay_score,
            created_at
        FROM scores
        WHERE assessment_id = :assessment_id
    """),
        {"assessment_id": ASSESSMENT_ID},
    )

    score = result.fetchone()
    if score:
        print(f"Profile: {score.profile_score}%")
        print(f"Theory: {score.theory_score}%")
        print(f"Essay: {score.essay_score}%")
        print(f"Created: {score.created_at}")
    else:
        print("❌ No scores found")

    # 6. Check recommendation
    print("\n5. RECOMMENDATION")
    print("-" * 80)

    result = conn.execute(
        text("""
        SELECT
            id,
            summary_markdown,
            created_at
        FROM recommendations
        WHERE assessment_id = :assessment_id
        ORDER BY created_at DESC
        LIMIT 1
    """),
        {"assessment_id": ASSESSMENT_ID},
    )

    rec = result.fetchone()
    if rec:
        print(f"Recommendation ID: {rec.id}")
        print(f"Created: {rec.created_at}")

        # Check for tech mentions
        summary = rec.summary_markdown.lower()
        print("\nTech mentions in summary:")
        for tech in ["golang", "microservice", "redis", "postgresql", "mongodb"]:
            if tech in summary:
                print(f"  ✅ {tech}")
            else:
                print(f"  ❌ {tech}")

        # Check for "haven't specified" message
        if "haven't specified" in summary or "haven't mentioned" in summary:
            print("\n⚠️  FOUND: 'haven't specified technologies' message")

        # Show first 300 chars
        print("\nSummary Preview:")
        print(rec.summary_markdown[:300])
        print("...")
    else:
        print("❌ No recommendation found")

print("\n" + "=" * 80)
print("DEBUG COMPLETE")
print("=" * 80)
