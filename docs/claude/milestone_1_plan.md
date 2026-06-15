# Milestone 1 — Implementation Plan

**Status:** Ready to implement. Infrastructure is complete. No code exists yet.
**Intended reader:** A fresh Claude Code session with no prior conversation context.

---

## Read these first

Before writing any code, read these files in order:

1. `/CLAUDE.md` — project overview, experiment rules, confirmed tech stack, directory structure
2. `docs/claude/ROADMAP.md` — full milestone plan
3. `docs/claude/fastapi_nuc_setup.md` — how the NUC/Docker/NPM infra is set up

### Key facts from prior sessions (not in those files)

- The NUC backend will be reached at `https://vogel-api.duckdns.org` — NPM is already configured and returning 502 (correct, waiting for container)
- MySQL runs on the NUC host outside Docker; containers connect via `host.docker.internal`
- The Docker service block is already added to the NUC's `docker-compose.yml` but the image doesn't exist yet
- `vogel-api.duckdns.org` DuckDNS subdomain is active; Let's Encrypt cert is issued in NPM
- No Python code exists anywhere in this repo yet

---

## Goal

By the end of Milestone 1:

- `uvicorn` starts without errors from `src/dice_applet/main.py`
- `GET /health` returns `{"status": "ok"}`
- Teacher can `POST /teacher/login` and receive a session cookie
- Student can `POST /student/join` with a classroom code and receive an animal name + personal code
- All DB tables exist via `alembic upgrade head` on the NUC MySQL instance
- At least `tests/test_health.py` passes

---

## Confirmed tech stack

| Concern | Decision |
|---|---|
| Language | Python 3.13 |
| Framework | FastAPI + Uvicorn |
| ORM | SQLAlchemy 2.x async (`asyncio` + `aiomysql`) |
| Migrations | Alembic |
| Validation | Pydantic v2 (comes with FastAPI) |
| Config | `pydantic-settings` (reads `.env`) |
| Auth — teacher | Signed cookie (JWT via `python-jose`) |
| Auth — student | Personal code (8-char random string) looked up in DB |
| Password hashing | `bcrypt` |
| Testing | `pytest` + `pytest-asyncio` + `httpx` |
| Formatter | Black, line-length 120 |

---

## File tree to create

```
dice_applet/                     ← repo root
├── src/
│   └── dice_applet/
│       ├── __init__.py
│       ├── main.py              ← FastAPI app, CORS, lifespan
│       ├── config.py            ← Settings via pydantic-settings
│       ├── db/
│       │   ├── __init__.py
│       │   ├── base.py          ← async engine, session factory, Base
│       │   └── models.py        ← all ORM models
│       ├── routers/
│       │   ├── __init__.py
│       │   ├── health.py
│       │   ├── teacher.py
│       │   ├── student.py
│       │   └── classroom.py
│       ├── schemas/
│       │   ├── __init__.py
│       │   ├── teacher.py
│       │   ├── student.py
│       │   └── classroom.py
│       └── services/
│           ├── __init__.py
│           ├── auth.py          ← password verify, cookie sign/verify
│           └── animals.py       ← animal name + code generation
├── migrations/
│   ├── env.py                   ← Alembic env (async-aware)
│   ├── script.py.mako
│   └── versions/                ← empty at start
├── tests/
│   ├── conftest.py
│   └── test_health.py
├── Dockerfile
├── .env.example
├── alembic.ini
└── pyproject.toml
```

---

## pyproject.toml

```toml
[project]
name = "dice-applet"
version = "0.1.0"
requires-python = ">=3.13"
dependencies = [
    "fastapi>=0.115",
    "uvicorn[standard]>=0.30",
    "sqlalchemy[asyncio]>=2.0",
    "aiomysql>=0.2",
    "alembic>=1.13",
    "pydantic-settings>=2.0",
    "python-jose[cryptography]>=3.3",
    "bcrypt>=4.1",
    "python-dotenv>=1.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.23",
    "httpx>=0.27",
    "black",
]

[tool.black]
line-length = 120

[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"
```

---

## Database models (`src/dice_applet/db/models.py`)

### Classroom
| Column | Type | Notes |
|---|---|---|
| id | Integer PK | |
| name | String(100) | teacher-given name |
| join_code | String(5) unique | uppercase alpha, e.g. `HK3TW` |
| is_active | Boolean | default True |
| created_at | DateTime | server default now() |

