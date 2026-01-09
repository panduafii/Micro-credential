#!/usr/bin/env python3
"""
Fix Q7 to use simple text input format instead of compound dropdowns.
New format: User inputs "X bulan dan Y project" as answer_text
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

# New Q7 definition - SIMPLE TEXT INPUT format
# Frontend renders 2 number inputs, combines to: "X bulan dan Y project"
Q7_PROMPT = (
    "Sudah berapa lama Anda belajar programming dan berapa project yang sudah Anda kerjakan?"
)

Q7_NEW = {
    "prompt": Q7_PROMPT,
    "options": None,  # No dropdown options - just text inputs
    "expected_values": json.dumps({
        "type": "compound",
        "format": "text",  # Indicates simple text format
        "pattern": r"(\d+) bulan dan (\d+) project",  # Regex to parse
        "scoring": {
            # Score based on months
            "months": {
                "ranges": [
                    {"min": 0, "max": 3, "score": 10},
                    {"min": 4, "max": 6, "score": 25},
                    {"min": 7, "max": 12, "score": 50},
                    {"min": 13, "max": 24, "score": 75},
                    {"min": 25, "max": 999, "score": 100},
                ]
            },
            # Score based on projects
            "projects": {
                "ranges": [
                    {"min": 0, "max": 0, "score": 10},
                    {"min": 1, "max": 2, "score": 25},
                    {"min": 3, "max": 5, "score": 50},
                    {"min": 6, "max": 10, "score": 75},
                    {"min": 11, "max": 999, "score": 100},
                ]
            },
        },
        "weight": {"months": 0.5, "projects": 0.5},
    }),
    "metadata": json.dumps({"dimension": "experience-level", "type": "compound"}),
}


async def fix_q7():
    """Fix Q7 to simple text format."""
    print("\n" + "=" * 60)
    print("  Fixing Q7 to Simple Text Format")
    print("=" * 60)

    engine = create_async_engine(DATABASE_URL, echo=False)

    try:
        async with engine.begin() as conn:
            # Update Q7 for backend-engineer
            print("\n📝 Updating BE Q7 to simple text format...")

            query = text("""
                UPDATE question_templates
                SET prompt = :prompt,
                    options = :options,
                    expected_values = CAST(:expected_values AS jsonb),
                    metadata = CAST(:metadata AS jsonb),
                    updated_at = NOW()
                WHERE role_slug = 'backend-engineer'
                  AND sequence = 7
                RETURNING id, prompt
            """).bindparams(
                prompt=Q7_PROMPT,
                options=None,
                expected_values=Q7_NEW["expected_values"],
                metadata=Q7_NEW["metadata"],
            )

            result = await conn.execute(query)
            row = result.fetchone()

            if row:
                print(f"   ✅ Updated Q7: {row[0]}")
                print(f"      Prompt: {row[1][:50]}...")
            else:
                print("   ⚠️ Q7 not found for backend-engineer")

            # Update Q7 for data-analyst
            print("\n📝 Updating DA Q7 to simple text format...")

            query_da = text("""
                UPDATE question_templates
                SET prompt = :prompt,
                    options = :options,
                    expected_values = CAST(:expected_values AS jsonb),
                    metadata = CAST(:metadata AS jsonb),
                    updated_at = NOW()
                WHERE role_slug = 'data-analyst'
                  AND sequence = 7
                RETURNING id, prompt
            """).bindparams(
                prompt=Q7_PROMPT,
                options=None,
                expected_values=Q7_NEW["expected_values"],
                metadata=Q7_NEW["metadata"],
            )

            result_da = await conn.execute(query_da)
            row_da = result_da.fetchone()

            if row_da:
                print(f"   ✅ Updated Q7: {row_da[0]}")
            else:
                print("   ⚠️ Q7 not found for data-analyst")

            print("\n✅ Q7 update complete!")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        raise
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(fix_q7())
