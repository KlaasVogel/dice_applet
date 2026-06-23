# Milestone 1 — NUC Deployment Steps

**Status:** Complete (2026-06-23). `https://vogel-api.duckdns.org/health` returns `{"status":"ok"}` from outside the home network.

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
- [x] Repo cloned to `/srv/dice_applet` on the NUC, `main` branch pulled
- [x] `claude` SSH user created; member of `coding` group; `safe.directory` configured for `/srv/dice_applet`
- [x] MySQL database `dice_applet` and user `dice_user` created on NUC host
- [x] `/srv/dice_applet/.env` created from `.env.example`, `DATABASE_URL` filled in

## Steps to do

### 3. Finish the `.env` — generate SECRET_KEY and TEACHER_PASSWORD_HASH

The `.env` was copied from the example but still has placeholder values for `SECRET_KEY` and
`TEACHER_PASSWORD_HASH`. Generate real values on the NUC:

```bash
ssh nuc  # as klaas
cd /srv/dice_applet

# Generate SECRET_KEY:
python3 -c "import secrets; print('SECRET_KEY=' + secrets.token_hex(32))"

# Generate TEACHER_PASSWORD_HASH (replace the password):
python3 -c "import bcrypt; print('TEACHER_PASSWORD_HASH=' + bcrypt.hashpw(b'REPLACE_WITH_REAL_PASSWORD', bcrypt.gensalt()).decode())"
```

Paste both values into `.env`. The final `.env` should look like:

```env
DATABASE_URL=mysql+aiomysql://dice_user:REAL_PASSWORD@host.docker.internal:3306/dice_applet
SECRET_KEY=<64-char hex string>
TEACHER_PASSWORD_HASH=$2b$12$...
ALLOWED_ORIGINS=https://www.klaasvogel.nl
LOG_LEVEL=INFO
```

Note: `bcrypt` may not be installed system-wide — if the command fails, either
`pip3 install bcrypt` or generate the hash locally and copy it over.

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

- [x] MySQL database + user exist on the NUC host
- [x] `.env` complete on the NUC — `SECRET_KEY` and `TEACHER_PASSWORD_HASH` generated and filled
- [x] `docker build` succeeds on the NUC
- [x] `docker compose up -d dice_applet_api` running, logs show Uvicorn started
- [x] `alembic upgrade head` (via `docker exec`) created all 4 tables
- [x] `curl https://vogel-api.duckdns.org/health` → `{"status":"ok"}` from outside the home network
