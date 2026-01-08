#!/usr/bin/env python3
"""
Script untuk seed soal via API endpoint (untuk production).

Soal dirancang untuk mahasiswa IT semester 1-2 dengan tingkat kesulitan bertahap.

Jalankan dengan:
    export API_URL=https://microcred-api.onrender.com
    export ADMIN_EMAIL=admin@microcred.com
    export ADMIN_PASSWORD=SecurePass123!
    poetry run python scripts/seed_questions_api.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

# REQUIRED: Add parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

import requests

API_URL = os.getenv("API_URL", "https://microcred-api.onrender.com")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@microcred.com")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "SecurePass123!")


def get_admin_token() -> str:
    """Login and get admin token."""
    resp = requests.post(
        f"{API_URL}/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["tokens"]["access_token"]


def create_question(token: str, question: dict[str, Any]) -> dict[str, Any]:
    """Create a question via API."""
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.post(
        f"{API_URL}/questions",
        json=question,
        headers=headers,
        timeout=30,
    )
    if resp.status_code == 409:
        prompt_preview = question["prompt"][:40]
        print(f"  ⚠️ Question exists: {prompt_preview}...")
        return {"exists": True}
    resp.raise_for_status()
    return resp.json()


def delete_questions_by_track(token: str, role_slug: str) -> None:
    """Delete all questions for a track."""
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(
        f"{API_URL}/questions?role_slug={role_slug}",
        headers=headers,
        timeout=30,
    )
    resp.raise_for_status()
    questions = resp.json()

    for q in questions:
        q_id = q["id"]
        del_resp = requests.delete(
            f"{API_URL}/questions/{q_id}",
            headers=headers,
            timeout=30,
        )
        if del_resp.status_code == 204:
            print(f"  🗑️ Deleted question {q_id}")


# ============================================================================
# BACKEND ENGINEER QUESTIONS (Semester 1-2 IT Students)
# ============================================================================
BACKEND_QUESTIONS = [
    # === THEORETICAL (Pilihan Ganda) ===
    # Soal 1: MUDAH
    {
        "role_slug": "backend-engineer",
        "sequence": 1,
        "question_type": "theoretical",
        "prompt": "Apa kepanjangan dari API?",
        "options": [
            {"id": "A", "text": "Application Programming Interface"},
            {"id": "B", "text": "Advanced Programming Integration"},
            {"id": "C", "text": "Automatic Program Installation"},
            {"id": "D", "text": "Application Process Integration"},
        ],
        "correct_answer": "A",
        "difficulty": "easy",
        "weight": 1.0,
        "metadata": {"dimension": "fundamentals", "topic": "api-basics"},
    },
    # Soal 2: SEDANG
    {
        "role_slug": "backend-engineer",
        "sequence": 2,
        "question_type": "theoretical",
        "prompt": "HTTP method mana yang digunakan untuk mengambil data dari server?",
        "options": [
            {"id": "A", "text": "POST"},
            {"id": "B", "text": "GET"},
            {"id": "C", "text": "DELETE"},
            {"id": "D", "text": "PUT"},
        ],
        "correct_answer": "B",
        "difficulty": "medium",
        "weight": 1.0,
        "metadata": {"dimension": "http", "topic": "methods"},
    },
    # Soal 3: AGAK SUSAH
    {
        "role_slug": "backend-engineer",
        "sequence": 3,
        "question_type": "theoretical",
        "prompt": "Apa perbedaan utama antara SQL dan NoSQL database?",
        "options": [
            {"id": "A", "text": "SQL lebih cepat dari NoSQL"},
            {"id": "B", "text": "SQL menggunakan struktur tabel relasional, NoSQL fleksibel"},
            {"id": "C", "text": "NoSQL tidak bisa menyimpan data"},
            {"id": "D", "text": "SQL hanya untuk website, NoSQL untuk mobile"},
        ],
        "correct_answer": "B",
        "difficulty": "hard",
        "weight": 1.0,
        "metadata": {"dimension": "database", "topic": "sql-nosql"},
    },
    # === ESSAY (Teknis) ===
    # Soal 4: MUDAH
    {
        "role_slug": "backend-engineer",
        "sequence": 4,
        "question_type": "essay",
        "prompt": (
            "Jelaskan apa itu REST API dan berikan contoh penggunaannya "
            "dalam aplikasi sehari-hari!"
        ),
        "options": None,
        "correct_answer": None,
        "answer_key": (
            "REST API adalah arsitektur untuk komunikasi antar sistem via HTTP. "
            "Contoh: aplikasi cuaca mengambil data dari server, login sosial media."
        ),
        "model_answer": (
            "REST (Representational State Transfer) API adalah arsitektur yang "
            "memungkinkan komunikasi antara client dan server menggunakan protokol "
            "HTTP. Contoh penggunaan: 1) Aplikasi cuaca di HP mengambil data dari "
            "server cuaca, 2) Login dengan Google/Facebook di aplikasi lain, "
            "3) Aplikasi e-commerce menampilkan produk dari database server."
        ),
        "rubric": {
            "understanding": {"weight": 0.4, "description": "Pemahaman konsep REST"},
            "examples": {"weight": 0.4, "description": "Contoh yang relevan"},
            "clarity": {"weight": 0.2, "description": "Kejelasan penjelasan"},
        },
        "difficulty": "easy",
        "weight": 1.0,
        "metadata": {"dimension": "api-design", "topic": "rest-basics"},
    },
    # Soal 5: SEDANG
    {
        "role_slug": "backend-engineer",
        "sequence": 5,
        "question_type": "essay",
        "prompt": (
            "Jelaskan perbedaan antara GET dan POST dalam HTTP! "
            "Kapan sebaiknya menggunakan masing-masing method tersebut?"
        ),
        "options": None,
        "correct_answer": None,
        "answer_key": (
            "GET untuk mengambil data (read-only), POST untuk mengirim data. "
            "GET: URL visible, cacheable. POST: body hidden, untuk form/upload."
        ),
        "model_answer": (
            "GET digunakan untuk mengambil data dari server, data dikirim via URL, "
            "bersifat read-only dan bisa di-cache. Contoh: membuka halaman web. "
            "POST digunakan untuk mengirim data ke server, data ada di body request, "
            "lebih aman untuk data sensitif. Contoh: submit form login, upload file. "
            "Gunakan GET untuk read, POST untuk create/update data."
        ),
        "rubric": {
            "get_explanation": {"weight": 0.3, "description": "Penjelasan GET benar"},
            "post_explanation": {"weight": 0.3, "description": "Penjelasan POST benar"},
            "use_cases": {"weight": 0.25, "description": "Contoh penggunaan tepat"},
            "clarity": {"weight": 0.15, "description": "Penjelasan jelas"},
        },
        "difficulty": "medium",
        "weight": 1.0,
        "metadata": {"dimension": "http", "topic": "get-vs-post"},
    },
    # Soal 6: AGAK SUSAH
    {
        "role_slug": "backend-engineer",
        "sequence": 6,
        "question_type": "essay",
        "prompt": (
            "Apa itu JSON dan mengapa format ini populer digunakan dalam API? "
            "Berikan contoh struktur JSON sederhana!"
        ),
        "options": None,
        "correct_answer": None,
        "answer_key": (
            "JSON (JavaScript Object Notation) format data ringan, mudah dibaca. "
            "Populer karena: lightweight, language-independent, easy parsing."
        ),
        "model_answer": (
            "JSON (JavaScript Object Notation) adalah format pertukaran data yang "
            "ringan dan mudah dibaca. Alasan populer: 1) Mudah dibaca manusia, "
            "2) Ukuran kecil dibanding XML, 3) Didukung hampir semua bahasa. "
            'Contoh: {"nama": "Budi", "umur": 20, "jurusan": "TI"}'
        ),
        "rubric": {
            "definition": {"weight": 0.3, "description": "Definisi JSON benar"},
            "advantages": {"weight": 0.3, "description": "Alasan popularitas"},
            "example": {"weight": 0.25, "description": "Contoh JSON valid"},
            "clarity": {"weight": 0.15, "description": "Penjelasan terstruktur"},
        },
        "difficulty": "hard",
        "weight": 1.5,
        "metadata": {"dimension": "data-format", "topic": "json"},
    },
    # === PROFILE (4 soal) ===
    {
        "role_slug": "backend-engineer",
        "sequence": 7,
        "question_type": "profile",
        "prompt": "Sudah berapa lama Anda belajar pemrograman?",
        "options": [
            {"id": "A", "text": "Baru mulai (< 3 bulan)"},
            {"id": "B", "text": "3-6 bulan"},
            {"id": "C", "text": "6-12 bulan"},
            {"id": "D", "text": "1-2 tahun"},
            {"id": "E", "text": "> 2 tahun"},
        ],
        "correct_answer": None,
        "expected_values": {"scoring": {"A": 20, "B": 40, "C": 60, "D": 80, "E": 100}},
        "difficulty": "easy",
        "weight": 1.0,
        "metadata": {"dimension": "experience", "topic": "programming"},
    },
    {
        "role_slug": "backend-engineer",
        "sequence": 8,
        "question_type": "profile",
        "prompt": "Bahasa pemrograman apa yang paling sering Anda gunakan?",
        "options": [
            {"id": "A", "text": "Python"},
            {"id": "B", "text": "JavaScript"},
            {"id": "C", "text": "Java"},
            {"id": "D", "text": "C/C++"},
            {"id": "E", "text": "Belum ada / Lainnya"},
        ],
        "correct_answer": None,
        "expected_values": {"scoring": {"A": 100, "B": 90, "C": 80, "D": 70, "E": 40}},
        "difficulty": "easy",
        "weight": 1.0,
        "metadata": {"dimension": "experience", "topic": "language"},
    },
    {
        "role_slug": "backend-engineer",
        "sequence": 9,
        "question_type": "profile",
        "prompt": "Apakah Anda pernah membuat project backend sendiri?",
        "options": [
            {"id": "A", "text": "Belum pernah"},
            {"id": "B", "text": "Pernah ikut tutorial"},
            {"id": "C", "text": "Pernah membuat project sederhana"},
            {"id": "D", "text": "Pernah membuat beberapa project"},
            {"id": "E", "text": "Sudah punya portfolio project"},
        ],
        "correct_answer": None,
        "expected_values": {"scoring": {"A": 20, "B": 40, "C": 60, "D": 80, "E": 100}},
        "difficulty": "easy",
        "weight": 1.0,
        "metadata": {"dimension": "experience", "topic": "project"},
    },
    {
        "role_slug": "backend-engineer",
        "sequence": 10,
        "question_type": "profile",
        "prompt": "Seberapa familiar Anda dengan database (MySQL/PostgreSQL)?",
        "options": [
            {"id": "A", "text": "Belum pernah menggunakan"},
            {"id": "B", "text": "Tahu dasar-dasar SQL"},
            {"id": "C", "text": "Bisa CRUD sederhana"},
            {"id": "D", "text": "Bisa JOIN dan query kompleks"},
            {"id": "E", "text": "Mahir dan bisa optimasi"},
        ],
        "correct_answer": None,
        "expected_values": {"scoring": {"A": 20, "B": 40, "C": 60, "D": 80, "E": 100}},
        "difficulty": "easy",
        "weight": 1.0,
        "metadata": {"dimension": "experience", "topic": "database"},
    },
]

# ============================================================================
# DATA ANALYST QUESTIONS (Semester 1-2 IT Students)
# ============================================================================
DATA_ANALYST_QUESTIONS = [
    # === THEORETICAL (Pilihan Ganda) ===
    # Soal 1: MUDAH
    {
        "role_slug": "data-analyst",
        "sequence": 1,
        "question_type": "theoretical",
        "prompt": "Apa fungsi utama dari spreadsheet seperti Microsoft Excel?",
        "options": [
            {"id": "A", "text": "Mengedit foto"},
            {"id": "B", "text": "Mengolah dan menganalisis data dalam bentuk tabel"},
            {"id": "C", "text": "Membuat presentasi"},
            {"id": "D", "text": "Menulis dokumen"},
        ],
        "correct_answer": "B",
        "difficulty": "easy",
        "weight": 1.0,
        "metadata": {"dimension": "tools", "topic": "spreadsheet"},
    },
    # Soal 2: SEDANG
    {
        "role_slug": "data-analyst",
        "sequence": 2,
        "question_type": "theoretical",
        "prompt": "Perintah SQL mana yang digunakan untuk mengambil data dari tabel?",
        "options": [
            {"id": "A", "text": "INSERT"},
            {"id": "B", "text": "UPDATE"},
            {"id": "C", "text": "SELECT"},
            {"id": "D", "text": "DELETE"},
        ],
        "correct_answer": "C",
        "difficulty": "medium",
        "weight": 1.0,
        "metadata": {"dimension": "sql", "topic": "basic-queries"},
    },
    # Soal 3: AGAK SUSAH
    {
        "role_slug": "data-analyst",
        "sequence": 3,
        "question_type": "theoretical",
        "prompt": "Apa yang dimaksud dengan rata-rata (mean) dalam statistik?",
        "options": [
            {"id": "A", "text": "Nilai yang paling sering muncul"},
            {"id": "B", "text": "Nilai tengah setelah data diurutkan"},
            {"id": "C", "text": "Jumlah semua nilai dibagi banyaknya data"},
            {"id": "D", "text": "Selisih nilai terbesar dan terkecil"},
        ],
        "correct_answer": "C",
        "difficulty": "hard",
        "weight": 1.0,
        "metadata": {"dimension": "statistics", "topic": "central-tendency"},
    },
    # === ESSAY (Teknis) ===
    # Soal 4: MUDAH
    {
        "role_slug": "data-analyst",
        "sequence": 4,
        "question_type": "essay",
        "prompt": (
            "Jelaskan apa itu data dan berikan 3 contoh data yang sering "
            "Anda temui dalam kehidupan sehari-hari!"
        ),
        "options": None,
        "correct_answer": None,
        "answer_key": (
            "Data adalah fakta/informasi yang bisa diolah. "
            "Contoh: nilai ujian, suhu udara, harga barang."
        ),
        "model_answer": (
            "Data adalah kumpulan fakta, angka, atau informasi yang dapat diolah "
            "untuk mendapatkan insight. Contoh dalam kehidupan sehari-hari: "
            "1) Nilai ujian mahasiswa - data numerik untuk evaluasi akademik, "
            "2) Data transaksi belanja - untuk analisis pengeluaran, "
            "3) Jumlah pengunjung website - untuk mengukur popularitas."
        ),
        "rubric": {
            "definition": {"weight": 0.4, "description": "Definisi data benar"},
            "examples": {"weight": 0.4, "description": "Contoh relevan dan jelas"},
            "clarity": {"weight": 0.2, "description": "Penjelasan mudah dipahami"},
        },
        "difficulty": "easy",
        "weight": 1.0,
        "metadata": {"dimension": "fundamentals", "topic": "data-basics"},
    },
    # Soal 5: SEDANG
    {
        "role_slug": "data-analyst",
        "sequence": 5,
        "question_type": "essay",
        "prompt": (
            "Jelaskan fungsi dari perintah SQL berikut: SELECT, FROM, WHERE! "
            "Berikan contoh query sederhana!"
        ),
        "options": None,
        "correct_answer": None,
        "answer_key": (
            "SELECT: memilih kolom, FROM: menentukan tabel, WHERE: filter. "
            "Contoh: SELECT nama FROM mahasiswa WHERE nilai > 80"
        ),
        "model_answer": (
            "SELECT digunakan untuk memilih kolom yang ingin ditampilkan. "
            "FROM menentukan tabel sumber data. WHERE untuk memfilter data "
            "berdasarkan kondisi tertentu. Contoh query: "
            "SELECT nama, nilai FROM mahasiswa WHERE nilai > 80; "
            "Query ini mengambil nama dan nilai mahasiswa yang nilainya > 80."
        ),
        "rubric": {
            "select_from": {"weight": 0.3, "description": "Penjelasan SELECT FROM"},
            "where": {"weight": 0.3, "description": "Penjelasan WHERE benar"},
            "example": {"weight": 0.25, "description": "Contoh query valid"},
            "clarity": {"weight": 0.15, "description": "Penjelasan terstruktur"},
        },
        "difficulty": "medium",
        "weight": 1.0,
        "metadata": {"dimension": "sql", "topic": "basic-syntax"},
    },
    # Soal 6: AGAK SUSAH
    {
        "role_slug": "data-analyst",
        "sequence": 6,
        "question_type": "essay",
        "prompt": (
            "Apa perbedaan antara data kualitatif dan kuantitatif? "
            "Berikan masing-masing 2 contoh!"
        ),
        "options": None,
        "correct_answer": None,
        "answer_key": (
            "Kuantitatif: data berupa angka (tinggi badan, nilai ujian). "
            "Kualitatif: data deskriptif/kategori (warna, jenis kelamin)."
        ),
        "model_answer": (
            "Data kuantitatif adalah data yang berupa angka dan bisa dihitung, "
            "contoh: tinggi badan (170 cm), nilai ujian (85). "
            "Data kualitatif adalah data yang bersifat deskriptif atau kategori, "
            "contoh: warna favorit (merah, biru), jenis kelamin (L/P). "
            "Kuantitatif bisa dilakukan operasi matematika, kualitatif tidak."
        ),
        "rubric": {
            "quantitative": {"weight": 0.3, "description": "Definisi kuantitatif"},
            "qualitative": {"weight": 0.3, "description": "Definisi kualitatif"},
            "examples": {"weight": 0.25, "description": "Contoh tepat"},
            "comparison": {"weight": 0.15, "description": "Perbandingan jelas"},
        },
        "difficulty": "hard",
        "weight": 1.5,
        "metadata": {"dimension": "statistics", "topic": "data-types"},
    },
    # === PROFILE (4 soal) ===
    {
        "role_slug": "data-analyst",
        "sequence": 7,
        "question_type": "profile",
        "prompt": "Seberapa sering Anda menggunakan Excel atau Google Sheets?",
        "options": [
            {"id": "A", "text": "Belum pernah"},
            {"id": "B", "text": "Jarang (beberapa kali)"},
            {"id": "C", "text": "Kadang-kadang"},
            {"id": "D", "text": "Sering untuk tugas"},
            {"id": "E", "text": "Sangat sering / setiap hari"},
        ],
        "correct_answer": None,
        "expected_values": {"scoring": {"A": 20, "B": 40, "C": 60, "D": 80, "E": 100}},
        "difficulty": "easy",
        "weight": 1.0,
        "metadata": {"dimension": "experience", "topic": "spreadsheet"},
    },
    {
        "role_slug": "data-analyst",
        "sequence": 8,
        "question_type": "profile",
        "prompt": "Apakah Anda sudah pernah belajar SQL?",
        "options": [
            {"id": "A", "text": "Belum pernah"},
            {"id": "B", "text": "Baru dengar istilahnya"},
            {"id": "C", "text": "Pernah belajar dasar"},
            {"id": "D", "text": "Bisa query sederhana"},
            {"id": "E", "text": "Sudah cukup mahir"},
        ],
        "correct_answer": None,
        "expected_values": {"scoring": {"A": 20, "B": 30, "C": 50, "D": 75, "E": 100}},
        "difficulty": "easy",
        "weight": 1.0,
        "metadata": {"dimension": "experience", "topic": "sql"},
    },
    {
        "role_slug": "data-analyst",
        "sequence": 9,
        "question_type": "profile",
        "prompt": "Apakah Anda tertarik dengan visualisasi data (grafik, chart)?",
        "options": [
            {"id": "A", "text": "Tidak tertarik"},
            {"id": "B", "text": "Sedikit tertarik"},
            {"id": "C", "text": "Cukup tertarik"},
            {"id": "D", "text": "Tertarik"},
            {"id": "E", "text": "Sangat tertarik"},
        ],
        "correct_answer": None,
        "expected_values": {"scoring": {"A": 20, "B": 40, "C": 60, "D": 80, "E": 100}},
        "difficulty": "easy",
        "weight": 1.0,
        "metadata": {"dimension": "interest", "topic": "visualization"},
    },
    {
        "role_slug": "data-analyst",
        "sequence": 10,
        "question_type": "profile",
        "prompt": "Bagaimana kemampuan matematika/statistik dasar Anda?",
        "options": [
            {"id": "A", "text": "Kurang percaya diri"},
            {"id": "B", "text": "Cukup"},
            {"id": "C", "text": "Lumayan baik"},
            {"id": "D", "text": "Baik"},
            {"id": "E", "text": "Sangat baik"},
        ],
        "correct_answer": None,
        "expected_values": {"scoring": {"A": 30, "B": 50, "C": 65, "D": 80, "E": 100}},
        "difficulty": "easy",
        "weight": 1.0,
        "metadata": {"dimension": "skill", "topic": "math"},
    },
]


def main() -> None:
    """Main function to seed questions."""
    print(f"🔐 Logging in as {ADMIN_EMAIL}...")
    token = get_admin_token()
    print("✅ Login successful!")

    # Seed Backend Engineer questions
    print("\n🗑️ Deleting existing backend-engineer questions...")
    delete_questions_by_track(token, "backend-engineer")

    print("\n📝 Creating Backend Engineer questions...")
    for q in BACKEND_QUESTIONS:
        result = create_question(token, q)
        if "exists" not in result:
            difficulty = q["difficulty"]
            prompt_preview = q["prompt"][:40]
            print(f"  ✅ [{difficulty}] {prompt_preview}...")

    # Seed Data Analyst questions
    print("\n🗑️ Deleting existing data-analyst questions...")
    delete_questions_by_track(token, "data-analyst")

    print("\n📝 Creating Data Analyst questions...")
    for q in DATA_ANALYST_QUESTIONS:
        result = create_question(token, q)
        if "exists" not in result:
            difficulty = q["difficulty"]
            prompt_preview = q["prompt"][:40]
            print(f"  ✅ [{difficulty}] {prompt_preview}...")

    print("\n🎉 Done! Questions seeded successfully.")
    print("\n📊 Summary per track:")
    print("  Backend Engineer: 3 theoretical, 3 essay, 4 profile")
    print("  Data Analyst: 3 theoretical, 3 essay, 4 profile")
    print("\n📚 Difficulty progression:")
    print("  Theoretical: Easy → Medium → Hard")
    print("  Essay: Easy → Medium → Hard")


if __name__ == "__main__":
    main()
