#!/usr/bin/env python3
"""
Manual SQL update untuk fix expected_values dan metadata di production.
Langsung update kolom-kolom yang masih kosong.
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
    print("   Please set it with: export DATABASE_URL='postgresql+asyncpg://...'")
    sys.exit(1)

# Ensure asyncpg driver
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
elif not DATABASE_URL.startswith("postgresql+asyncpg://"):
    DATABASE_URL = f"postgresql+asyncpg://{DATABASE_URL}"

print("🔗 Connecting to database...")
print(f"   URL: {DATABASE_URL[:50]}...")


async def fix_backend_engineer_questions():
    """Fix backend-engineer Q8-Q10 expected_values and metadata."""
    print("\n" + "=" * 60)
    print("  Fixing BACKEND-ENGINEER Questions")
    print("=" * 60)

    engine = create_async_engine(DATABASE_URL, echo=False)

    try:
        async with engine.begin() as conn:
            # Q8: Tech preferences
            print("\n📝 Updating Q8 (tech-preferences)...")
            result = await conn.execute(
                text("""
                UPDATE question_templates
                SET
                    metadata = '{"dimension": "tech-preferences"}'::json,
                    expected_values = '{
                        "accepted_values": [
                            "docker", "kubernetes", "aws", "gcp", "azure",
                            "graphql", "redis", "kafka", "microservices",
                            "ci/cd", "terraform", "mongodb", "postgresql", "elasticsearch"
                        ],
                        "allow_custom": true
                    }'::json
                WHERE role_slug = 'backend-engineer'
                  AND sequence = 8
                  AND question_type = 'profile'
                RETURNING id, prompt;
            """)
            )
            row = result.fetchone()
            if row:
                print(f"   ✅ Updated Q8: {row[1][:60]}...")
            else:
                print("   ⚠️  No rows updated for Q8")

            # Q9: Duration preference
            print("\n📝 Updating Q9 (content-duration)...")
            result = await conn.execute(
                text("""
                UPDATE question_templates
                SET
                    metadata = '{"dimension": "content-duration"}'::json,
                    expected_values = '{
                        "accepted_values": ["short", "medium", "long", "any"],
                        "allow_custom": false
                    }'::json
                WHERE role_slug = 'backend-engineer'
                  AND sequence = 9
                  AND question_type = 'profile'
                RETURNING id, prompt;
            """)
            )
            row = result.fetchone()
            if row:
                print(f"   ✅ Updated Q9: {row[1][:60]}...")
            else:
                print("   ⚠️  No rows updated for Q9")

            # Q10: Payment preference
            print("\n📝 Updating Q10 (payment-preference)...")
            result = await conn.execute(
                text("""
                UPDATE question_templates
                SET
                    metadata = '{"dimension": "payment-preference"}'::json,
                    expected_values = '{
                        "accepted_values": ["paid", "free", "any"],
                        "allow_custom": false
                    }'::json
                WHERE role_slug = 'backend-engineer'
                  AND sequence = 10
                  AND question_type = 'profile'
                RETURNING id, prompt;
            """)
            )
            row = result.fetchone()
            if row:
                print(f"   ✅ Updated Q10: {row[1][:60]}...")
            else:
                print("   ⚠️  No rows updated for Q10")

            print("\n✅ Backend-engineer questions updated successfully!")

    except Exception as e:
        print(f"\n❌ Error updating backend-engineer: {e}")
        import traceback

        traceback.print_exc()
    finally:
        await engine.dispose()


async def fix_data_analyst_questions():
    """Fix data-analyst Q8-Q10 expected_values and metadata."""
    print("\n" + "=" * 60)
    print("  Fixing DATA-ANALYST Questions")
    print("=" * 60)

    engine = create_async_engine(DATABASE_URL, echo=False)

    try:
        async with engine.begin() as conn:
            # Q8: Tech preferences
            print("\n📝 Updating Q8 (tech-preferences)...")
            result = await conn.execute(
                text("""
                UPDATE question_templates
                SET
                    metadata = '{"dimension": "tech-preferences"}'::json,
                    expected_values = '{
                        "accepted_values": [
                            "python", "sql", "tableau", "power bi", "excel",
                            "r", "pandas", "numpy", "matplotlib", "seaborn",
                            "looker", "bigquery", "spark"
                        ],
                        "allow_custom": true
                    }'::json
                WHERE role_slug = 'data-analyst'
                  AND sequence = 8
                  AND question_type = 'profile'
                RETURNING id, prompt;
            """)
            )
            row = result.fetchone()
            if row:
                print(f"   ✅ Updated Q8: {row[1][:60]}...")
            else:
                print("   ⚠️  No rows updated for Q8")

            # Q9: Duration preference
            print("\n📝 Updating Q9 (content-duration)...")
            result = await conn.execute(
                text("""
                UPDATE question_templates
                SET
                    metadata = '{"dimension": "content-duration"}'::json,
                    expected_values = '{
                        "accepted_values": ["short", "medium", "long", "any"],
                        "allow_custom": false
                    }'::json
                WHERE role_slug = 'data-analyst'
                  AND sequence = 9
                  AND question_type = 'profile'
                RETURNING id, prompt;
            """)
            )
            row = result.fetchone()
            if row:
                print(f"   ✅ Updated Q9: {row[1][:60]}...")
            else:
                print("   ⚠️  No rows updated for Q9")

            # Q10: Payment preference
            print("\n📝 Updating Q10 (payment-preference)...")
            result = await conn.execute(
                text("""
                UPDATE question_templates
                SET
                    metadata = '{"dimension": "payment-preference"}'::json,
                    expected_values = '{
                        "accepted_values": ["paid", "free", "any"],
                        "allow_custom": false
                    }'::json
                WHERE role_slug = 'data-analyst'
                  AND sequence = 10
                  AND question_type = 'profile'
                RETURNING id, prompt;
            """)
            )
            row = result.fetchone()
            if row:
                print(f"   ✅ Updated Q10: {row[1][:60]}...")
            else:
                print("   ⚠️  No rows updated for Q10")

            print("\n✅ Data-analyst questions updated successfully!")

    except Exception as e:
        print(f"\n❌ Error updating data-analyst: {e}")
        import traceback

        traceback.print_exc()
    finally:
        await engine.dispose()


async def verify_updates():
    """Verify that updates were successful."""
    print("\n" + "=" * 60)
    print("  Verifying Updates")
    print("=" * 60)

    engine = create_async_engine(DATABASE_URL, echo=False)

    try:
        async with engine.begin() as conn:
            result = await conn.execute(
                text("""
                SELECT
                    role_slug,
                    sequence,
                    substring(prompt, 1, 50) as prompt_preview,
                    metadata->>'dimension' as dimension,
                    expected_values->>'allow_custom' as allow_custom,
                    jsonb_array_length(expected_values->'accepted_values') as values_count
                FROM question_templates
                WHERE (role_slug = 'backend-engineer' OR role_slug = 'data-analyst')
                  AND sequence IN (8, 9, 10)
                  AND question_type = 'profile'
                ORDER BY role_slug, sequence;
            """)
            )

            rows = result.fetchall()

            print("\n📊 Current state of profiling questions:\n")
            print(
                f"{"Role":<20} {"Q":<3} {"Dimension":<20} {"Custom":<8} {"Values":<8} {"Prompt":<50}"
            )
            print("-" * 110)

            for row in rows:
                role_slug, seq, prompt, dimension, allow_custom, values_count = row
                print(
                    f"{role_slug:<20} {seq:<3} {dimension or "N/A":<20} {allow_custom or "N/A":<8} {values_count or 0:<8} {prompt}..."
                )

            # Check if all are correct
            print("\n🔍 Validation:")
            all_good = True
            for row in rows:
                role_slug, seq, prompt, dimension, allow_custom, values_count = row
                if seq == 8:
                    if dimension != "tech-preferences":
                        print(
                            f"   ❌ {role_slug} Q8: dimension should be 'tech-preferences', got '{dimension}'"
                        )
                        all_good = False
                    if allow_custom != "true":
                        print(
                            f"   ❌ {role_slug} Q8: allow_custom should be 'true', got '{allow_custom}'"
                        )
                        all_good = False
                    if values_count < 10:
                        print(f"   ❌ {role_slug} Q8: should have 10+ values, got {values_count}")
                        all_good = False
                elif seq == 9:
                    if dimension != "content-duration":
                        print(
                            f"   ❌ {role_slug} Q9: dimension should be 'content-duration', got '{dimension}'"
                        )
                        all_good = False
                elif seq == 10:
                    if dimension != "payment-preference":
                        print(
                            f"   ❌ {role_slug} Q10: dimension should be 'payment-preference', got '{dimension}'"
                        )
                        all_good = False

            if all_good:
                print("   ✅ All validations passed!")
            else:
                print("   ⚠️  Some validations failed. Check above.")

    except Exception as e:
        print(f"\n❌ Error verifying: {e}")
        import traceback

        traceback.print_exc()
    finally:
        await engine.dispose()


async def main():
    """Main execution."""
    print("=" * 60)
    print("  MANUAL SQL FIX FOR PROFILING QUESTIONS")
    print("=" * 60)

    # Fix both roles
    await fix_backend_engineer_questions()
    await fix_data_analyst_questions()

    # Verify
    await verify_updates()

    print("\n" + "=" * 60)
    print("  COMPLETE")
    print("=" * 60)
    print("\n✅ Manual fix completed! Please test the API again.\n")


if __name__ == "__main__":
    asyncio.run(main())
