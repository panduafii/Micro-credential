#!/usr/bin/env python3
"""
Fix question metadata and update profile questions in production.
This script:
1. Updates Q7 to ask about months of experience + number of projects
2. Updates Q8-Q10 metadata for personalization dimensions
"""

import asyncio
import json
import os
import sys

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

# Get production database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("❌ ERROR: DATABASE_URL environment variable not set!")
    print("   Please set it with: export DATABASE_URL='postgresql+asyncpg://...'")
    sys.exit(1)

# Ensure asyncpg driver
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
elif not DATABASE_URL.startswith("postgresql+asyncpg://"):
    DATABASE_URL = f"postgresql+asyncpg://{DATABASE_URL}"

print("🔗 Connecting to database...")
print(f"   URL: {DATABASE_URL[:50]}...")


# New Q7 definition - compound question with TWO separate selections
# Frontend should render two dropdowns, submit as {"months": "X", "projects": "Y"}
Q7_PROMPT = (
    "Sudah berapa lama Anda belajar programming dan berapa project " "yang sudah Anda kerjakan?"
)
Q7_NEW = {
    "prompt": Q7_PROMPT,
    "options": json.dumps({
        "type": "compound",
        "fields": [
            {
                "id": "months",
                "label": "Lama belajar programming:",
                "type": "select",
                "options": [
                    {"value": "0-3", "text": "0-3 bulan"},
                    {"value": "3-6", "text": "3-6 bulan"},
                    {"value": "6-12", "text": "6-12 bulan"},
                    {"value": "12-24", "text": "1-2 tahun"},
                    {"value": "24+", "text": "> 2 tahun"},
                ],
            },
            {
                "id": "projects",
                "label": "Jumlah project yang dikerjakan:",
                "type": "select",
                "options": [
                    {"value": "0", "text": "0 project"},
                    {"value": "1-2", "text": "1-2 project"},
                    {"value": "3-5", "text": "3-5 project"},
                    {"value": "6-10", "text": "6-10 project"},
                    {"value": "10+", "text": "> 10 project"},
                ],
            },
        ],
        "display_format": "{months} dan {projects}",  # How to display the answer
    }),
    "expected_values": json.dumps({
        "type": "compound",
        "scoring": {
            "months": {"0-3": 10, "3-6": 25, "6-12": 50, "12-24": 75, "24+": 100},
            "projects": {"0": 10, "1-2": 25, "3-5": 50, "6-10": 75, "10+": 100},
        },
        "weight": {"months": 0.5, "projects": 0.5},
    }),
    "metadata": json.dumps({"dimension": "experience-level", "type": "compound"}),
}


