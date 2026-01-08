#!/usr/bin/env python3
"""
Script untuk seed soal dengan format baru:
- Theoretical: pilihan ganda (A, B, C, D) dengan kunci jawaban
- Essay: dengan rubric untuk GPT scoring
- Profile: 4 soal profil

Jalankan dengan:
    poetry run python scripts/seed_questions.py
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncio
import os

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.infrastructure.db.models import QuestionTemplate, QuestionType

# Questions for Backend Engineer track
BACKEND_QUESTIONS = [
    # === THEORETICAL (Pilihan Ganda) - 3 soal ===
    {
        "role_slug": "backend-engineer",
        "sequence": 1,
        "question_type": QuestionType.THEORETICAL,
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
        "metadata_": {"dimension": "framework-knowledge", "topic": "fastapi"},
    },
    {
        "role_slug": "backend-engineer",
        "sequence": 2,
        "question_type": QuestionType.THEORETICAL,
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
        "metadata_": {"dimension": "api-design", "topic": "rest"},
    },
    {
        "role_slug": "backend-engineer",
        "sequence": 3,
        "question_type": QuestionType.THEORETICAL,
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
        "metadata_": {"dimension": "infrastructure", "topic": "redis"},
    },
    # === ESSAY - 3 soal ===
    {
        "role_slug": "backend-engineer",
        "sequence": 4,
        "question_type": QuestionType.ESSAY,
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
        "metadata_": {"dimension": "system-design", "topic": "architecture"},
    },
    {
        "role_slug": "backend-engineer",
        "sequence": 5,
        "question_type": QuestionType.ESSAY,
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
        "metadata_": {"dimension": "observability", "topic": "logging"},
    },
    {
        "role_slug": "backend-engineer",
        "sequence": 6,
        "question_type": QuestionType.ESSAY,
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
        "metadata_": {"dimension": "resilience", "topic": "fallback"},
    },
    # === PROFILE - 4 soal ===
    {
        "role_slug": "backend-engineer",
        "sequence": 7,
        "question_type": QuestionType.PROFILE,
        "prompt": "Berapa tahun pengalaman Anda bekerja dengan Python untuk backend development?",
        "options": [
            {"id": "A", "text": "Belum pernah / < 6 bulan"},
            {"id": "B", "text": "6 bulan - 1 tahun"},
            {"id": "C", "text": "1-2 tahun"},
            {"id": "D", "text": "2-5 tahun"},
            {"id": "E", "text": "> 5 tahun"},
        ],
        "correct_answer": None,  # Profile tidak ada jawaban benar
        "expected_values": {
            "scoring": {
                "A": 20, "B": 40, "C": 60, "D": 80, "E": 100
            }
        },
        "difficulty": "easy",
        "weight": 1.0,
        "metadata_": {"dimension": "experience", "topic": "python"},
    },
    {
        "role_slug": "backend-engineer",
        "sequence": 8,
        "question_type": QuestionType.PROFILE,
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
        "metadata_": {"dimension": "experience", "topic": "redis"},
    },
    {
        "role_slug": "backend-engineer",
        "sequence": 9,
        "question_type": QuestionType.PROFILE,
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
            "preferred": ["A", "B"]  # FastAPI dan Django lebih relevan
        },
        "difficulty": "easy",
        "weight": 1.0,
        "metadata_": {"dimension": "experience", "topic": "framework"},
    },
    {
        "role_slug": "backend-engineer",
        "sequence": 10,
        "question_type": QuestionType.PROFILE,
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
        "metadata_": {"dimension": "experience", "topic": "devops"},
    },
]

# Questions for Data Analyst track
DATA_ANALYST_QUESTIONS = [
    # === THEORETICAL (Pilihan Ganda) - 3 soal ===
    {
        "role_slug": "data-analyst",
        "sequence": 1,
        "question_type": QuestionType.THEORETICAL,
        "prompt": "Apa perbedaan utama antara SQL JOIN dan UNION?",
        "options": [
            {"id": "A", "text": "JOIN menggabungkan kolom dari tabel berbeda, UNION menggabungkan baris"},
            {"id": "B", "text": "JOIN dan UNION melakukan hal yang sama"},
            {"id": "C", "text": "UNION lebih cepat dari JOIN"},
            {"id": "D", "text": "JOIN hanya untuk tabel yang sama"},
        ],
        "correct_answer": "A",
        "difficulty": "easy",
        "weight": 1.0,
        "metadata_": {"dimension": "sql", "topic": "joins"},
    },
    {
        "role_slug": "data-analyst",
        "sequence": 2,
        "question_type": QuestionType.THEORETICAL,
        "prompt": "Metrik mana yang paling tepat untuk mengukur central tendency data dengan outliers?",
        "options": [
            {"id": "A", "text": "Mean (rata-rata)"},
            {"id": "B", "text": "Median"},
            {"id": "C", "text": "Mode"},
            {"id": "D", "text": "Standard Deviation"},
        ],
        "correct_answer": "B",
        "difficulty": "medium",
        "weight": 1.0,
        "metadata_": {"dimension": "statistics", "topic": "central-tendency"},
    },
    {
        "role_slug": "data-analyst",
        "sequence": 3,
        "question_type": QuestionType.THEORETICAL,
        "prompt": "Apa kegunaan utama dari window function dalam SQL?",
        "options": [
            {"id": "A", "text": "Menghapus data duplikat"},
            {"id": "B", "text": "Melakukan kalkulasi across rows tanpa grouping"},
            {"id": "C", "text": "Membuat tabel baru"},
            {"id": "D", "text": "Mengubah tipe data"},
        ],
        "correct_answer": "B",
        "difficulty": "medium",
        "weight": 1.0,
        "metadata_": {"dimension": "sql", "topic": "window-functions"},
    },
    # === ESSAY - 3 soal ===
    {
        "role_slug": "data-analyst",
        "sequence": 4,
        "question_type": QuestionType.ESSAY,
        "prompt": "Jelaskan proses end-to-end dalam membangun dashboard analytics untuk tracking user engagement. Sertakan data sources, metrics, dan tools yang Anda rekomendasikan.",
        "options": None,
        "correct_answer": None,
        "answer_key": "Proses meliputi: 1) Define KPIs (DAU, MAU, retention, churn), 2) Data collection (events, sessions), 3) ETL pipeline, 4) Data warehouse, 5) Visualization tools (Metabase, Tableau, Looker).",
        "model_answer": "Proses membangun dashboard: 1) Discovery: identifikasi stakeholder needs dan KPIs utama (DAU, session duration, feature adoption rate). 2) Data Collection: implement event tracking dengan tools seperti Segment atau custom events. 3) ETL: build pipeline menggunakan Airflow/dbt untuk transform raw events ke analytics-ready tables. 4) Storage: use data warehouse (BigQuery/Snowflake) dengan star schema. 5) Visualization: Metabase/Tableau dengan filters untuk segmentasi. 6) Maintenance: monitoring data quality dan refresh schedules.",
        "rubric": {
            "process": {"weight": 0.25, "description": "Proses end-to-end yang lengkap"},
            "metrics": {"weight": 0.25, "description": "KPIs yang relevan"},
            "tools": {"weight": 0.25, "description": "Pemilihan tools yang tepat"},
            "implementation": {"weight": 0.25, "description": "Detail implementasi"},
        },
        "difficulty": "hard",
        "weight": 1.5,
        "metadata_": {"dimension": "analytics", "topic": "dashboard"},
    },
    {
        "role_slug": "data-analyst",
        "sequence": 5,
        "question_type": QuestionType.ESSAY,
        "prompt": "Bagaimana Anda mendeteksi dan menangani data quality issues dalam dataset besar? Berikan contoh konkret.",
        "options": None,
        "correct_answer": None,
        "answer_key": "Strategi: profiling, validation rules, anomaly detection, data lineage tracking, automated alerts.",
        "model_answer": "Strategi data quality: 1) Profiling: gunakan Great Expectations atau pandas-profiling untuk initial assessment. 2) Validation Rules: null checks, range validation, referential integrity, format consistency. 3) Anomaly Detection: statistical methods (z-score) untuk outliers, time-series analysis untuk trend breaks. 4) Lineage Tracking: document data transformations. 5) Automated Alerts: setup threshold-based alerts untuk metrics drift. Contoh: deteksi sudden spike di conversion rate → investigate apakah tracking issue atau real change.",
        "rubric": {
            "detection": {"weight": 0.3, "description": "Metode deteksi yang komprehensif"},
            "handling": {"weight": 0.3, "description": "Strategi handling yang tepat"},
            "tools": {"weight": 0.2, "description": "Tools yang relevan"},
            "examples": {"weight": 0.2, "description": "Contoh konkret"},
        },
        "difficulty": "medium",
        "weight": 1.0,
        "metadata_": {"dimension": "data-quality", "topic": "validation"},
    },
    {
        "role_slug": "data-analyst",
        "sequence": 6,
        "question_type": QuestionType.ESSAY,
        "prompt": "Jelaskan bagaimana Anda akan mempresentasikan hasil analisis kepada stakeholder non-teknis. Sertakan tips storytelling dengan data.",
        "options": None,
        "correct_answer": None,
        "answer_key": "Tips: start with conclusion, use simple visualizations, avoid jargon, connect to business impact, provide actionable recommendations.",
        "model_answer": "Storytelling dengan data: 1) Start with Why: mulai dengan business question yang dijawab. 2) SCQA Framework: Situation → Complication → Question → Answer. 3) Visual Simplicity: gunakan chart yang familiar (bar, line), hindari 3D charts. 4) One Insight Per Slide: jangan overwhelm audience. 5) Business Language: translate metrics ke business impact (revenue, cost savings). 6) Call to Action: end dengan clear recommendations. 7) Anticipate Questions: prepare backup slides dengan detail. Example: 'User churn increased 15% → this costs us $50K/month → recommendation: implement retention campaign targeting at-risk users.'",
        "rubric": {
            "structure": {"weight": 0.25, "description": "Struktur presentasi yang jelas"},
            "visualization": {"weight": 0.25, "description": "Penggunaan visual yang efektif"},
            "communication": {"weight": 0.25, "description": "Kemampuan komunikasi non-teknis"},
            "actionability": {"weight": 0.25, "description": "Rekomendasi yang actionable"},
        },
        "difficulty": "medium",
        "weight": 1.0,
        "metadata_": {"dimension": "communication", "topic": "storytelling"},
    },
    # === PROFILE - 4 soal ===
    {
        "role_slug": "data-analyst",
        "sequence": 7,
        "question_type": QuestionType.PROFILE,
        "prompt": "Berapa tahun pengalaman Anda bekerja dengan SQL?",
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
        "metadata_": {"dimension": "experience", "topic": "sql"},
    },
    {
        "role_slug": "data-analyst",
        "sequence": 8,
        "question_type": QuestionType.PROFILE,
        "prompt": "Tools visualisasi apa yang paling sering Anda gunakan?",
        "options": [
            {"id": "A", "text": "Tableau"},
            {"id": "B", "text": "Power BI"},
            {"id": "C", "text": "Metabase / Looker"},
            {"id": "D", "text": "Python (Matplotlib/Plotly)"},
            {"id": "E", "text": "Excel / Google Sheets"},
        ],
        "correct_answer": None,
        "expected_values": {
            "scoring": {
                "A": 100, "B": 90, "C": 85, "D": 80, "E": 50
            }
        },
        "difficulty": "easy",
        "weight": 1.0,
        "metadata_": {"dimension": "experience", "topic": "visualization"},
    },
    {
        "role_slug": "data-analyst",
        "sequence": 9,
        "question_type": QuestionType.PROFILE,
        "prompt": "Seberapa familiar Anda dengan Python untuk data analysis?",
        "options": [
            {"id": "A", "text": "Belum pernah menggunakan"},
            {"id": "B", "text": "Basic (pandas, numpy)"},
            {"id": "C", "text": "Intermediate (seaborn, scikit-learn basics)"},
            {"id": "D", "text": "Advanced (ML, statistical analysis)"},
            {"id": "E", "text": "Expert (can build production pipelines)"},
        ],
        "correct_answer": None,
        "expected_values": {
            "scoring": {
                "A": 20, "B": 50, "C": 70, "D": 90, "E": 100
            }
        },
        "difficulty": "easy",
        "weight": 1.0,
        "metadata_": {"dimension": "experience", "topic": "python"},
    },
    {
        "role_slug": "data-analyst",
        "sequence": 10,
        "question_type": QuestionType.PROFILE,
        "prompt": "Apakah Anda memiliki pengalaman dengan cloud data platforms?",
        "options": [
            {"id": "A", "text": "Belum pernah"},
            {"id": "B", "text": "BigQuery (Google Cloud)"},
            {"id": "C", "text": "Redshift (AWS)"},
            {"id": "D", "text": "Snowflake"},
            {"id": "E", "text": "Multiple platforms"},
        ],
        "correct_answer": None,
        "expected_values": {
            "scoring": {
                "A": 30, "B": 80, "C": 80, "D": 85, "E": 100
            }
        },
        "difficulty": "easy",
        "weight": 1.0,
        "metadata_": {"dimension": "experience", "topic": "cloud"},
    },
]


async def seed_questions():
    """Seed questions to database."""
    database_url = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://microcred:postgres-password@localhost:5432/microcred"
    )

    # Create async engine
    engine = create_async_engine(database_url, echo=True)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # Delete existing questions for these tracks
        for track in ["backend-engineer", "data-analyst"]:
            await session.execute(
                delete(QuestionTemplate).where(QuestionTemplate.role_slug == track)
            )
        await session.commit()

        # Insert new questions
        all_questions = BACKEND_QUESTIONS + DATA_ANALYST_QUESTIONS

        for q in all_questions:
            question = QuestionTemplate(
                role_slug=q["role_slug"],
                sequence=q["sequence"],
                question_type=q["question_type"],
                prompt=q["prompt"],
                options=q.get("options"),
                correct_answer=q.get("correct_answer"),
                answer_key=q.get("answer_key"),
                model_answer=q.get("model_answer"),
                rubric=q.get("rubric"),
                expected_values=q.get("expected_values"),
                difficulty=q.get("difficulty", "medium"),
                weight=q.get("weight", 1.0),
                metadata_=q.get("metadata_"),
                version=1,
                is_active=True,
            )
            session.add(question)

        await session.commit()
        print(f"✅ Seeded {len(all_questions)} questions successfully!")

        # Verify
        result = await session.execute(
            select(QuestionTemplate).where(QuestionTemplate.is_active == True)
        )
        questions = result.scalars().all()
        print(f"\n📊 Summary:")
        for track in ["backend-engineer", "data-analyst"]:
            track_qs = [q for q in questions if q.role_slug == track]
            theoretical = len([q for q in track_qs if q.question_type == QuestionType.THEORETICAL])
            essay = len([q for q in track_qs if q.question_type == QuestionType.ESSAY])
            profile = len([q for q in track_qs if q.question_type == QuestionType.PROFILE])
            print(f"  {track}: {theoretical} theoretical, {essay} essay, {profile} profile")


if __name__ == "__main__":
    asyncio.run(seed_questions())
