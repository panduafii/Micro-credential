#!/usr/bin/env python3
"""Clear all draft assessments to force new snapshots."""

import asyncio
import os
import sys

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

# Get database URL
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("❌ ERROR: DATABASE_URL environment variable not set!")
    sys.exit(1)

# Ensure asyncpg driver
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
elif not DATABASE_URL.startswith("postgresql+asyncpg://"):
    DATABASE_URL = f"postgresql+asyncpg://{DATABASE_URL}"


async def clear_all_draft_assessments():
    """Clear all draft/in-progress assessments."""
    engine = create_async_engine(DATABASE_URL, connect_args={"ssl": "require"})

    try:
        async with engine.begin() as conn:
            print("\n" + "=" * 60)
            print("  CLEAR ALL DRAFT ASSESSMENTS")
            print("=" * 60)

            # Count assessments
            result = await conn.execute(
                text(
                    """
                    SELECT COUNT(*)
                    FROM assessments
                    WHERE status IN ('draft', 'in_progress')
                    """
                )
            )
            count = result.scalar()
            print(f"\n📊 Found {count} draft/in-progress assessments")

            if count == 0:
                print("✅ No assessments to clear!")
                return

            # Get user info
            result = await conn.execute(
                text(
                    """
                    SELECT a.id, a.owner_id, u.email, a.status,
                           a.created_at, r.name as role_name
                    FROM assessments a
                    JOIN users u ON a.owner_id = u.id
                    JOIN role_catalog r ON a.role_slug = r.slug
                    WHERE a.status IN ('draft', 'in_progress')
                    ORDER BY a.created_at DESC
                    """
                )
            )
            assessments = result.fetchall()

            print("\n📋 Assessments to be deleted:")
            for assessment in assessments:
                aid, owner, email, status, created, role = assessment
                print(f"   - {email[:30]:<30} | {role:<20} | " f"{status:<12} | {created}")

            # Delete snapshots first (foreign key)
            result = await conn.execute(
                text(
                    """
                    DELETE FROM assessment_question_snapshots
                    WHERE assessment_id IN (
                        SELECT id FROM assessments
                        WHERE status IN ('draft', 'in_progress')
                    )
                    """
                )
            )
            snapshots_deleted = result.rowcount
            print(f"\n🗑️  Deleted {snapshots_deleted} question snapshots")

            # Delete responses
            result = await conn.execute(
                text(
                    """
                    DELETE FROM assessment_responses
                    WHERE assessment_id IN (
                        SELECT id FROM assessments
                        WHERE status IN ('draft', 'in_progress')
                    )
                    """
                )
            )
            responses_deleted = result.rowcount
            print(f"🗑️  Deleted {responses_deleted} responses")

            # Delete assessments
            result = await conn.execute(
                text(
                    """
                    DELETE FROM assessments
                    WHERE status IN ('draft', 'in_progress')
                    """
                )
            )
            assessments_deleted = result.rowcount
            print(f"🗑️  Deleted {assessments_deleted} assessments")

            print("\n✅ All draft/in-progress assessments cleared!")
            print("\n💡 Users will get new questions when they " "start a new assessment")

    finally:
        await engine.dispose()


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("  WARNING: PRODUCTION DATABASE")
    print("=" * 60)
    print("\nThis will DELETE all draft/in-progress assessments.")
    print("Users will need to start new assessments.")
    print("Completed assessments will NOT be affected.")
    print("=" * 60)

    response = input("\nContinue? (yes/no): ")
    if response.lower() != "yes":
        print("❌ Cancelled.")
        sys.exit(0)

    asyncio.run(clear_all_draft_assessments())

    print("\n" + "=" * 60)
    print("  COMPLETE")
    print("=" * 60)
    print("\n✅ Users can now start new assessments with updated questions!\n")