### Student
| Column | Type | Notes |
|---|---|---|
| id | Integer PK | |
| classroom_id | FK → Classroom | |
| animal_name | String(50) | from animals list below |
| personal_code | String(8) unique | uppercase alphanumeric, e.g. `QP7R2KXN` |
| ip_address | String(45) nullable | for "log in as <name>" shortcut |
| created_at | DateTime | server default now() |

### StudentDataset
One row per student per activity (max 4 rows per student). Tracks lock/approval state.

| Column | Type | Notes |
|---|---|---|
| id | Integer PK | |
| student_id | FK → Student | |
| activity | SmallInteger | 1–4 |
| is_locked | Boolean | default False — teacher can lock |
| unlock_requested | Boolean | default False — student requests unlock |
| is_approved | Boolean | default False — teacher approves for class graph |

Unique constraint: `(student_id, activity)`.

### Measurement
| Column | Type | Notes |
|---|---|---|
| id | Integer PK | |
| dataset_id | FK → StudentDataset | |
| player | SmallInteger | 1 or 2 (activities 3 & 4 have two players) |
| roll_number | SmallInteger | 0 = before first roll (starting count) |
| dice_count | SmallInteger | number of dice remaining |
| recorded_at | DateTime | server default now() |

---

## Config (`src/dice_applet/config.py`)

```python
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    database_url: str
    secret_key: str
    teacher_password_hash: str
    allowed_origins: str = "https://www.klaasvogel.nl"
    log_level: str = "INFO"

    @property
    def origins_list(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",")]

settings = Settings()
```

---

## Main app (`src/dice_applet/main.py`)

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from .db.base import init_db
from .routers import health, teacher, student, classroom

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield

