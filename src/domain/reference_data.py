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

ESSAY_RUBRICS: dict[str, dict[str, object]] = {
    "easy": {
        "dimensions": {
            "relevance": 0.3,
            "clarity": 0.25,
            "completeness": 0.25,
            "depth": 0.1,
            "technical": 0.1,
        },
        "floor": 10,
        "ceiling": 95,
    },
    "medium": {
        "dimensions": {
            "relevance": 0.25,
            "clarity": 0.2,
            "completeness": 0.2,
            "depth": 0.2,
            "technical": 0.15,
        },
        "floor": 5,
        "ceiling": 95,
    },
    "hard": {
        "dimensions": {
            "relevance": 0.2,
            "clarity": 0.15,
            "completeness": 0.15,
            "depth": 0.25,
            "technical": 0.25,
        },
        "floor": 0,
        "ceiling": 95,
    },
}


def make_question(
    role_slug: str,
    sequence: int,
    qtype: str,
    prompt: str,
    dimension: str,
    *,
    difficulty: str = "medium",
    weight: float = 1.0,
    correct_answer: str | None = None,
    answer_key: str | None = None,
    model_answer: str | None = None,
    rubric: dict | None = None,
    expected_values: dict | None = None,
) -> dict[str, object]:
    return {
        "role_slug": role_slug,
        "sequence": sequence,
        "question_type": qtype,
        "prompt": prompt,
        "difficulty": difficulty,
        "weight": weight,
        "correct_answer": correct_answer,
        "answer_key": answer_key,
        "model_answer": model_answer,
        "rubric": rubric,
        "expected_values": expected_values,
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
        difficulty="easy",
        weight=1.0,
        correct_answer="A",
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
        difficulty="medium",
        weight=1.2,
        correct_answer="A",
    ),
    make_question(
        "backend-engineer",
        3,
        "theoretical",
        "Jelaskan konsep caching dan sebutkan 3 strategi caching yang umum digunakan.",
        "performance",
        difficulty="hard",
        weight=1.5,
        correct_answer="A",
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
        difficulty="easy",
        weight=1.0,
        answer_key=(
            "Buat CRUD endpoints dengan validasi body, status code tepat, dan error handling. "
            "Gunakan method GET/POST/PUT/DELETE, cek not-found, dan kembalikan JSON."
        ),
        model_answer=(
            "Buat CRUD endpoints dengan validasi body, status code tepat, dan error handling. "
            "Gunakan method GET/POST/PUT/DELETE, cek not-found, dan kembalikan JSON."
        ),
        rubric=ESSAY_RUBRICS["easy"],
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
        difficulty="medium",
        weight=1.2,
        answer_key=(
            "Gunakan regex/validator email dan tulis unit test untuk valid, invalid, kosong, null, "
            "serta karakter khusus. Pastikan assert hasil True/False sesuai kasus."
        ),
        model_answer=(
            "Gunakan regex/validator email dan tulis unit test untuk valid, invalid, kosong, null, "
            "serta karakter khusus. Pastikan assert hasil True/False sesuai kasus."
        ),
        rubric=ESSAY_RUBRICS["medium"],
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
        difficulty="hard",
        weight=1.5,
        answer_key=(
            "Relasi: Users 1-N Orders, Orders 1-N OrderItems, OrderItems N-1 Products. "
            "Sertakan kunci asing, tipe data utama, dan index pada FK serta lookup umum."
        ),
        model_answer=(
            "Relasi: Users 1-N Orders, Orders 1-N OrderItems, OrderItems N-1 Products. "
            "Sertakan kunci asing, tipe data utama, dan index pada FK serta lookup umum."
        ),
        rubric=ESSAY_RUBRICS["hard"],
    ),
    make_question(
        "backend-engineer",
        7,
        "profile",
        "Berapa tahun pengalaman Anda sebagai Backend Engineer?",
        "experience",
        expected_values={"accepted_values": ["<1", "1-3", "3-5", "5+"]},
    ),
    make_question(
        "backend-engineer",
        8,
        "profile",
        "Framework dan bahasa pemrograman apa yang paling sering Anda gunakan?",
        "tech-stack",
        expected_values={"accepted_values": ["node", "python", "go", "java", "ruby"]},
    ),
    make_question(
        "backend-engineer",
        9,
        "profile",
        "Apakah Anda pernah deploy aplikasi ke production? Jelaskan platform yang digunakan.",
        "deployment",
        expected_values={"accepted_values": ["aws", "gcp", "azure", "render", "docker"]},
    ),
    make_question(
        "backend-engineer",
        10,
        "profile",
        "Ceritakan tantangan teknis terbesar yang pernah Anda hadapi dan bagaimana solusinya.",
        "problem-solving",
        expected_values={"accepted_values": ["outage", "scaling", "migration", "refactor"]},
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
        difficulty="easy",
        weight=1.0,
        correct_answer="A",
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
        difficulty="medium",
        weight=1.2,
        correct_answer="A",
    ),
    make_question(
        "data-analyst",
        3,
        "theoretical",
        "Jelaskan konsep data cleaning dan mengapa ini penting dalam analisis data.",
        "data-quality",
        difficulty="hard",
        weight=1.5,
        correct_answer="A",
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
        difficulty="easy",
        weight=1.0,
        answer_key=(
            "Gunakan JOIN dengan kategori, GROUP BY kategori dan produk. Hitung SUM(revenue), "
            "SUM(quantity), AVG(price), lalu urutkan top 5 revenue."
        ),
        model_answer=(
            "Gunakan JOIN dengan kategori, GROUP BY kategori dan produk. Hitung SUM(revenue), "
            "SUM(quantity), AVG(price), lalu urutkan top 5 revenue."
        ),
        rubric=ESSAY_RUBRICS["easy"],
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
        difficulty="medium",
        weight=1.2,
        answer_key=(
            "Langkah EDA: cek missing/outlier, distribusi, korelasi, segmentasi. "
            "Visual: histogram, boxplot, scatter, bar per segmen, korelasi heatmap."
        ),
        model_answer=(
            "Langkah EDA: cek missing/outlier, distribusi, korelasi, segmentasi. "
            "Visual: histogram, boxplot, scatter, bar per segmen, korelasi heatmap."
        ),
        rubric=ESSAY_RUBRICS["medium"],
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
        difficulty="hard",
        weight=1.5,
        answer_key=(
            "Ringkas insight: traffic naik, conversion turun, bounce naik. "
            "Jelaskan kemungkinan penyebab dan rekomendasi aksi perbaikan funnel."
        ),
        model_answer=(
            "Ringkas insight: traffic naik, conversion turun, bounce naik. "
            "Jelaskan kemungkinan penyebab dan rekomendasi aksi perbaikan funnel."
        ),
        rubric=ESSAY_RUBRICS["hard"],
    ),
    make_question(
        "data-analyst",
        7,
        "profile",
        "Berapa tahun pengalaman Anda sebagai Data Analyst?",
        "experience",
        expected_values={"accepted_values": ["<1", "1-3", "3-5", "5+"]},
    ),
    make_question(
        "data-analyst",
        8,
        "profile",
        "Tools apa yang Anda kuasai untuk analisis data? (contoh: Excel, SQL, Python, Tableau)",
        "tools",
        expected_values={"accepted_values": ["excel", "sql", "python", "tableau", "power bi"]},
    ),
    make_question(
        "data-analyst",
        9,
        "profile",
        "Apakah Anda pernah membuat dashboard atau report untuk stakeholders? Jelaskan singkat.",
        "reporting",
        expected_values={"accepted_values": ["yes", "no", "dashboard", "report"]},
    ),
    make_question(
        "data-analyst",
        10,
        "profile",
        "Ceritakan project analisis data yang paling berkesan dan dampaknya bagi bisnis.",
        "impact",
    ),
]
