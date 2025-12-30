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


def make_question(
    role_slug: str, sequence: int, qtype: str, prompt: str, dimension: str
) -> dict[str, object]:
    return {
        "role_slug": role_slug,
        "sequence": sequence,
        "question_type": qtype,
        "prompt": prompt,
        "metadata": {"dimension": dimension},
    }


QUESTION_TEMPLATES = [
    # Backend Engineer Questions
    make_question(
        "backend-engineer",
        1,
        "theoretical",
        (
            "Jelaskan perbedaan antara REST API dan GraphQL. "
            "Kapan sebaiknya menggunakan masing-masing?"
        ),
        "api-design",
    ),
    make_question(
        "backend-engineer",
        2,
        "theoretical",
        (
            "Apa yang dimaksud dengan database indexing? "
            "Bagaimana cara menentukan kolom mana yang perlu di-index?"
        ),
        "database",
    ),
    make_question(
        "backend-engineer",
        3,
        "theoretical",
        "Jelaskan konsep caching dan sebutkan 3 strategi caching yang umum digunakan.",
        "performance",
    ),
    make_question(
        "backend-engineer",
        4,
        "essay",
        (
            "Implementasikan REST API endpoint untuk CRUD operations pada resource 'products'. "
            "Endpoint harus include: GET /products (list), POST /products (create), "
            "PUT /products/:id (update), DELETE /products/:id (delete). "
            "Tulis kode dengan validasi input dan error handling."
        ),
        "api-implementation",
    ),
    make_question(
        "backend-engineer",
        5,
        "essay",
        (
            "Tulis unit test untuk fungsi yang memvalidasi email format. "
            "Test harus cover: valid email, invalid format, empty string, "
            "null value, dan email dengan special characters."
        ),
        "testing",
    ),
    make_question(
        "backend-engineer",
        6,
        "essay",
        (
            "Desain database schema untuk aplikasi e-commerce sederhana "
            "dengan entitas: Users, Products, Orders, dan Order Items. "
            "Jelaskan relasi antar tabel dan field yang diperlukan."
        ),
        "database-design",
    ),
    make_question(
        "backend-engineer",
        7,
        "profile",
        "Berapa tahun pengalaman Anda sebagai Backend Engineer?",
        "experience",
    ),
    make_question(
        "backend-engineer",
        8,
        "profile",
        "Framework dan bahasa pemrograman apa yang paling sering Anda gunakan?",
        "tech-stack",
    ),
    make_question(
        "backend-engineer",
        9,
        "profile",
        "Apakah Anda pernah deploy aplikasi ke production? Jelaskan platform yang digunakan.",
        "deployment",
    ),
    make_question(
        "backend-engineer",
        10,
        "profile",
        "Ceritakan tantangan teknis terbesar yang pernah Anda hadapi dan bagaimana solusinya.",
        "problem-solving",
    ),
    # Data Analyst Questions
    make_question(
        "data-analyst",
        1,
        "theoretical",
        (
            "Jelaskan perbedaan antara mean, median, dan mode. "
            "Kapan sebaiknya menggunakan masing-masing ukuran central tendency?"
        ),
        "statistics",
    ),
    make_question(
        "data-analyst",
        2,
        "theoretical",
        (
            "Apa yang dimaksud dengan data visualization best practices? "
            "Sebutkan 3 prinsip penting dalam membuat visualisasi data yang efektif."
        ),
        "visualization",
    ),
    make_question(
        "data-analyst",
        3,
        "theoretical",
        "Jelaskan konsep data cleaning dan mengapa ini penting dalam analisis data.",
        "data-quality",
    ),
    make_question(
        "data-analyst",
        4,
        "essay",
        (
            "Tulis SQL query untuk menganalisis sales data: "
            "Tampilkan top 5 products berdasarkan total revenue, "
            "join dengan category info, dan group by category. "
            "Include total quantity sold dan average price per product."
        ),
        "sql-analysis",
    ),
    make_question(
        "data-analyst",
        5,
        "essay",
        (
            "Diberikan dataset customer dengan kolom: age, gender, income, purchase_amount. "
            "Jelaskan langkah-langkah untuk melakukan exploratory data analysis (EDA). "
            "Apa saja visualisasi yang akan Anda buat dan insight apa yang dicari?"
        ),
        "eda",
    ),
    make_question(
        "data-analyst",
        6,
        "essay",
        (
            "Buatlah executive summary dari hasil analisis: "
            "Website traffic meningkat 30% bulan ini, tapi conversion rate turun 15%. "
            "Bounce rate naik 20%. Jelaskan insight dan rekomendasi aksi dalam 150 kata."
        ),
        "insight-communication",
    ),
    make_question(
        "data-analyst",
        7,
        "profile",
        "Berapa tahun pengalaman Anda sebagai Data Analyst?",
        "experience",
    ),
    make_question(
        "data-analyst",
        8,
        "profile",
        "Tools apa yang Anda kuasai untuk analisis data? (contoh: Excel, SQL, Python, Tableau)",
        "tools",
    ),
    make_question(
        "data-analyst",
        9,
        "profile",
        "Apakah Anda pernah membuat dashboard atau report untuk stakeholders? Jelaskan singkat.",
        "reporting",
    ),
    make_question(
        "data-analyst",
        10,
        "profile",
        "Ceritakan project analisis data yang paling berkesan dan dampaknya bagi bisnis.",
        "impact",
    ),
]
