# Local Test / Dev Environment

How to run the app locally — backend on SQLite (no MySQL needed) plus the static frontend —
and how to test flows that depend on a classroom existing, given Milestone 5 (the teacher
dashboard UI for creating classrooms) hasn't been built yet.

---

## 1. Prerequisites

```bash
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
```

## 2. `.env` for local dev

Copy `.env.example` to `.env` and use SQLite instead of MySQL — no local database server needed:

```env
DATABASE_URL=sqlite+aiosqlite:///./dev.db
SECRET_KEY=<generate, see below>
TEACHER_PASSWORD_HASH=<generate, see below>
ALLOWED_ORIGINS=https://www.klaasvogel.nl,http://localhost:5500
LOG_LEVEL=INFO
```

Generate `SECRET_KEY` and `TEACHER_PASSWORD_HASH` (pick any local password — this is a
throwaway credential, unrelated to the real admin password on the NUC/production `.env`):

```bash
.venv/bin/python3 -c "import secrets; print(secrets.token_hex(32))"
.venv/bin/python3 -c "import bcrypt; print(bcrypt.hashpw(b'YOUR_LOCAL_PASSWORD', bcrypt.gensalt()).decode())"
```

`ALLOWED_ORIGINS` must contain the *exact* origin (scheme + host + port) the frontend is
served from. The frontend's `fetch()` calls send `credentials: "include"`, so the browser
enforces a strict CORS match — anything not listed here gets silently rejected in the
console, not a helpful error on screen.

## 3. Apply migrations

```bash
.venv/bin/python3 -m alembic upgrade head
```

This creates `dev.db` from scratch. **If you ever see a 500 on nearly every endpoint**, this
is the first thing to check — a migration may have failed partway, leaving `dev.db` with an
incomplete schema. Fix: delete it and re-run (it's disposable local data, not the NUC/prod DB):

```bash
rm dev.db && .venv/bin/python3 -m alembic upgrade head
```

## 4. Run the backend

```bash
.venv/bin/uvicorn src.dice_applet.main:app --reload
```

API at `http://localhost:8000`, interactive docs at `http://localhost:8000/docs`.

`.env` changes are **not** picked up by `--reload` (it only watches `.py` files) — restart
the process manually after editing `.env`.

## 5. Serve the frontend

```bash
python3 -m http.server 5500 --directory frontend
```

Open **`http://localhost:5500/index.html`** — not a `file://` path. Two things depend on
this:

- `frontend/js/config.js` only points at `http://localhost:8000` when
  `location.hostname` is `localhost` or `127.0.0.1`; any other origin (including `file://`,
  where `location.hostname` is empty) falls back to the production relative path and every
  request 404s.
- Session cookies are set with `Secure` + `SameSite=None` (`services/auth.py`). Browsers
  treat `http://localhost` as a secure-context exception and will accept/send these; they
  won't reliably do the same for `file://` or a bare LAN IP. Keep both frontend and backend
  on `localhost` (not `127.0.0.1`) for consistency.

## 6. Creating a test classroom

The teacher dashboard for creating classrooms (Milestone 5) isn't built yet — but the backend
endpoints it will use already work (added in Milestone 2.1: registration, admin approval,
classroom creation). `scripts/bootstrap_test_classroom.py` drives them directly:

```bash
.venv/bin/python3 scripts/bootstrap_test_classroom.py
```

It prompts for the admin password (the plaintext behind `TEACHER_PASSWORD_HASH`), then:
registers a throwaway teacher + school (skipped if they already exist), approves them as
admin, logs in as that teacher, and creates a classroom — printing a `join_code`.

Safe to re-run: reuses the same teacher/school and just mints a fresh classroom (and join
code) each time. Useful flags: `--base-url`, `--teacher-email`, `--teacher-password`,
`--school-name`, `--classroom-name`.

Paste the printed `join_code` into the student join screen at
`http://localhost:5500/index.html` to test the full Milestone 3 student flow.

## 7. Known local-only quirks

- **`TEACHER_PASSWORD_HASH` is local-only.** It has no relationship to the admin password
  configured in the NUC/production `.env` — regenerate it freely, it never leaves your
  machine.
- **Python HTTP clients don't get the `localhost`-is-secure browser exemption.** A plain
  `httpx`/`requests` client that logs in over `http://` will receive the `Secure` session
  cookie in the response but then silently drop it on the *next* request (the cookie jar
  refuses to send `Secure` cookies over a non-TLS connection — no localhost special case,
  unlike browsers). `scripts/bootstrap_test_classroom.py` works around this in its `login()`
  helper by re-inserting the cookie into the client's jar by hand after each login. Reuse
  that pattern in any other script that authenticates against the local API over plain HTTP.

## Troubleshooting

| Symptom | Cause |
|---|---|
| 500 on almost every request | Migrations didn't fully apply — see step 3 |
| Script gets 401 right after a successful login | The plain-http `Secure` cookie quirk above |
| CORS error in the browser console | Frontend origin missing from `ALLOWED_ORIGINS`, or uvicorn wasn't restarted after editing `.env` |
| Student join / cookies don't persist | Frontend opened as `file://` instead of served from `http://localhost:<port>` |