async def fix_all_questions():
    """Fix all profile questions."""
    print("\n" + "=" * 60)
    print("  Fixing Profile Questions")
    print("=" * 60)

    engine = create_async_engine(DATABASE_URL, echo=False)

    try:
        async with engine.begin() as conn:
            # ============================================
            # BACKEND ENGINEER
            # ============================================
            print("\n🔧 BACKEND ENGINEER Questions:")

            # Update Q7 - Experience Level (compound question)
            print("\n📝 Updating BE Q7 (experience-level - compound)...")
            result = await conn.execute(
                text(
                    """
                UPDATE question_templates
                SET
                    prompt = :prompt,
                    options = CAST(:options AS jsonb),
                    expected_values = CAST(:expected_values AS jsonb),
                    metadata = CAST(:metadata AS jsonb)
                WHERE role_slug = 'backend-engineer'
                  AND sequence = 7
                  AND question_type = 'profile'
                RETURNING id, prompt;
            """
                ).bindparams(
                    prompt=Q7_NEW["prompt"],
                    options=Q7_NEW["options"],
                    expected_values=Q7_NEW["expected_values"],
                    metadata=Q7_NEW["metadata"],
                )
            )
            row = result.fetchone()
            if row:
                print(f"   ✅ Updated Q7: {row[1][:60]}...")
            else:
                print("   ⚠️  No rows updated for BE Q7")

            # Update Q8 - tech-preferences
            print("\n📝 Updating BE Q8 (tech-preferences)...")
            result = await conn.execute(
                text("""
                UPDATE question_templates
                SET metadata = '{"dimension": "tech-preferences"}'::jsonb
                WHERE role_slug = 'backend-engineer'
                  AND sequence = 8
                  AND question_type = 'profile'
                RETURNING id, prompt, metadata;
            """)
            )
            row = result.fetchone()
            if row:
                print(f"   ✅ Updated: metadata={row[2]}")
            else:
                print("   ⚠️  No rows updated for BE Q8")

            # Update Q9 - content-duration
            print("\n📝 Updating BE Q9 (content-duration)...")
            result = await conn.execute(
                text("""
                UPDATE question_templates
                SET metadata = '{"dimension": "content-duration"}'::jsonb
                WHERE role_slug = 'backend-engineer'
                  AND sequence = 9
                  AND question_type = 'profile'
                RETURNING id, prompt, metadata;
            """)
            )
            row = result.fetchone()
            if row:
                print(f"   ✅ Updated: metadata={row[2]}")
            else:
                print("   ⚠️  No rows updated for BE Q9")

            # Update Q10 - payment-preference
            print("\n📝 Updating BE Q10 (payment-preference)...")
            result = await conn.execute(
                text("""
                UPDATE question_templates
                SET metadata = '{"dimension": "payment-preference"}'::jsonb
                WHERE role_slug = 'backend-engineer'
                  AND sequence = 10
                  AND question_type = 'profile'
                RETURNING id, prompt, metadata;
            """)
            )
            row = result.fetchone()
            if row:
                print(f"   ✅ Updated: metadata={row[2]}")
            else:
                print("   ⚠️  No rows updated for BE Q10")

            # ============================================
            # DATA ANALYST
            # ============================================
            print("\n🔧 DATA ANALYST Questions:")

            # Update Q7 - Experience Level (compound question)
            print("\n📝 Updating DA Q7 (experience-level - compound)...")
            result = await conn.execute(
                text(
                    """
                UPDATE question_templates
                SET
                    prompt = :prompt,
                    options = CAST(:options AS jsonb),
                    expected_values = CAST(:expected_values AS jsonb),
                    metadata = CAST(:metadata AS jsonb)
                WHERE role_slug = 'data-analyst'
                  AND sequence = 7
                  AND question_type = 'profile'
                RETURNING id, prompt;
            """
                ).bindparams(
                    prompt=Q7_NEW["prompt"],
                    options=Q7_NEW["options"],
                    expected_values=Q7_NEW["expected_values"],
                    metadata=Q7_NEW["metadata"],
                )
            )
            row = result.fetchone()
            if row:
                print(f"   ✅ Updated Q7: {row[1][:60]}...")
            else:
                print("   ⚠️  No rows updated for DA Q7")

            # Update Q8 - tech-preferences
            print("\n📝 Updating DA Q8 (tech-preferences)...")
            result = await conn.execute(
                text("""
                UPDATE question_templates
                SET metadata = '{"dimension": "tech-preferences"}'::jsonb
                WHERE role_slug = 'data-analyst'
                  AND sequence = 8
                  AND question_type = 'profile'
                RETURNING id, prompt, metadata;
            """)
            )
            row = result.fetchone()
            if row:
                print(f"   ✅ Updated: metadata={row[2]}")
            else:
                print("   ⚠️  No rows updated for DA Q8")

            # Update Q9 - content-duration
            print("\n📝 Updating DA Q9 (content-duration)...")
            result = await conn.execute(
                text("""
                UPDATE question_templates
                SET metadata = '{"dimension": "content-duration"}'::jsonb
                WHERE role_slug = 'data-analyst'
                  AND sequence = 9
                  AND question_type = 'profile'
                RETURNING id, prompt, metadata;
            """)
            )
            row = result.fetchone()
            if row:
                print(f"   ✅ Updated: metadata={row[2]}")
            else:
                print("   ⚠️  No rows updated for DA Q9")

            # Update Q10 - payment-preference
            print("\n📝 Updating DA Q10 (payment-preference)...")
            result = await conn.execute(
                text("""
                UPDATE question_templates
                SET metadata = '{"dimension": "payment-preference"}'::jsonb
                WHERE role_slug = 'data-analyst'
                  AND sequence = 10
                  AND question_type = 'profile'
                RETURNING id, prompt, metadata;
            """)
            )
            row = result.fetchone()
            if row:
                print(f"   ✅ Updated: metadata={row[2]}")
            else:
                print("   ⚠️  No rows updated for DA Q10")

            # ============================================
            # VERIFY ALL CHANGES
            # ============================================
            print("\n" + "=" * 60)
            print("  Verification")
            print("=" * 60)

            result = await conn.execute(
                text("""
                SELECT role_slug, sequence, prompt, metadata, expected_values
                FROM question_templates
                WHERE question_type = 'profile'
                  AND sequence IN (7, 8, 9, 10)
                ORDER BY role_slug, sequence;
            """)
            )
            rows = result.fetchall()
            for row in rows:
                print(f"\n{row[0]} Q{row[1]}:")
                print(f"   prompt: {row[2][:60]}...")
                print(f"   metadata: {row[3]}")

            print("\n✅ All updates completed!")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(fix_all_questions())