app = FastAPI(title="Dice Applet API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(teacher.router, prefix="/teacher")
app.include_router(student.router, prefix="/student")
app.include_router(classroom.router, prefix="/classroom")
```

---

## API endpoints for Milestone 1

Only implement these — stub the rest with `raise HTTPException(501)` or `TODO` comments.

### Health
- `GET /health` → `{"status": "ok"}`

### Teacher
- `POST /teacher/login` body: `{password: str}` → sets `dice_session` cookie, returns `{"ok": true}`
- `DELETE /teacher/logout` → clears cookie
- `POST /teacher/classrooms` body: `{name: str}` → creates classroom, returns `{id, name, join_code}`
- `GET /teacher/classrooms` → `[{id, name, join_code, is_active, student_count}]`

### Student
- `POST /student/join` body: `{classroom_code: str}` → returns `{animal_name, personal_code}`
  - classroom_code lookup is case-insensitive
  - generates unique animal_name within the classroom (no duplicates per classroom)
  - if IP already in classroom students list, include `{suggested_name, suggested_code}` in response too
- `POST /student/reconnect` body: `{personal_code: str}` → returns `{animal_name, classroom_id}`

### Classroom (teacher auth required)
- `GET /classroom/{id}` → `{id, name, join_code, is_active, students: [{id, animal_name, personal_code}]}`

---

## Auth implementation

### Teacher session cookie
Use `python-jose` to sign a simple payload:

```python
# services/auth.py
from jose import jwt
from datetime import datetime, timedelta, timezone
from .config import settings

ALGORITHM = "HS256"
COOKIE_NAME = "dice_session"

def create_teacher_token() -> str:
    expire = datetime.now(timezone.utc) + timedelta(hours=12)
    return jwt.encode({"role": "teacher", "exp": expire}, settings.secret_key, algorithm=ALGORITHM)

def verify_teacher_token(token: str) -> bool:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
        return payload.get("role") == "teacher"
    except Exception:
        return False

def verify_password(plain: str, hashed: str) -> bool:
    import bcrypt
    return bcrypt.checkpw(plain.encode(), hashed.encode())
```

Protect teacher routes with a FastAPI dependency:

```python
from fastapi import Cookie, HTTPException, status

async def require_teacher(dice_session: str | None = Cookie(default=None)):
    if not dice_session or not verify_teacher_token(dice_session):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
```

### Student identity
No token needed for Milestone 1. Students pass their `personal_code` in a request body or as a header `X-Personal-Code`. The service looks it up in the DB.

---

## Animal names list (`services/animals.py`)

Use these 60 names. Within a classroom, each student gets a unique name (retry if taken):

```python
ANIMAL_NAMES = [
    "Albatross", "Axolotl", "Badger", "Barracuda", "Bison",
    "Blobfish", "Capybara", "Chameleon", "Cheetah", "Chinchilla",
    "Chipmunk", "Condor", "Coyote", "Dingo", "Dolphin",
    "Echidna", "Elephant", "Flamingo", "Fox", "Gecko",
    "Giraffe", "Gorilla", "Hamster", "Hedgehog", "Hyena",
    "Iguana", "Jaguar", "Jellyfish", "Kangaroo", "Kiwi",
    "Koala", "Lemur", "Leopard", "Llama", "Lynx",
    "Manatee", "Meerkat", "Mongoose", "Narwhal", "Numbat",
    "Ocelot", "Octopus", "Okapi", "Orca", "Ostrich",
    "Otter", "Pangolin", "Parrot", "Porcupine", "Quokka",
    "Raccoon", "Rhino", "Salamander", "Sloth", "Tapir",
    "Tarantula", "Toucan", "Walrus", "Wombat", "Zebrafish",
]
```

Personal code generation (8 chars, uppercase alphanumeric, no ambiguous chars O/0/I/1):

```python
import secrets
SAFE_CHARS = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"

def generate_personal_code() -> str:
    return "".join(secrets.choice(SAFE_CHARS) for _ in range(8))

def generate_join_code() -> str:
    return "".join(secrets.choice(SAFE_CHARS) for _ in range(5))
```

---

## Dockerfile

```dockerfile
FROM python:3.13-slim

WORKDIR /app

COPY pyproject.toml .
RUN pip install --no-cache-dir ".[dev]"

COPY src/ src/
COPY migrations/ migrations/
COPY alembic.ini .

RUN useradd -m -u 1000 appuser && chown -R appuser /app
USER appuser

EXPOSE 8000
CMD ["uvicorn", "dice_applet.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## .env.example

```env
DATABASE_URL=mysql+aiomysql://dice_user:yourpassword@host.docker.internal:3306/dice_applet
SECRET_KEY=generate_with__python3_-c__import_secrets_print_secrets.token_hex_32
TEACHER_PASSWORD_HASH=generate_with__python3_-c__import_bcrypt_print_bcrypt.hashpw_b_yourpassword_bcrypt.gensalt.decode
ALLOWED_ORIGINS=https://www.klaasvogel.nl
LOG_LEVEL=INFO
```

---

## Alembic setup notes

Run after creating models:
```bash
alembic init migrations
# then edit migrations/env.py to use async engine — see SQLAlchemy async Alembic docs
alembic revision --autogenerate -m "initial schema"
alembic upgrade head
```

The `migrations/env.py` must import `Base` from `src.dice_applet.db.base` and use `run_async_migrations()` pattern (standard for SQLAlchemy 2.x async Alembic).

---

## Implementation order

Follow this sequence to keep things runnable at each step:

1. `pyproject.toml` → `pip install -e ".[dev]"`
2. `config.py` + `.env.example`
3. `db/base.py` (engine + session)
4. `db/models.py` (all models)
5. Alembic init + first migration
6. `services/auth.py` + `services/animals.py`
7. `routers/health.py` + `main.py` (minimal, just health route) → verify `uvicorn` starts
8. `routers/teacher.py` + schemas
9. `routers/student.py` + schemas
10. `routers/classroom.py` (stub)
11. `tests/conftest.py` + `tests/test_health.py`
12. `Dockerfile` → verify `docker build` succeeds

---

## Exit criteria checklist

- [ ] `pip install -e ".[dev]"` succeeds
- [ ] `uvicorn dice_applet.main:app --reload` starts without errors
- [ ] `curl http://localhost:8000/health` → `{"status":"ok"}`
- [ ] `alembic upgrade head` creates all tables in MySQL
- [ ] Teacher login endpoint sets a cookie and returns 200
- [ ] Student join endpoint returns animal name + personal code
- [ ] `pytest` passes (at minimum `test_health.py`)
- [ ] `docker build -t dice_applet_api:latest .` succeeds
- [ ] After `docker compose up -d dice_applet_api` on NUC: `curl https://vogel-api.duckdns.org/health` → `{"status":"ok"}`
