# College Management — FastAPI Backend

Backend for the **College Management** Flutter app.  
Stack: **FastAPI** · **PostgreSQL (Supabase)** · **SQLAlchemy 2.0 async** · **Alembic** · **JWT Auth**

---

## Quick Start

```bash
# 1. Create and activate a virtual environment
python -m venv .venv
.venv\Scripts\activate        # Windows

# 2. Install dependencies
pip install -r requirements.txt

# 3. Copy environment variables and fill in values
cp .env.example .env

# 4. Run database migrations (creates all tables in Supabase)
alembic upgrade head

# 5. Start the dev server
uvicorn app.main:app --reload --port 8000

# 6. Open the interactive API docs
# http://localhost:8000/docs
```

---

## Setting up Supabase

1. Create a new project at [supabase.com](https://supabase.com)
2. Go to **Project Settings → Database → Connection string**
3. Select **URI mode** and set pooling to **Session**
4. Copy the connection string into your `.env`:
   ```
   DATABASE_URL=postgresql+asyncpg://postgres:[password]@db.[ref].supabase.co:5432/postgres
   ```
5. Run `alembic upgrade head` to create all tables

---

## Project Structure

```
app/
├── main.py           # App factory (CORS, error handler, static files)
├── config.py         # Settings via pydantic-settings
├── database.py       # Async SQLAlchemy session factory
├── core/
│   ├── security.py   # JWT + bcrypt
│   ├── exceptions.py # Domain exception classes
│   ├── dependencies.py # Auth guards (get_current_user, require_role)
│   └── logger/       # Loguru-based centralized logger
├── models/           # SQLAlchemy ORM tables (13 tables)
├── schemas/          # Pydantic v2 request/response models
├── repositories/     # All SQL queries
├── services/         # Business logic (auth, file uploads)
└── api/v1/           # Route handlers (auth, admin, hod, staff, student)
```

---

## Running Tests

```bash
# Install test extras
pip install aiosqlite pytest-asyncio

# Run all tests
pytest
```

Tests use an in-memory SQLite database — no Supabase connection needed.

---

## Generating a Migration

```bash
# After changing any ORM model:
alembic revision --autogenerate -m "describe your change"
alembic upgrade head
```

---

## Deploying to Render

1. Push to GitHub
2. Create a new **Web Service** on Render, connect your repo
3. Render will detect `render.yaml` automatically
4. Set **DATABASE_URL** in Render's environment variables (your Supabase URL)
5. Done — Render deploys on every push to `main`

---

## Roles & Access

| Role      | Access                                                           |
| --------- | ---------------------------------------------------------------- |
| `admin`   | Full user management, system stats                               |
| `hod`     | Exam scheduling, results, timetable, announcements               |
| `staff`   | Attendance, assignments, materials, exam marks                   |
| `student` | Read-only: results, attendance, materials; assignment submission |
