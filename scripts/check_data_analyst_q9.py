#!/usr/bin/env python3
"""Check data-analyst Q9 options in database."""

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


async def check_q9():
    """Check Q9 options for data-analyst."""
    engine = create_async_engine(DATABASE_URL, connect_args={"ssl": "require"})

    try:
        async with engine.begin() as conn:
            # Get Q9 for data-analyst
            result = await conn.execute(
                text(
                    """
                    SELECT id, role_slug, sequence, prompt, options,
                           expected_values, metadata
                    FROM question_templates
                    WHERE role_slug = 'data-analyst'
                      AND sequence = 9
                      AND is_active = true
                    """
                )
            )
            row = result.fetchone()

            if not row:
                print("❌ Q9 not found for data-analyst")
                return False

            print(f"✅ Found Q9 (ID: {row[0]})")
            print(f"📋 Prompt: {row[3]}")
            print(f"📋 Options: {json.dumps(row[4], indent=2)}")
            print(f"📋 Expected values: {json.dumps(row[5], indent=2)}")
            print(f"📋 Metadata: {json.dumps(row[6], indent=2)}")

            # Check if options are wrong
            if row[4] and len(row[4]) > 0:
                option_texts = [opt.get("text", "") for opt in row[4]]
                if any("tertarik" in text.lower() for text in option_texts):
                    print("\n⚠️  PROBLEM: Options still using old 'interest level' format!")
                    print("Expected: Short/Medium/Long/Any duration")
                    print(f"Got: {option_texts}")
                    return False
                else:
                    print("\n✅ Options look correct!")
                    return True
            else:
                print("\n⚠️  No options found!")
                return False

    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(check_q9())
