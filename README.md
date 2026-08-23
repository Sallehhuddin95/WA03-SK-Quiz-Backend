# SK Quiz Backend

FastAPI + PostgreSQL API untuk kuiz Matematik Tahun 6.

## Prasyarat

- Python 3.13
- uv (package manager) - `pip install uv`
- PostgreSQL 14+

## Setup

```powershell
# 1. Pasang dependencies
uv sync

# 2. Sediakan .env (salin dari .env.example, isi password postgres)
Copy-Item .env.example .env

# 3. Cipta database (guna psql atau alat lain)
#    CREATE DATABASE sk_quiz;

# 4. Jalankan migration + seed data rujukan (subjects, tahun, topics)
uv run alembic upgrade head

# 5. Seed 90 soalan MVP (idempotent)
uv run python scripts/seed_dev.py

# 6. Jalankan server
uv run uvicorn app.main:app --reload
```

API docs: http://localhost:8000/docs

## Konfigurasi

Semua melalui environment variable atau `.env`:

| Env | Default | Keterangan |
| --- | --- | --- |
| `DATABASE_URL` | `postgresql+psycopg://postgres:postgres@localhost:5432/sk_quiz` | URL sambungan PostgreSQL |
| `TIMEZONE` | `Asia/Kuala_Lumpur` | Zon masa untuk timestamp API |

## Test

Test suite menggunakan database PostgreSQL berasingan `sk_quiz_test`:

```powershell
# 1. Cipta database test
#    CREATE DATABASE sk_quiz_test;

# 2. Set DATABASE_URL ke database test, kemudian:
uv run pytest
```

Migration dijalankan secara automatik oleh `tests/conftest.py` sebelum suite bermula.

## Struktur

```text
app/
├── api/v1/          # Route handlers (transport sahaja)
├── schemas/         # Pydantic v2 request/response contracts
├── services/        # Logik perniagaan
├── repositories/    # Akses pangkalan data
├── models/          # SQLAlchemy models
└── core/            # Config, database, exceptions, pagination
alembic/             # Migration
scripts/             # Skrip pembangunan
tests/               # pytest suites
```