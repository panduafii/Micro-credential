#!/usr/bin/env python3
"""Check the actual state of production data to debug user's issue."""

import json
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

# Production database
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("❌ DATABASE_URL not found in environment")
    sys.exit(1)

# Convert asyncpg URL to psycopg2
if DATABASE_URL.startswith("postgresql+asyncpg://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")

engine = create_engine(DATABASE_URL)

print("=" * 80)
print("CHECKING PRODUCTION STATE")
print("=" * 80)

with engine.connect() as conn:
    # 1. Find the most recent assessment with Q8 response containing "golang" or "microservice"
    print("\n1. FINDING USER'S RECENT ASSESSMENTS...")
    print("-" * 80)

    result = conn.execute(
        text("""
        SELECT DISTINCT
            a.id as assessment_id,
            a.user_id,
            a.created_at,
            a.completed_at,
            s.profile_score,
            s.theory_score,
            s.essay_score
        FROM assessments a
        JOIN assessment_question_snapshots aqs ON a.id = aqs.assessment_id
        JOIN scores s ON a.id = s.assessment_id
        WHERE aqs.question_number = 8
        AND (
            aqs.response_text LIKE '%golang%'
            OR aqs.response_text LIKE '%microservice%'
            OR aqs.response_text LIKE '%redis%'
        )
        ORDER BY a.created_at DESC
        LIMIT 5
    """)
    )

    assessments = result.fetchall()

    if not assessments:
        print("❌ No assessments found with golang/microservice/redis in Q8")
        sys.exit(1)

    print(f"Found {len(assessments)} recent assessments:\n")
    for idx, row in enumerate(assessments, 1):
        print(f"{idx}. Assessment: {row.assessment_id}")
        print(f"   User ID: {row.user_id}")
        print(f"   Created: {row.created_at}")
        print(
            "   Profile: "
            f"{row.profile_score}%, "
            "Theory: "
            f"{row.theory_score}%, "
            "Essay: "
            f"{row.essay_score}%"
        )
        print()

    # Focus on the most recent one
    target_assessment_id = assessments[0].assessment_id

    print("=" * 80)
    print(f"ANALYZING ASSESSMENT: {target_assessment_id}")
    print("=" * 80)

    # 2. Check Q7-Q10 responses and metadata
    print("\n2. CHECKING Q7-Q10 RESPONSES & METADATA...")
    print("-" * 80)

    result = conn.execute(
        text("""
        SELECT
            question_number,
            response_text,
            metadata_json,
            score
        FROM assessment_question_snapshots
        WHERE assessment_id = :assessment_id
        AND question_number BETWEEN 7 AND 10
        ORDER BY question_number
    """),
        {"assessment_id": target_assessment_id},
    )

    questions = result.fetchall()

    for q in questions:
        metadata = json.loads(q.metadata_json) if q.metadata_json else {}
        dimension = metadata.get("dimension", "❌ NULL")

        print(f"\nQ{q.question_number} (dimension: {dimension})")
        print(f"  Response: {q.response_text}")
        print(f"  Score: {q.score}/100")
        print(f"  Full metadata: {json.dumps(metadata, indent=2)}")

    # 3. Check recommendation
    print("\n3. CHECKING RECOMMENDATION...")
    print("-" * 80)

    result = conn.execute(
        text("""
        SELECT
            id,
            created_at,
            summary_markdown,
            LEFT(summary_markdown, 500) as summary_preview
        FROM recommendations
        WHERE assessment_id = :assessment_id
        ORDER BY created_at DESC
        LIMIT 1
    """),
        {"assessment_id": target_assessment_id},
    )

    rec = result.fetchone()

    if rec:
        print(f"Recommendation ID: {rec.id}")
        print(f"Created: {rec.created_at}")
        print("\nSummary Preview:")
        print("-" * 80)
        print(rec.summary_preview)
        print("...")

        # Check if summary mentions user's tech preferences
        summary = rec.summary_markdown.lower()
        tech_mentions = []
        for tech in ["golang", "microservice", "redis", "postgresql", "mongodb"]:
            if tech in summary:
                tech_mentions.append(f"✅ {tech}")
            else:
                tech_mentions.append(f"❌ {tech}")

        print("\nTech Mentions in Summary:")
        for mention in tech_mentions:
            print(f"  {mention}")

        # Check for the problematic message
        if "haven't specified" in summary or "haven't mentioned" in summary:
            print("\n⚠️  FOUND PROBLEMATIC MESSAGE: 'haven't specified technologies'")
        else:
            print("\n✅ No 'haven't specified' message found")
    else:
        print("❌ No recommendation found for this assessment!")

    # 4. Check recommendation items
    print("\n4. CHECKING RECOMMENDATION ITEMS (TOP 5)...")
    print("-" * 80)

    if rec:
        result = conn.execute(
            text("""
            SELECT
                ri.rank,
                ri.course_title,
                ri.relevance_score,
                ri.match_explanation
            FROM recommendation_items ri
            WHERE ri.recommendation_id = :rec_id
            ORDER BY ri.rank
            LIMIT 5
        """),
            {"rec_id": rec.id},
        )

        items = result.fetchall()

        if items:
            for item in items:
                print(f"\n#{item.rank}. {item.course_title}")
                print(f"    Relevance: {item.relevance_score}")
                print(f"    Reason: {item.match_explanation}")
        else:
            print("❌ No recommendation items found!")

print("\n" + "=" * 80)
print("ANALYSIS COMPLETE")
print("=" * 80)
