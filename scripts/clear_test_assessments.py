#!/usr/bin/env python3
"""
Clear test assessments so new snapshots can be created with updated questions.
"""

import asyncio
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

print("🔗 Connecting to database...")


async def clear_test_assessments():
    """Clear assessments for test user."""
    engine = create_async_engine(DATABASE_URL, echo=False)

    try:
        async with engine.begin() as conn:
            # Get test user ID
            result = await conn.execute(
                text("SELECT id FROM users WHERE email = 'test@example.com'")
            )
            user_row = result.fetchone()

            if not user_row:
                print("⚠️  No test user found with email test@example.com")
                return

            user_id = user_row[0]
            print(f"📋 Found test user: {user_id}")

            # Count assessments
            result = await conn.execute(
                text("SELECT COUNT(*) FROM assessments WHERE owner_id = :user_id"),
                {"user_id": user_id},
            )
            count = result.scalar()
            print(f"📊 Found {count} assessments for test user")

            if count == 0:
                print("✅ No assessments to clear")
                return

            # Delete assessment snapshots first (foreign key constraint)
            result = await conn.execute(
                text(
                    """
                DELETE FROM assessment_question_snapshots
                WHERE assessment_id IN (
                    SELECT id FROM assessments WHERE owner_id = :user_id
                )
            """
                ),
                {"user_id": user_id},
            )
            print(f"🗑️  Deleted {result.rowcount} question snapshots")

            # Delete assessment responses
            result = await conn.execute(
                text(
                    """
                DELETE FROM assessment_responses
                WHERE question_snapshot_id IN (
                    SELECT aqs.id FROM assessment_question_snapshots aqs
                    JOIN assessments a ON aqs.assessment_id = a.id
                    WHERE a.owner_id = :user_id
                )
            """
                ),
                {"user_id": user_id},
            )
            print(f"🗑️  Deleted {result.rowcount} responses")

            # Delete assessments
            result = await conn.execute(
                text("DELETE FROM assessments WHERE owner_id = :user_id"),
                {"user_id": user_id},
            )
            print(f"🗑️  Deleted {result.rowcount} assessments")

            print("✅ All test assessments cleared!")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()
    finally:
        await engine.dispose()


async def main():
    print("=" * 60)
    print("  CLEAR TEST ASSESSMENTS")
    print("=" * 60)
    await clear_test_assessments()
    print("=" * 60)
    print("  COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
