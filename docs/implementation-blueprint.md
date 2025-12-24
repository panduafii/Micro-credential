# Implementation Blueprint & Delivery Plan

## 1. Validasi PRD vs Kode Saat Ini
- **Endpoint inti belum ada** — PRD mendeskripsikan alur assessment lengkap (`docs/prd.md:85-105`), tetapi aplikasi hanya memiliki `/health` (`src/api/routes/health.py:11`). Semua endpoint assessment, status polling, admin katalog, dan feedback belum diimplementasikan sama sekali.
- **Persistensi dan model data belum tersedia** — PRD mengharuskan tabel `assessments`, `assessment_question_snapshots`, `rule_scores`, `recommendation_items`, dan lainnya (`docs/prd.md:178-205`), tetapi kode hanya memiliki dataclass placeholder (`src/domain/models.py:7-34`) dan repository mock yang hanya melakukan logging (`src/infrastructure/repositories/unit_of_work.py:9-58`).
- **Pipeline async GPT/RAG masih fiktif** — PRD dan Epic 3 menuntut scoring GPT + rekomendasi RAG dengan status degraded (`docs/prd/epic-3-recommendations-transparency-and-feedback-loop.md:11-35`), sedangkan worker saat ini hanya mengembalikan payload dummy (`src/workers/jobs.py:10-53`).
- **Observability & auth belum diaplikasikan** — Ketentuan observability (`docs/prd.md:194-205`) dan role-based access belum diikat ke endpoint mana pun. `src/core/auth.py` dan middleware logging siap dipakai, namun belum digunakan sehingga keamanan masih kosong.
- **Pengujian tidak mencakup alur utama** — PRD minta integrasi/E2E (misal MVP validation plan `docs/prd/mvp-validation-plan.md:1-5`), tapi hanya ada tes health dan JWT (`tests/unit/test_api_health.py`, `tests/unit/test_auth.py`).

## 2. Blueprint Arsitektur
1. **Lapisan API (FastAPI)**
   - Router: `assessments`, `tracks`, `admin/questions`, `admin/credentials`, `recommendations/feedback`, `status`.
   - Dependency: `get_current_user` + `require_roles` untuk role `student`, `advisor`, `admin`.
2. **Lapisan Domain & Service**
   - Service `AssessmentService` untuk start/resume, `SubmissionService` untuk finalisasi & enqueue jobs, `RecommendationService` untuk pembacaan hasil.
3. **Lapisan Persistensi**
   - Gunakan SQLAlchemy async (sudah ada di dependency). Implementasi UnitOfWork yang membungkus session + repo.
   - Alembic untuk migrasi versi pertama.
4. **Pipeline Async**
   - Queue `default` untuk `score_essay`, `generate_recommendations`, `fusion_summary`.
   - Job flow:
     1. `score_essay` → panggil OpenAI (atau mock) + simpan ke `essay_scores`.
     2. `generate_recommendations` → buat query RAG, panggil vector store, simpan ke `recommendation_items`.
     3. `fusion_summary` → gabung rule score + essay + RAG, update `recommendations`, set status `completed`.
   - Degraded mode: jika salah satu job gagal, set flag `degraded` dan fallback ke template statis.
5. **Integrasi RAG**
   - Library vector store (Chroma atau PGVector). Simpan `credential_catalog` dan `rag_traces` sesuai PRD.
   - Proses build index off-line melalui script `scripts/build_rag_index.py`.

## 3. Rencana Data & Migrasi
| Tabel | Fungsi | Catatan Migrasi |
| --- | --- | --- |
| `role_catalog` | Daftar track/role | Seed awal dari PRD (Backend Engineer, Data Analyst, dll.) |
| `assessments` | Header assessment | Kolom status, owner_id, role_id, timestamps |
| `assessment_question_snapshots` | Snapshot 10 pertanyaan | Simpan versi agar reproducible |
| `assessment_responses` | Jawaban per pertanyaan | JSON untuk essay/profile |
| `rule_scores` | Skor rule-based | Simpan breakdown rubric |
| `essay_scores` | Skor GPT | Termasuk trace/token metadata |
| `recommendations` | Ringkasan akhir | Flag degraded, narrative, latensi |
| `recommendation_items` | Item rekomendasi | Ranking, trace_id |
| `rag_traces` | Detail sumber RAG | Teks, sumber URL |
| `recommendation_feedback` | Feedback advisor/student | Link ke assessment |
| `async_jobs` | Riwayat job | Status queue, retry count |
| `metric_snapshots` | Observatory data | Latency ms, token count, queue depth |

