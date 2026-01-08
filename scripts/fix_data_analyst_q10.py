#!/usr/bin/env python3
"""Fix data-analyst Q10 options in database."""

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


async def fix_q10():
    """Fix Q10 options for data-analyst."""
    engine = create_async_engine(DATABASE_URL, connect_args={"ssl": "require"})

    # Correct options for Q10 (payment preference)
    correct_options = [
        {"id": "A", "text": "Paid courses only"},
        {"id": "B", "text": "Free courses only"},
        {"id": "C", "text": "Any (both paid and free)"},
    ]

    try:
        async with engine.begin() as conn:
            print("\n📝 Updating Q10 options for data-analyst...")

            # Update question_templates
            await conn.execute(
                text(
                    """
                    UPDATE question_templates
                    SET options = :options,
                        updated_at = NOW()
                    WHERE role_slug = 'data-analyst'
                      AND sequence = 10
                      AND is_active = true
                    """
                ),
                {"options": json.dumps(correct_options)},
            )

            print("✅ Updated question_templates for Q10")

            # Verify
            result = await conn.execute(
                text(
                    """
                    SELECT id, prompt, options
                    FROM question_templates
                    WHERE role_slug = 'data-analyst'
                      AND sequence = 10
                      AND is_active = true
                    """
                )
            )
            row = result.fetchone()

            if row:
                print("\n✅ Verification:")
                print(f"   ID: {row[0]}")
                print(f"   Prompt: {row[1]}")
                print(f"   Options: {json.dumps(row[2], indent=2)}")
                print("\n✅ Q10 fixed successfully!")
                print(
                    "\n⚠️  Note: Existing assessments akan tetap " "pakai options lama (snapshots)"
                )
                print("   Assessments baru akan pakai options yang benar.")
            else:
                print("❌ Q10 not found after update!")

    finally:
        await engine.dispose()


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("FIX DATA-ANALYST Q10 OPTIONS")
    print("=" * 60)
    print("\nThis will update Q10 options from:")
    print("  OLD: Kurang percaya diri / Cukup / etc.")
    print("  NEW: Paid / Free / Any")
    print("\n⚠️  This affects PRODUCTION database!")
    print("=" * 60)

    response = input("\nContinue? (yes/no): ")
    if response.lower() != "yes":
        print("❌ Cancelled.")
        sys.exit(0)

    asyncio.run(fix_q10())
