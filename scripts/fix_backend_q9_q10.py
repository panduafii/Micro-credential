#!/usr/bin/env python3
"""Fix backend-engineer Q9 and Q10 options in database."""

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
    sys.exit(1)

# Ensure asyncpg driver
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
elif not DATABASE_URL.startswith("postgresql+asyncpg://"):
    DATABASE_URL = f"postgresql+asyncpg://{DATABASE_URL}"

print("🔗 Connecting to database...")


async def fix_backend_questions():
    """Fix Q9 and Q10 options for backend-engineer."""
    engine = create_async_engine(DATABASE_URL, connect_args={"ssl": "require"})

    # Correct options for Q9 (duration preference)
    q9_options = [
        {"id": "A", "text": "Short (< 5 jam)"},
        {"id": "B", "text": "Medium (5-15 jam)"},
        {"id": "C", "text": "Long (> 15 jam)"},
        {"id": "D", "text": "Any duration"},
    ]

    # Correct options for Q10 (payment preference)
    q10_options = [
        {"id": "A", "text": "Paid courses only"},
        {"id": "B", "text": "Free courses only"},
        {"id": "C", "text": "Any (both paid and free)"},
    ]

    try:
        async with engine.begin() as conn:
            print("\n📝 Updating Q9 options for backend-engineer...")
            await conn.execute(
                text(
                    """
                    UPDATE question_templates
                    SET options = :options,
                        updated_at = NOW()
                    WHERE role_slug = 'backend-engineer'
                      AND sequence = 9
                      AND is_active = true
                    """
                ),
                {"options": json.dumps(q9_options)},
            )
            print("✅ Updated Q9")

            print("\n📝 Updating Q10 options for backend-engineer...")
            await conn.execute(
                text(
                    """
                    UPDATE question_templates
                    SET options = :options,
                        updated_at = NOW()
                    WHERE role_slug = 'backend-engineer'
                      AND sequence = 10
                      AND is_active = true
                    """
                ),
                {"options": json.dumps(q10_options)},
            )
            print("✅ Updated Q10")

            # Verify
            result = await conn.execute(
                text(
                    """
                    SELECT sequence, prompt, options
                    FROM question_templates
                    WHERE role_slug = 'backend-engineer'
                      AND sequence IN (9, 10)
                      AND is_active = true
                    ORDER BY sequence
                    """
                )
            )
            questions = result.fetchall()

            print("\n" + "=" * 60)
            print("✅ Verification:")
            print("=" * 60)

            for row in questions:
                seq, prompt, options = row
                print(f"\nQ{seq}: {prompt}")
                print("Options:")
                for opt in options:
                    print(f"   {opt["id"]}. {opt["text"]}")

            print("\n" + "=" * 60)
            print("✅ All questions fixed successfully!")
            print("=" * 60)
            print("\n⚠️  Note: Existing assessments akan tetap pakai options lama " "(snapshots)")
            print("   Assessments baru akan pakai options yang benar.")

    finally:
        await engine.dispose()


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("FIX BACKEND-ENGINEER Q9 & Q10 OPTIONS")
    print("=" * 60)
    print("\nThis will update:")
    print("  Q9: Duration preference (Short/Medium/Long/Any)")
    print("  Q10: Payment preference (Paid/Free/Any)")
    print("\n⚠️  This affects PRODUCTION database!")
    print("=" * 60)

    response = input("\nContinue? (yes/no): ")
    if response.lower() != "yes":
        print("❌ Cancelled.")
        sys.exit(0)

    asyncio.run(fix_backend_questions())