Langkah migrasi:
1. Tambahkan Alembic + generate revisi awal untuk semua tabel.
2. Buat seed script memuat `role_catalog`, `credential_catalog`, `question_bank` dari PRD.
3. Siapkan fixture data lokal (YAML/JSON) untuk testing.

## 4. Strategi Data, RAG, dan Anti-Halusinasi
- **Katalog Kredensial**: buat CSV/JSON berisi micro-credential nyata (nama, deskripsi, tag, tautan). Data ini menjadi sumber tunggal untuk RAG. Pastikan ada referensi ke institusi atau situs real agar rekomendasi dapat diverifikasi.
- **RAG Index Lifecycle**:
  1. Import CSV → normalisasi → simpan di Postgres `credential_catalog`.
  2. Jalankan script embedding menggunakan `text-embedding-3-small` (atau model lokal jika biaya menjadi concern) dan simpan embedding di PGVector/Chroma.
  3. Worker RAG mengambil Top-K berdasarkan role + sinyal profil.
- **Scoring GPT**: definisikan rubric eksplisit (misalnya dimensi clarity/accuracy/coherence) dan log prompt+response (disensor) ke `audit_events` agar bisa diaudit dan menghindari output tak terlacak.
- **Fallback Mode**: siapkan template rekomendasi manual yang diambil dari `credential_catalog` untuk tiap role jika GPT/RAG gagal. Catat flag `degraded` + penyebab.
- **Validasi Data**: tambahkan constraint referential + check (misal `status` enum) untuk menjamin data konsisten.

## 5. Observability & DevOps
- **Logging**: gunakan `structlog` dengan contextvars (sudah ada di `src/api/main.py:24-41`). Tambahkan event penting di service & worker.
- **Metrics**: integrasi Prometheus FastAPI middleware untuk request/latency. Worker menulis `metric_snapshots` + ekspor via custom endpoint atau pushgateway.
- **Tracing**: opsional dengan OpenTelemetry; targetkan trace id dibawa dari API → worker via job payload.
- **Deployment Pipeline**:
  1. Tambah Dockerfile (jika belum). 2. Definisikan Compose untuk API + worker + Postgres + Redis + Chroma. 3. Rencana infra ke ECS Fargate seperti PRD (tulis modul Terraform dasar: VPC, ECS service, RDS, Elasticache).
- **Runbook**: dokumentasikan prosedur gagal queue, RAG rebuild, rotate key.

## 6. Backlog & Sprint Plan (4 Sprint)
1. **Sprint 1 – Fondasi API & DB (Week 1)**
   - Setup Alembic, definisi model SQLAlchemy, migrasi awal.
   - Implement endpoint track listing, assessment start/resume (rule-based scaffolding).
   - Integrasikan auth dependencies dan validasi role.
   - Unit test untuk config/model/service dasar.
2. **Sprint 2 – Async Pipeline & Worker (Week 2)**
   - Implement `score_essay`, `generate_recommendations`, `fusion_summary` job skeleton.
   - Hubungkan RQ worker dengan repo DB nyata.
   - Tambah status polling endpoint dan webhook stub.
   - Integration test jalur submit → job queued.
3. **Sprint 3 – RAG, Observability, Feedback (Week 3)**
   - Build data ingestion + embedding pipeline.
   - Implement RAG query builder + fallback degraded mode.
   - Tambah metrics/logging hooks, Prometheus endpoints, feedback endpoint.
   - E2E test dengan dataset sample.
4. **Sprint 4 – Hardening & Pilot Readiness (Week 4)**
   - Load/perf test minimal (≥100 concurrent assessments simulasi).
   - Dokumentasi runbook, dashboard Grafana, alert rules.
   - Pilot instrumentation (dashboard queue depth, failure rate).
   - Uji keamanan dasar (JWT misuse, role bypass).

## 7. Tindak Lanjut
- Konfirmasi sumber data credential + question bank realistis sebelum Sprint 2.
- Tentukan anggaran OpenAI/token atau alternatif open-source untuk menghindari dependensi biaya.
- Setelah blueprint disetujui, kita bisa mulai mengimplementasikan Sprint 1 (migrasi + endpoint dasar).
