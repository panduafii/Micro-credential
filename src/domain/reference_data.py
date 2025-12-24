from __future__ import annotations

ROLE_DEFINITIONS = [
    {
        "slug": "backend-engineer",
        "name": "Backend Engineer",
        "description": "Async-first service work: queue orchestration, scoring, dan rekomendasi.",
    },
    {
        "slug": "data-analyst",
        "name": "Data Analyst",
        "description": "Analytics dan transparency focus untuk rekomendasi micro-credential.",
    },
]


def make_question(role_slug: str, sequence: int, qtype: str, prompt: str, dimension: str) -> dict[str, object]:
    return {
        "role_slug": role_slug,
        "sequence": sequence,
        "question_type": qtype,
        "prompt": prompt,
        "metadata": {"dimension": dimension},
    }


QUESTION_TEMPLATES = [
    make_question(
        "backend-engineer",
        1,
        "theoretical",
        "Jelaskan perbedaan utama antara FastAPI async dengan framework synchronous untuk API backend berbeban tinggi.",
        "architecture",
    ),
    make_question(
        "backend-engineer",
        2,
        "theoretical",
        "Apa arti idempotensi pada endpoint submit assessment dan bagaimana cara menjaganya ketika job async digunakan?",
        "reliability",
    ),
    make_question(
        "backend-engineer",
        3,
        "theoretical",
        "Bandingkan modular monolith vs microservice untuk MVP empat minggu yang mengandalkan RAG dan GPT workers.",
        "tradeoff",
    ),
    make_question(
        "backend-engineer",
        4,
        "essay",
        "Rancang alur scoring hybrid (rule + GPT) agar SLA <10 detik tercapai. Jelaskan komponen utama dan komunikasi antar komponen.",
        "system-design",
    ),
    make_question(
        "backend-engineer",
        5,
        "essay",
        "Platform memiliki requirement audit trail. Jelaskan pendekatan logging dan storage yang memastikan jejak rekomendasi bisa dilacak.",
        "observability",
    ),
    make_question(
        "backend-engineer",
        6,
        "essay",
        "Bagaimana strategi fallback ketika GPT atau vector store gagal namun hasil rekomendasi harus tetap diberikan?",
        "resilience",
    ),
    make_question(
        "backend-engineer",
        7,
        "profile",
        "Berapa pengalaman Anda bekerja dengan Redis atau message queue sejenis?",
        "experience",
    ),
    make_question(
        "backend-engineer",
        8,
        "profile",
        "Tumpukan teknologi apa yang paling familiar untuk menjalankan FastAPI di produksi?",
        "stack",
    ),
    make_question(
        "backend-engineer",
        9,
        "profile",
        "Apa prioritas utama Anda: throughput, cost, atau transparansi?",
        "priority",
    ),
    make_question(
        "backend-engineer",
        10,
        "profile",
        "Sebutkan satu tantangan terbesar saat mengoperasikan layanan async sebelumnya.",
        "pain-point",
    ),
    make_question(
        "data-analyst",
        1,
        "theoretical",
        "Apa arti explainability dalam konteks rekomendasi micro-credential dan bagaimana cara mengukurnya?",
        "explainability",
    ),
    make_question(
        "data-analyst",
        2,
        "theoretical",
        "Mengapa latency penting untuk trust advisor dan bagaimana cara memvisualisasikan SLA di dashboard?",
        "observability",
    ),
    make_question(
        "data-analyst",
        3,
        "theoretical",
        "Bandingkan teknik RAG zero-shot vs RAG berbasis taxonomy untuk katalog micro-credential.",
        "rag",
    ),
    make_question(
        "data-analyst",
        4,
        "essay",
        "Deskripsikan dataset minimal yang dibutuhkan untuk memvalidasi skor rekomendasi serta bagaimana Anda menilai kualitasnya.",
        "dataset",
    ),
    make_question(
        "data-analyst",
        5,
        "essay",
        "Bagaimana memetakan feedback advisor/students menjadi sinyal yang siap dipakai tuning model rekomendasi?",
        "feedback",
    ),
    make_question(
        "data-analyst",
        6,
        "essay",
        "Tulis contoh ringkasan naratif hasil assessment yang transparan dan mudah dipahami bagi mahasiswa.",
        "storytelling",
    ),
    make_question(
        "data-analyst",
        7,
        "profile",
        "Apa pengalaman Anda dengan BI tools atau observability stack?",
        "experience",
    ),
    make_question(
        "data-analyst",
        8,
        "profile",
        "Sebutkan bahasa pemrograman favorit untuk analisis data dan alasannya.",
        "tooling",
    ),
    make_question(
        "data-analyst",
        9,
        "profile",
        "Apa KPI utama yang Anda prioritaskan untuk pilot micro-credential ini?",
        "priority",
    ),
    make_question(
        "data-analyst",
        10,
        "profile",
        "Bagikan cerita singkat saat Anda harus menjelaskan hasil AI ke stakeholder non-teknis.",
        "communication",
    ),
]
