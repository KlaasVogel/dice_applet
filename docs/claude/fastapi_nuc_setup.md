# FastAPI on NUC — Setup Instructions

**Status:** Ready to action — all infrastructure details are known.

> For the concrete, current-state checklist of what's left to deploy Milestone 1 (now that the
> code exists), see `milestone_1_deployment_steps.md`. This file remains the general background
> on how the NUC/Docker/NPM architecture is set up.

> **Security warning:** `docs/claude/current_docker-compose.yml` contains live credentials
> (DuckDNS token, NordVPN token, FlexGet password). Add it to `.gitignore` or replace
> the values with placeholders before pushing to GitHub.

---

## Architecture (as it will work)

```
Internet
  └─► Router → NUC:443
        └─► sslh container
              └─► stunnel container (SSL termination)
                    └─► nginx / NPM container  ← all proxy routing lives here
                          └─► dice_applet_api container (internal port 8000)
                                └─► MySQL on NUC host (via host.docker.internal)
```

The frontend on mijndomein.nl calls the API over HTTPS. NPM handles the cert and routes the subdomain to the FastAPI container. MySQL stays on the host — no need to Dockerize it.

---

## Step 1 — Add a second DuckDNS subdomain

Your existing `duckdns` service already keeps `vogelhuis-vpn` updated. Add a second subdomain for the API on the same token by updating the `SUBDOMAINS` line (comma-separated, no spaces):

```yaml
# In your docker-compose.yml, update the duckdns service:
environment:
  - SUBDOMAINS=vogelhuis-vpn,vogel-api   # add the new one here
```

Then register `vogel-api` in the DuckDNS dashboard at https://www.duckdns.org using the same token. Both subdomains will now point to your public IP.

---

## Step 2 — Add the FastAPI service to docker-compose.yml

Add this block to your existing `docker-compose.yml` (alongside the other services):

```yaml
  dice_applet_api:
    image: dice_applet_api:latest   # built on the NUC; see Step 4
    container_name: dice_applet_api
    restart: unless-stopped
    extra_hosts:
      - "host.docker.internal:host-gateway"   # allows connecting to MySQL on the NUC host
    env_file:
      - ./dice_applet/.env          # create this file on the NUC; see Step 3
    networks:
      - vpn_network                 # same network as nginx, so NPM can route to it
```

No `ports:` needed — NPM reaches it over the internal Docker network.

Place the app files at `~/docker/dice_applet/` (or wherever your compose root is).

---

## Step 3 — Create the .env file on the NUC

Create `~/docker/dice_applet/.env` (this file stays on the NUC only — never commit it):

```env
# Database — connects to MySQL on the NUC host
DATABASE_URL=mysql+aiomysql://dice_user:yourpassword@host.docker.internal:3306/dice_applet

# Security
SECRET_KEY=<generate with: python3 -c "import secrets; print(secrets.token_hex(32))">
TEACHER_PASSWORD_HASH=<generate with: python3 -c "import bcrypt; print(bcrypt.hashpw(b'yourpassword', bcrypt.gensalt()).decode())">

# CORS — must match the exact origin of the frontend
ALLOWED_ORIGINS=https://www.klaasvogel.nl

# App
LOG_LEVEL=INFO
```

---

## Step 4 — Deploy: build the image on the NUC

No registry is needed. The NUC builds the image directly from the repo.

First time:
```bash
git clone https://github.com/KlaasVogel/dice_applet.git ~/docker/dice_applet
cd ~/docker/dice_applet
docker build -t dice_applet_api:latest .
docker compose up -d dice_applet_api
```

To deploy an update:
```bash
cd ~/docker/dice_applet
git pull
docker build -t dice_applet_api:latest .
docker compose up -d --no-deps dice_applet_api   # restarts only this service
```

To verify it's running:
```bash
docker logs dice_applet_api
# Should show: "Uvicorn running on http://0.0.0.0:8000"
```

---

