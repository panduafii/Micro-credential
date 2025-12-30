#!/usr/bin/env python
# ruff: noqa: E402, I001
"""
Natural flow test: Complete assessment dengan jawaban realistis.

Test end-to-end flow dengan:
- Jawaban theoretical yang benar
- Jawaban profile yang natural
- Jawaban essay programming test yang lengkap
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import asyncio

import structlog
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from src.infrastructure.db.models import AssessmentResponse
from src.core.config import get_settings
from src.domain.services.submission import SubmissionService
from scripts.process_jobs import process_assessment_jobs

logger = structlog.get_logger(__name__)

# Realistic answers for backend-engineer role
NATURAL_ANSWERS = {
    # Theoretical questions (100 points each)
    1: {
        "response_data": {
            "answer_text": (
                "REST API menggunakan HTTP methods (GET, POST, PUT, DELETE) dan "
                "multiple endpoints, lebih simple dan cacheable. GraphQL menggunakan "
                "single endpoint dengan flexible query, client bisa request data spesifik. "
                "Gunakan REST untuk API public yang simple. Gunakan GraphQL jika client "
                "butuh flexibility dan ingin avoid over-fetching/under-fetching data."
            ),
        }
    },
    2: {
        "response_data": {
            "answer_text": (
                "Database indexing membuat struktur data terpisah untuk mempercepat query. "
                "Index sebaiknya dibuat pada kolom yang sering digunakan untuk WHERE, JOIN, "
                "atau ORDER BY. Jangan over-index karena memperlambat INSERT/UPDATE. "
                "Contoh: kolom user_id, email, created_at sering di-index. "
                "Gunakan EXPLAIN query untuk analyze performance."
            ),
        }
    },
    3: {
        "response_data": {
            "answer_text": (
                "Caching menyimpan data temporary untuk mengurangi load dan latency. "
                "3 strategi: 1) Cache-aside - aplikasi cek cache dulu, miss → query DB. "
                "2) Write-through - update cache dan DB bersamaan. "
                "3) Write-behind - update cache dulu, async update ke DB. "
                "Pilih berdasarkan consistency requirement dan read/write pattern."
            ),
        }
    },
    # Essay questions (100 points each)
    4: {
        "response_data": {
            "answer_text": """
# Python FastAPI Example
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()

class Product(BaseModel):
    name: str
    price: float
    stock: int

products_db = {}

@router.get("/products")
async def list_products():
    return {"products": list(products_db.values())}

@router.post("/products")
async def create_product(product: Product):
    product_id = len(products_db) + 1
    products_db[product_id] = {"id": product_id, **product.dict()}
    return products_db[product_id]

@router.put("/products/{product_id}")
async def update_product(product_id: int, product: Product):
    if product_id not in products_db:
        raise HTTPException(status_code=404, detail="Product not found")
    products_db[product_id].update(product.dict())
    return products_db[product_id]

@router.delete("/products/{product_id}")
async def delete_product(product_id: int):
    if product_id not in products_db:
        raise HTTPException(status_code=404, detail="Product not found")
    del products_db[product_id]
    return {"message": "Product deleted"}
""",
        }
    },
    5: {
        "response_data": {
            "answer_text": """
import unittest
import re

def validate_email(email):
    if not email or email is None:
        return False
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

class TestEmailValidation(unittest.TestCase):
    def test_valid_email(self):
        self.assertTrue(validate_email("user@example.com"))
        self.assertTrue(validate_email("test.user@company.co.id"))
    
    def test_invalid_format(self):
        self.assertFalse(validate_email("notanemail"))
        self.assertFalse(validate_email("@example.com"))
        self.assertFalse(validate_email("user@"))
    
    def test_empty_string(self):
        self.assertFalse(validate_email(""))
    
    def test_null_value(self):
        self.assertFalse(validate_email(None))
    
    def test_special_characters(self):
        self.assertTrue(validate_email("user+tag@example.com"))
        self.assertTrue(validate_email("user_name@example.com"))
""",
        }
    },
    6: {
        "response_data": {
            "answer_text": """
-- E-commerce Database Schema

CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_email (email)
);

CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    price DECIMAL(10,2) NOT NULL,
    stock INT DEFAULT 0,
    category VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_category (category)
);

CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    user_id INT NOT NULL,
    total_amount DECIMAL(10,2) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    INDEX idx_user_status (user_id, status)
);

CREATE TABLE order_items (
    id SERIAL PRIMARY KEY,
    order_id INT NOT NULL,
    product_id INT NOT NULL,
    quantity INT NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(id)
);

