#!/usr/bin/env python3
"""
Script untuk seed soal via API endpoint (untuk production)

Jalankan dengan:
    export API_URL=https://microcred-api.onrender.com
    export ADMIN_EMAIL=admin@microcred.com
    export ADMIN_PASSWORD=SecurePass123!
    poetry run python scripts/seed_questions_api.py
"""

import os
import requests
from typing import Any

API_URL = os.getenv("API_URL", "https://microcred-api.onrender.com")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@microcred.com")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "SecurePass123!")


def get_admin_token() -> str:
    """Login and get admin token."""
    resp = requests.post(
        f"{API_URL}/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
    )
    resp.raise_for_status()
    return resp.json()["tokens"]["access_token"]


def create_question(token: str, question: dict[str, Any]) -> dict[str, Any]:
    """Create a question via API."""
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.post(f"{API_URL}/questions", json=question, headers=headers)
    if resp.status_code == 409:
        print(f"  ⚠️ Question already exists: {question['prompt'][:50]}...")
        return {"exists": True}
    resp.raise_for_status()
    return resp.json()


def delete_questions_by_track(token: str, role_slug: str) -> None:
    """Delete all questions for a track."""
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(f"{API_URL}/questions?role_slug={role_slug}", headers=headers)
    resp.raise_for_status()
    questions = resp.json()  # Response is a list directly
    
    for q in questions:
        resp = requests.delete(f"{API_URL}/questions/{q['id']}", headers=headers)
        if resp.status_code == 204:
            print(f"  🗑️ Deleted question {q['id']}")


