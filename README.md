# Dice Applet

An educational web applet for simulating radioactive decay using dice, built for Dutch
secondary school physics classes. Students perform physical dice rolls, record their
measurements in the app, and it visualises the resulting decay curves.

**Live:** [klaasvogel.nl/natuurkunde/dobbelstenen](https://www.klaasvogel.nl/natuurkunde/dobbelstenen)
**Default language:** Dutch, with an English toggle

## How it works

Students start with 100 dice and roll them repeatedly, removing dice that come up a
target colour each round, recording the remaining count after every roll. A paired
variant has two students exchanging dice between rounds. Four activities in total — see
[`CLAUDE.md`](CLAUDE.md) for the full rules and [`docs/claude/ROADMAP.md`](docs/claude/ROADMAP.md)
for build status.

Teachers manage classrooms (create them, get a join code, approve/lock student data)
without collecting any real names — students are identified only by an auto-generated
animal name and a personal code.

## Tech stack

- **Backend:** FastAPI + SQLAlchemy (async) + Alembic, MySQL in production
- **Frontend:** Vanilla HTML/CSS/JS, p5.js for graphs
- **Auth:** Cookie-based sessions (teacher/admin), JWT session cookie (student)

## Getting started (local development)

```bash
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
cp .env.example .env   # then edit — see below
.venv/bin/python3 -m alembic upgrade head
.venv/bin/uvicorn src.dice_applet.main:app --reload
```

For local dev, point `DATABASE_URL` at SQLite instead of MySQL so you don't need a
database server running (`sqlite+aiosqlite:///./dev.db`). Because there's no UI yet to
create a classroom (that's Milestone 5 — see the roadmap), a helper script bootstraps a
test teacher/school/classroom via the API directly:

```bash
.venv/bin/python3 scripts/bootstrap_test_classroom.py
```

**Full walkthrough — env setup, serving the frontend, cookie/CORS gotchas, and
troubleshooting:** [`docs/claude/local_test_environment.md`](docs/claude/local_test_environment.md)

Run the test suite with:

```bash
.venv/bin/pytest
```

## Running with Docker

A self-contained `docker-compose.yml` (API + MySQL) is provided for anyone who wants to
run their own instance:

```bash
cp .env.example .env
```

Edit `.env`:
- Add `MYSQL_PASSWORD=<a password>` — used both for the bundled MySQL container and by
  the API to connect to it (`docker-compose.yml` builds `DATABASE_URL` from this
  automatically; you don't need to set `DATABASE_URL` yourself).
- Generate `SECRET_KEY` and `TEACHER_PASSWORD_HASH`:

  ```bash
  python3 -c "import secrets; print(secrets.token_hex(32))"
  python3 -c "import bcrypt; print(bcrypt.hashpw(b'YOUR_ADMIN_PASSWORD', bcrypt.gensalt()).decode())"
  ```
- Set `ALLOWED_ORIGINS` to whatever origin you'll serve `frontend/` from.

Then:

```bash
docker compose up -d --build
docker compose exec api alembic upgrade head   # first run only
```

The API is now at `http://localhost:8000` (`/health` should return `{"status":"ok"}`).
Serve `frontend/` with any static file server — it's plain HTML/CSS/JS with no build step.

## Project structure

```
dice_applet/
├── src/dice_applet/   # FastAPI app: routers, db models, services, schemas
├── frontend/          # Vanilla HTML/CSS/JS + p5.js graphs
├── migrations/         # Alembic migrations
├── scripts/            # Dev/test helper scripts
├── tests/              # pytest suite
└── docs/               # Roadmap, deployment notes, changelogs
```

## License

MIT — see [`LICENSE`](LICENSE).