-- Relasi: User 1-to-Many Orders, Order 1-to-Many OrderItems, Product referenced by OrderItems
""",
        }
    },
    # Profile questions (50 points each)
    7: {
        "response_data": {
            "answer_text": (
                "3 tahun pengalaman, termasuk 1 tahun "
                "sebagai Senior Backend Engineer di startup fintech."
            )
        }
    },
    8: {
        "response_data": {
            "answer_text": (
                "Python dengan FastAPI/Django, Node.js dengan Express, "
                "PostgreSQL dan MongoDB untuk database."
            )
        }
    },
    9: {
        "response_data": {
            "answer_text": (
                "Ya, pernah deploy ke AWS EC2 dan Heroku untuk startup, "
                "juga Docker container ke Google Cloud Run untuk project freelance."
            )
        }
    },
    10: {
        "response_data": {
            "answer_text": (
                "Handling 1000+ concurrent requests menyebabkan database timeout. "
                "Solusi: implement connection pooling, add Redis cache untuk "
                "frequent queries, dan optimize slow queries dengan indexing."
            )
        }
    },
}


async def submit_realistic_assessment(role_slug: str = "backend-engineer"):
    """Submit assessment dengan jawaban natural dan lengkap."""
    from src.domain import User
    from src.domain.services.assessments import AssessmentService

    settings = get_settings()
    engine = create_async_engine(settings.database_url)
    async_session_maker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session_maker() as session:
        # 1. Create assessment properly with questions
        assessment_service = AssessmentService(session)
        user = User(user_id="test-user-natural", roles=["student"])

        result = await assessment_service.start_or_resume(
            user=user,
            role_slug=role_slug,
        )

        assessment_id = result["assessment_id"]
        questions = result["questions"]

        print(f"\n📝 Assessment ID: {assessment_id}")
        print(f"📋 Role: {role_slug}")
        print(f"❓ Questions: {len(questions)}")
        print("\n" + "=" * 60)

        # 2. Fill in answers for all questions
        answered = 0
        for q in questions:
            seq = q["sequence"]
            if seq in NATURAL_ANSWERS:
                response = AssessmentResponse(
                    assessment_id=assessment_id,
                    question_snapshot_id=q["id"],
                    response_data=NATURAL_ANSWERS[seq]["response_data"],
                )
                session.add(response)
                answered += 1

                # Show preview
                answer_text = NATURAL_ANSWERS[seq]["response_data"].get("answer_text", "")
                preview = answer_text[:80] + "..." if len(answer_text) > 80 else answer_text
                print(f"✅ Q{seq} ({q["question_type"]}): {preview}")

        await session.commit()
        print(f"\n✅ Answered {answered}/{len(questions)} questions")
        print("=" * 60)

        # 3. Submit assessment (trigger scoring)
        submission_service = SubmissionService(session)
        submit_result = await submission_service.submit_assessment(
            assessment_id=assessment_id,
            user_id="test-user-natural",
        )

        print("\n🚀 Assessment submitted!")
        scores = submit_result.scores
        theoretical = scores.get("theoretical", {})
        profile = scores.get("profile", {})
        essay = scores.get("essay", {})

        print(f"📊 Theoretical Score: {theoretical.get("total", 0)}/{theoretical.get("max", 0)}")
        print(f"👤 Profile Score: {profile.get("total", 0)}/{profile.get("max", 0)}")
        print(f"✍️  Essay Score: {essay.get("total", 0)}/{essay.get("max", 0)}")

        total = theoretical.get("total", 0) + profile.get("total", 0) + essay.get("total", 0)
        print(f"📈 Total: {total}")
        print(f"🔄 Jobs Queued: {", ".join(submit_result.jobs_queued)}")
        print(f"⚠️  Degraded: {submit_result.degraded}")
        print("=" * 60)

        return assessment_id


async def main():
    """Run natural flow test."""
    print("\n" + "=" * 60)
    print("🧪 NATURAL FLOW TEST - Backend Engineer Assessment")
    print("=" * 60)

    # Step 1: Create and fill assessment
    assessment_id = await submit_realistic_assessment("backend-engineer")

    if not assessment_id:
        print("\n❌ Failed to create assessment")
        return

    # Step 2: Process async jobs
    print("\n⏳ Processing async jobs (GPT, RAG, Fusion)...")
    print("=" * 60)

    try:
        await process_assessment_jobs(assessment_id)
        print("\n🎉 All jobs completed successfully!")
    except Exception as e:
        print(f"\n❌ Job processing failed: {e}")
        return

    # Step 3: Show result summary
    print("\n" + "=" * 60)
    print("📊 ASSESSMENT RESULT SUMMARY")
    print("=" * 60)
    print(f"Assessment ID: {assessment_id}")
    print("\nℹ️  Get full result:")
    print(f"   curl http://localhost:8000/assessments/{assessment_id}/result \\")
    print("        -H 'Authorization: Bearer YOUR_TOKEN'")
    print("\nℹ️  Or check in API:")
    print(f"   GET /assessments/{assessment_id}/result")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
