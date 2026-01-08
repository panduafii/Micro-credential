#!/usr/bin/env python3
"""Check backend-engineer Q9 and Q10."""

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
elif not DATABASE_URL.startswith("postgresql+asyncpg://"):
    DATABASE_URL = f"postgresql+asyncpg://{DATABASE_URL}"


async def check_questions():
    """Check Q9 and Q10 for backend-engineer."""
    engine = create_async_engine(DATABASE_URL, connect_args={"ssl": "require"})

    try:
        async with engine.begin() as conn:
            # Get Q9 and Q10
            result = await conn.execute(
                text(
                    """
                    SELECT sequence, prompt, options, expected_values
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
            print("BACKEND-ENGINEER PROFILE QUESTIONS Q9-Q10")
            print("=" * 60)

            for row in questions:
                seq, prompt, options, expected_values = row
                print(f"\n{"=" * 60}")
                print(f"Q{seq}: {prompt}")
                print(f"{"=" * 60}")

                if options:
                    print("\n📋 Options:")
                    for opt in options:
                        print(f"   {opt["id"]}. {opt["text"]}")

                if expected_values:
                    print("\n✨ Expected Values:")
                    print(f"   Accepted: {expected_values.get("accepted_values", [])}")
                    print(f"   Allow Custom: {expected_values.get("allow_custom", False)}")

                # Validation
                print("\n✅ Validation:")
                if seq == 9:
                    # Check duration options
                    option_texts = [opt["text"] for opt in options] if options else []
                    if any(
                        "jam" in text.lower() or "hour" in text.lower() for text in option_texts
                    ):
                        print("   ✅ Q9 has correct duration options!")
                    else:
                        print("   ❌ Q9 options still incorrect!")
                        print(f"   Got: {option_texts}")

                elif seq == 10:
                    # Check payment options
                    option_texts = [opt["text"] for opt in options] if options else []
                    if any(
                        "paid" in text.lower() or "free" in text.lower() for text in option_texts
                    ):
                        print("   ✅ Q10 has correct payment options!")
                    else:
                        print("   ❌ Q10 options still incorrect!")
                        print(f"   Got: {option_texts}")

            print("\n" + "=" * 60)
            print("✅ Check complete!")
            print("=" * 60)

    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(check_questions())