# Questions for Backend Engineer track
BACKEND_QUESTIONS = [
    # === THEORETICAL (Pilihan Ganda) - 3 soal ===
    {
        "role_slug": "backend-engineer",
        "sequence": 1,
        "question_type": "theoretical",
        "prompt": "Apa perbedaan utama antara FastAPI dengan Flask dalam hal performa?",
        "options": [
            {"id": "A", "text": "FastAPI lebih lambat karena menggunakan type hints"},
            {"id": "B", "text": "FastAPI mendukung async/await secara native sehingga lebih efisien untuk I/O-bound tasks"},
            {"id": "C", "text": "Flask lebih cepat karena lebih ringan"},
            {"id": "D", "text": "Tidak ada perbedaan performa yang signifikan"},
        ],
        "correct_answer": "B",
        "difficulty": "medium",
        "weight": 1.0,
        "metadata": {"dimension": "framework-knowledge", "topic": "fastapi"},
    },
    {
        "role_slug": "backend-engineer",
        "sequence": 2,
        "question_type": "theoretical",
        "prompt": "Apa yang dimaksud dengan idempotency dalam REST API?",
        "options": [
            {"id": "A", "text": "Request yang sama menghasilkan response yang berbeda setiap kali"},
            {"id": "B", "text": "Request yang sama dapat dieksekusi berkali-kali dengan hasil yang sama"},
            {"id": "C", "text": "Request hanya boleh dieksekusi satu kali"},
            {"id": "D", "text": "Request yang membutuhkan autentikasi"},
        ],
        "correct_answer": "B",
        "difficulty": "medium",
        "weight": 1.0,
        "metadata": {"dimension": "api-design", "topic": "rest"},
    },
    {
        "role_slug": "backend-engineer",
        "sequence": 3,
        "question_type": "theoretical",
        "prompt": "Kapan sebaiknya menggunakan Redis sebagai cache?",
        "options": [
            {"id": "A", "text": "Untuk menyimpan data yang jarang berubah dan sering diakses"},
            {"id": "B", "text": "Untuk menyimpan semua data aplikasi"},
            {"id": "C", "text": "Hanya untuk session management"},
            {"id": "D", "text": "Redis tidak cocok untuk caching"},
        ],
        "correct_answer": "A",
        "difficulty": "easy",
        "weight": 1.0,
        "metadata": {"dimension": "infrastructure", "topic": "redis"},
    },
    # === ESSAY - 3 soal ===
    {
        "role_slug": "backend-engineer",
        "sequence": 4,
        "question_type": "essay",
        "prompt": "Rancang arsitektur sistem scoring hybrid (rule-based + GPT) yang dapat memenuhi SLA response time < 10 detik. Jelaskan komponen utama, alur data, dan strategi optimasi yang Anda gunakan.",
        "options": None,
        "correct_answer": None,
        "answer_key": "Arsitektur harus mencakup: 1) Rule engine untuk scoring cepat (theoretical/profile), 2) Queue system (Redis) untuk essay ke GPT, 3) Async processing dengan status polling, 4) Caching layer, 5) Fallback mechanism jika GPT timeout.",
        "model_answer": "Sistem scoring hybrid terdiri dari beberapa layer: 1) Synchronous Layer untuk rule-based scoring yang memproses theoretical dan profile questions secara langsung dengan latency <100ms. 2) Async Layer menggunakan Redis queue untuk essay scoring via GPT API. 3) Status Service yang menyediakan progress polling setiap 2-3 detik. 4) Fusion Service yang menggabungkan semua hasil menjadi summary. Optimasi: parallel processing, connection pooling, response caching.",
        "rubric": {
            "completeness": {"weight": 0.3, "description": "Mencakup semua komponen utama"},
            "technical_accuracy": {"weight": 0.3, "description": "Konsep teknis benar"},
            "optimization": {"weight": 0.2, "description": "Strategi optimasi yang valid"},
            "clarity": {"weight": 0.2, "description": "Penjelasan jelas dan terstruktur"},
        },
        "difficulty": "hard",
        "weight": 1.5,
        "metadata": {"dimension": "system-design", "topic": "architecture"},
    },
    {
        "role_slug": "backend-engineer",
        "sequence": 5,
        "question_type": "essay",
        "prompt": "Jelaskan strategi logging dan audit trail yang memastikan setiap rekomendasi bisa dilacak. Sertakan tools dan format log yang Anda rekomendasikan.",
        "options": None,
        "correct_answer": None,
        "answer_key": "Strategi harus mencakup: structured logging (JSON format), correlation ID untuk tracing, log levels yang tepat, retention policy, dan integrasi dengan monitoring tools.",
        "model_answer": "Implementasi audit trail menggunakan: 1) Structured logging dengan format JSON untuk easy parsing. 2) Correlation ID (trace_id) di setiap request untuk end-to-end tracing. 3) Log levels: DEBUG untuk development, INFO untuk production events, WARNING untuk anomali, ERROR untuk failures. 4) Fields wajib: timestamp, trace_id, user_id, action, resource, result. 5) Tools: structlog untuk Python, ELK Stack atau Grafana Loki untuk aggregation. 6) Retention: 90 hari untuk compliance.",
        "rubric": {
            "strategy": {"weight": 0.3, "description": "Strategi logging yang komprehensif"},
            "tools": {"weight": 0.25, "description": "Pemilihan tools yang tepat"},
            "implementation": {"weight": 0.25, "description": "Detail implementasi yang jelas"},
            "compliance": {"weight": 0.2, "description": "Pertimbangan compliance dan retention"},
        },
        "difficulty": "medium",
        "weight": 1.0,
        "metadata": {"dimension": "observability", "topic": "logging"},
    },
    {
        "role_slug": "backend-engineer",
        "sequence": 6,
        "question_type": "essay",
        "prompt": "Bagaimana strategi fallback ketika GPT API atau vector store mengalami downtime, namun sistem harus tetap memberikan rekomendasi?",
        "options": None,
        "correct_answer": None,
        "answer_key": "Strategi fallback: circuit breaker pattern, cached recommendations, rule-based fallback, graceful degradation dengan clear messaging ke user.",
        "model_answer": "Strategi fallback multi-layer: 1) Circuit Breaker: setelah N failures, stop calling GPT dan switch ke fallback. 2) Cached Recommendations: simpan top courses per track di Redis, serve dari cache jika GPT down. 3) Rule-based Fallback: gunakan TF-IDF matching sederhana untuk rekomendasi basic. 4) Graceful Degradation: inform user bahwa rekomendasi mungkin kurang personalized. 5) Health checks dan auto-recovery ketika service available lagi.",
        "rubric": {
            "fallback_strategy": {"weight": 0.35, "description": "Strategi fallback yang komprehensif"},
            "resilience": {"weight": 0.25, "description": "Pola resilience (circuit breaker, retry)"},
            "user_experience": {"weight": 0.2, "description": "UX saat degraded mode"},
            "recovery": {"weight": 0.2, "description": "Strategi recovery otomatis"},
        },
        "difficulty": "hard",
        "weight": 1.5,
        "metadata": {"dimension": "resilience", "topic": "fallback"},
    },
    # === PROFILE - 4 soal ===
    {
        "role_slug": "backend-engineer",
        "sequence": 7,
        "question_type": "profile",
        "prompt": "Berapa tahun pengalaman Anda bekerja dengan Python untuk backend development?",
        "options": [
            {"id": "A", "text": "Belum pernah / < 6 bulan"},
            {"id": "B", "text": "6 bulan - 1 tahun"},
            {"id": "C", "text": "1-2 tahun"},
            {"id": "D", "text": "2-5 tahun"},
            {"id": "E", "text": "> 5 tahun"},
        ],
        "correct_answer": None,
        "expected_values": {
            "scoring": {
                "A": 20, "B": 40, "C": 60, "D": 80, "E": 100
            }
        },
        "difficulty": "easy",
        "weight": 1.0,
        "metadata": {"dimension": "experience", "topic": "python"},
    },
    {
        "role_slug": "backend-engineer",
        "sequence": 8,
        "question_type": "profile",
        "prompt": "Seberapa familiar Anda dengan Redis atau message queue sejenis (RabbitMQ, Kafka)?",
        "options": [
            {"id": "A", "text": "Belum pernah menggunakan"},
            {"id": "B", "text": "Pernah belajar/tutorial"},
            {"id": "C", "text": "Pernah menggunakan di project kecil"},
            {"id": "D", "text": "Menggunakan secara rutin di production"},
            {"id": "E", "text": "Expert, bisa setup dan optimize sendiri"},
        ],
        "correct_answer": None,
        "expected_values": {
            "scoring": {
                "A": 20, "B": 40, "C": 60, "D": 80, "E": 100
            }
        },
        "difficulty": "easy",
        "weight": 1.0,
        "metadata": {"dimension": "experience", "topic": "redis"},
    },
    {
        "role_slug": "backend-engineer",
        "sequence": 9,
        "question_type": "profile",
        "prompt": "Framework backend apa yang paling sering Anda gunakan?",
        "options": [
            {"id": "A", "text": "FastAPI"},
            {"id": "B", "text": "Django"},
            {"id": "C", "text": "Flask"},
            {"id": "D", "text": "Express.js (Node.js)"},
            {"id": "E", "text": "Lainnya / Belum pernah"},
        ],
        "correct_answer": None,
        "expected_values": {
            "scoring": {
                "A": 100, "B": 80, "C": 70, "D": 60, "E": 40
            },
            "preferred": ["A", "B"]
        },
        "difficulty": "easy",
        "weight": 1.0,
        "metadata": {"dimension": "experience", "topic": "framework"},
    },
    {
        "role_slug": "backend-engineer",
        "sequence": 10,
        "question_type": "profile",
        "prompt": "Apakah Anda memiliki pengalaman dengan containerization (Docker/Kubernetes)?",
        "options": [
            {"id": "A", "text": "Belum pernah"},
            {"id": "B", "text": "Hanya Docker untuk local development"},
            {"id": "C", "text": "Docker + Docker Compose"},
            {"id": "D", "text": "Docker + Kubernetes basics"},
            {"id": "E", "text": "Production Kubernetes experience"},
        ],
        "correct_answer": None,
        "expected_values": {
            "scoring": {
                "A": 20, "B": 40, "C": 60, "D": 80, "E": 100
            }
        },
        "difficulty": "easy",
        "weight": 1.0,
        "metadata": {"dimension": "experience", "topic": "devops"},
    },
]


def main():
    print(f"🔐 Logging in as {ADMIN_EMAIL}...")
    token = get_admin_token()
    print("✅ Login successful!")
    
    print("\n🗑️ Deleting existing backend-engineer questions...")
    delete_questions_by_track(token, "backend-engineer")
    
    print("\n📝 Creating new questions...")
    for q in BACKEND_QUESTIONS:
        result = create_question(token, q)
        if "exists" not in result:
            print(f"  ✅ Created: {q['prompt'][:50]}...")
    
    print("\n🎉 Done! Questions seeded successfully.")
    print("\nSummary:")
    print(f"  - Theoretical (pilihan ganda): 3 soal")
    print(f"  - Essay: 3 soal")
    print(f"  - Profile: 4 soal")
    print(f"  - Total: 10 soal")


if __name__ == "__main__":
    main()