## Step 5 — Set up MySQL database on the NUC host

```sql
-- Run as root in MySQL:
CREATE DATABASE dice_applet CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'dice_user'@'%' IDENTIFIED BY 'yourpassword';
GRANT ALL PRIVILEGES ON dice_applet.* TO 'dice_user'@'%';
FLUSH PRIVILEGES;
```

The `@'%'` allows connections from Docker containers (which appear as local network IPs, not `localhost`). If you want to restrict further, use the specific Docker bridge subnet instead of `%`.

---

## Step 6 — Configure NPM proxy host

In the NPM admin panel at `http://NUC-local-IP:81`:

1. **Proxy Hosts → Add Proxy Host**
2. **Domain Names:** `vogel-api.duckdns.org`
3. **Scheme:** `http`
4. **Forward Hostname / IP:** `dice_applet_api`  ← the container name, resolved via Docker DNS
5. **Forward Port:** `8000`
6. **Block Common Exploits:** ✓
7. **SSL tab → Request a new SSL certificate** (Let's Encrypt)
   - Email: klaasvogel@proton.me
   - **Do NOT enable Force SSL** — stunnel terminates TLS before the request reaches NPM.
     NPM receives plain HTTP from stunnel; Force SSL would cause a redirect loop for browser
     CORS preflight requests.
8. After the cert is issued, **remove it from the proxy host** (set Certificate → None on the SSL
   tab). The cert stays on disk in `./nginx/letsencrypt/archive/npm-X/` for stunnel to mount.

NPM stores certs in `./nginx/letsencrypt` automatically and handles renewal.

---

## Step 6b — Add the domain to stunnel's SNI config

stunnel routes HTTPS by inspecting the SNI (domain name in the TLS ClientHello). Every domain
that should reach NPM must be explicitly listed — unlisted domains silently fall through to the
OpenVPN fallback and time out.

**stunnel.conf is baked into the Docker image** (COPY in `Dockerfile.stunnel`), not mounted as a
volume. Any change requires a full image rebuild — `docker restart` alone will NOT apply it.

Find the new cert's archive folder (newest `npm-X` directory):

```bash
ls ~/infra/nginx/letsencrypt/archive/
sudo openssl x509 -noout -subject -in ~/infra/nginx/letsencrypt/archive/npm-X/cert1.pem
```

Then make two changes and rebuild:

**`docker-compose.yml`** — add a volume mount to the stunnel service:
```yaml
stunnel:
  volumes:
    # ... existing mounts ...
    - ./nginx/letsencrypt/archive/npm-X:/etc/stunnel/certs/vogel-api:ro
```

**`stunnel.conf`** — add a new virtual service:
```ini
[nginx_api]
sni = openvpn:vogel-api.duckdns.org
connect = nginx:80
cert = /etc/stunnel/certs/vogel-api/fullchain1.pem
key = /etc/stunnel/certs/vogel-api/privkey1.pem
```

**Rebuild and restart:**
```bash
cd ~/infra
docker compose build stunnel && docker compose up -d stunnel
```

---

## Step 7 — Verify the connection

From any machine outside your home network:
```bash
curl https://vogel-api.duckdns.org/health
# Expected: {"status": "ok"}
```

From browser DevTools on the mijndomein.nl page:
```js
fetch('https://vogel-api.duckdns.org/health').then(r => r.json()).then(console.log)
// Expected: {status: "ok"}  — no CORS error
```

---

## Notes on MySQL — host vs Docker

Keeping MySQL on the host (not in Docker) is the right call here:
- No data migration needed
- No extra ~200 MB RAM for a MySQL container
- The `host.docker.internal` trick (Step 2) lets the container reach it cleanly
- If you ever want to move it to Docker later, it's straightforward

---

## File that will go in the project repo

```
dice_applet/
└── Dockerfile          ← Claude will generate this when backend code is ready
```

The `.env` file lives only on the NUC and is listed in `.gitignore`.
