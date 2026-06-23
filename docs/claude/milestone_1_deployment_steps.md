# Milestone 1 — NUC Deployment Steps

**Status:** Not started. Code is implemented and verified locally (see `milestone_1_plan.md` exit
criteria — all green except the two NUC-dependent ones below).

**Purpose:** A concrete, reviewable checklist of everything that needs to happen on the home NUC
to get `GET https://vogel-api.duckdns.org/health` returning `{"status":"ok"}`. Review this and
decide what you want to do yourself vs. delegate.

> General background on the NUC architecture (sslh/stunnel/NPM, DuckDNS, Docker network) is in
> `fastapi_nuc_setup.md`. This file is the concrete, current-state checklist for actually shipping
> the code that now exists in this repo.

---

## Already done (per prior sessions — verify, don't redo)

- [x] DuckDNS subdomain `vogel-api.duckdns.org` registered and resolving
- [x] NPM proxy host for `vogel-api.duckdns.org` → `dice_applet_api:8000` configured, Let's Encrypt cert issued
- [x] `dice_applet_api` service block already added to the NUC's `docker-compose.yml`
- [x] `curl https://vogel-api.duckdns.org/health` currently returns `502` (correct — container doesn't exist yet)
- [x] Repo cloned to `/srv/dice_applet` on the NUC (on `main`, connected to GitHub)
- [x] `claude` SSH user created; member of `coding` group; `safe.directory` configured for `/srv/dice_applet`

## Steps to do

### 1. Pull the latest code onto the NUC

The repo lives at `/srv/dice_applet`. The `claude` user (SSH alias `nuc-claude`) handles pulls;
Docker commands must be run by `klaas` since `claude` has no Docker access.

```bash
# Pull latest (run as claude):
ssh nuc-claude "cd /srv/dice_applet && git pull"
```

Before pulling, check for the unstaged local changes that exist from the initial setup:

```bash
ssh nuc-claude "cd /srv/dice_applet && git status"
```

If there are local modifications, `klaas` should discard or commit them first:

```bash
ssh nuc  # as klaas
cd /srv/dice_applet
git restore .   # discard local modifications if they are not intentional
```

### 2. Create the MySQL database and user

Run as root in MySQL on the NUC host (MySQL lives on the host, not in Docker):

```sql
CREATE DATABASE dice_applet CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'dice_user'@'%' IDENTIFIED BY 'CHOOSE_A_REAL_PASSWORD';
GRANT ALL PRIVILEGES ON dice_applet.* TO 'dice_user'@'%';
FLUSH PRIVILEGES;
```

Skip if this was already done in an earlier session — check with `SHOW DATABASES;`.

### 3. Create the production `.env` file

Create `/srv/dice_applet/.env` (never committed — already gitignored). Use `.env.example` in
the repo as the template, but **generate fresh values** — do not reuse anything from a local dev
`.env`:

```bash
ssh nuc  # as klaas
cd /srv/dice_applet
python3 -c "import secrets; print('SECRET_KEY=' + secrets.token_hex(32))"
python3 -c "import bcrypt; print('TEACHER_PASSWORD_HASH=' + bcrypt.hashpw(b'REPLACE_WITH_REAL_PASSWORD', bcrypt.gensalt()).decode())"
```

Resulting `.env`:

```env
DATABASE_URL=mysql+aiomysql://dice_user:CHOOSE_A_REAL_PASSWORD@host.docker.internal:3306/dice_applet
SECRET_KEY=<paste generated value>
TEACHER_PASSWORD_HASH=<paste generated value>
ALLOWED_ORIGINS=https://www.klaasvogel.nl
LOG_LEVEL=INFO
```

Note: `DATABASE_URL` must use the real MySQL driver (`mysql+aiomysql://...`). Local dev in this
session used SQLite as a stand-in — that must **not** be carried over to the NUC.

### 4. Build the image

Run as `klaas` (Docker access required):

```bash
ssh nuc
cd /srv/dice_applet
docker build -t dice_applet_api:latest .
```

### 5. Verify the `docker-compose.yml` service block

Confirm the existing block (added in a prior session) matches, with `env_file` pointing to the
new location:

```yaml
  dice_applet_api:
    image: dice_applet_api:latest
    container_name: dice_applet_api
    restart: unless-stopped
    extra_hosts:
      - "host.docker.internal:host-gateway"
    env_file:
      - /srv/dice_applet/.env
    networks:
      - vpn_network
```

### 6. Start the container

Run as `klaas` from wherever the main `docker-compose.yml` lives:

```bash
ssh nuc
docker compose up -d dice_applet_api
docker logs dice_applet_api
# expect: "Uvicorn running on http://0.0.0.0:8000"
```

### 7. Run database migrations

The schema does not exist yet on the NUC's MySQL — this step creates it. Run Alembic inside the
running container (it already has `migrations/` and `alembic.ini` baked in from the `Dockerfile`):

```bash
docker exec dice_applet_api alembic upgrade head
```

This is a one-time step now; it'll need re-running after future migrations are added.

### 8. Verify end to end

From any machine outside the home network:

```bash
curl https://vogel-api.duckdns.org/health
# expect: {"status":"ok"}
```

Optional smoke test of the auth/join flow before connecting the real frontend:

```bash
curl -i -X POST https://vogel-api.duckdns.org/teacher/login \
  -H "Content-Type: application/json" \
  -d '{"password":"REPLACE_WITH_REAL_PASSWORD"}'
# expect: 200 {"ok":true} with a Set-Cookie: dice_session=...
```

---

## Exit criteria

- [ ] MySQL database + user exist on the NUC host
- [ ] `.env` created on the NUC with real MySQL credentials and freshly generated secrets
- [ ] `docker build` succeeds on the NUC
- [ ] `docker compose up -d dice_applet_api` running, logs show Uvicorn started
- [ ] `alembic upgrade head` (via `docker exec`) created all 4 tables
- [ ] `curl https://vogel-api.duckdns.org/health` → `{"status":"ok"}` from outside the home network
