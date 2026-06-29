# CLAUDE.md — Dice Applet

## Project Overview

An educational web applet for simulating radioactive decay using dice, used in Dutch secondary school physics classes. Students perform physical dice rolls and record their measurements here; the app visualises the resulting decay curves.

**Deployment URL:** `https://www.klaasvogel.nl/natuurkunde/dobbelstenen`
**Default language:** Dutch (toggle to English via flag icon)
**Target users:** Teachers (manage classrooms) + Students (record measurements)

---

## The Experiment

### Version 1 — Solo (2 activities)

- Start with 100 dice (2 blue sides, 1 white side, 3 unpainted sides)
- **Activity 1 (blue):** Roll all dice; remove dice showing blue. Record remaining count. Repeat.
- **Activity 2 (white):** Same procedure, removing white dice instead.

### Version 2 — Paired (2 more activities, 2 students)

- Student 1 starts with all dice; Student 2 starts with zero.
- **Activity 3:** Student 1 rolls; donates blue-top dice to Student 2. Student 2 rolls; removes white-top dice. Both record counts before each roll.
- **Activity 4:** Same as Activity 3 but colours are swapped (Student 1 donates white, Student 2 removes blue).

The four activities map to four tiles in the student UI.

---

## Roles & Access

| Role | Access method |
|---|---|
| Teacher | Password login via gear icon (top corner) |
| Student | Classroom code (4–5 chars) or personal code |

Students get an auto-generated animal name + icon as their identity within a session. They should write down their personal code to reconnect or share with a partner.

---

## Tech Stack (decisions & proposals)

| Concern | Decision | Status |
|---|---|---|
| Backend | FastAPI + Uvicorn | confirmed |
| ORM / DB layer | SQLAlchemy (async) | confirmed |
| Database | MySQL on NUC host (outside Docker) | confirmed |
| Graphs | p5.js | confirmed |
| Frontend | Vanilla HTML/CSS/JS | confirmed |
| Auth | Cookie-based session (teacher); short-lived token (student) | proposed |
| Real-time | WebSockets for live classroom graph updates | proposed |
| Backend host | Home NUC, Dockerized | confirmed |
| Reverse proxy | Nginx Proxy Manager (NPM) on NUC | confirmed |
| SSL | Let's Encrypt via NPM | confirmed |
| API domain | `vogel-api.duckdns.org` | confirmed |
| Image build | Build on NUC via `git pull` + `docker build` (no registry) | confirmed |

> Tag proposals with **confirmed** in this file once agreed.

---

## Project Structure

```
dice_applet/
├── .venv/
├── src/
│   └── dice_applet/
│       ├── main.py           # FastAPI app entry point
│       ├── db/               # SQLAlchemy models + session
│       ├── routers/          # teacher.py, student.py, classroom.py
│       ├── services/         # business logic
│       └── schemas/          # Pydantic schemas
├── frontend/
│   ├── index.html
│   ├── css/
│   ├── js/
│   │   ├── graph.js          # p5.js sketch
│   │   ├── student.js
│   │   └── teacher.js
│   └── assets/
│       └── animals/          # SVG icons per animal
├── tests/
├── docs/
│   └── claude/
│       ├── IDEAS.md          # original idea dump
│       ├── ROADMAP.md        # phased milestone plan
│       ├── architecture.md   # detailed arch decisions (TBD)
│       └── conventions.md    # naming, i18n keys, etc. (TBD)
├── .gitignore
├── CLAUDE.md                 # this file
├── README.md
└── pyproject.toml
```

---

## Key Concepts & Terminology

| Dutch | English | Notes |
|---|---|---|
| worp | throw / roll | x-axis label |
| actieve dobbelstenen | active dice | y-axis label |
| dobbelstenen | dice | |
| klas | classroom | teacher-managed group |
| leerling | student | |

---

## i18n

- All UI text exists in both NL (default) and EN.
- Language toggle is a flag icon in the top corner.
- Animal names stay in English in both languages.
- Store translations in a simple `i18n.js` dictionary object (no heavy library needed at this scale).

---

## Data & Privacy

- Students are identified only by animal name + personal code — no real names collected by the app.
- Teacher sets a classroom name; students join with a short code.
- Teacher can approve, lock, or reject individual student datasets before they appear on the class graph.

---

## NUC — dice_applet
- SSH user: claude (key-based only, no docker/sudo access)
- SSH alias: `nuc-claude`
- Shared group `coding` (klaas + claude) owns /srv/dice_applet
  - setgid bit enabled — new files inherit group `coding`
  - `safe.directory` already configured for `/srv/dice_applet` in claude's git config
- Can perform: git pull, git status, git log within /srv/dice_applet
- Cannot run docker commands — instead, output the exact commands 
  for the developer to run manually
- Always ask permission before connecting or pulling

## Web Server Access (klaasvogel.nl)
- Connect via: `lftp klaasvogel`
- Connects directly to `/httpdocs/natuurkunde/dobbelstenen`
- FTP with SSL verification disabled (certificate mismatch on host)
- **Always ask permission before connecting**
- **Always ask permission before uploading or deleting files**
- Once permission is granted it applies for the current session only
- Never upload outside the designated directory
- **CRITICAL:** Always use `put localfile -o subdir/filename` — plain `put` strips the
  directory and silently drops the file in the wrong location (e.g. `put frontend/css/style.css`
  lands at root as `style.css`, not `css/style.css`)

## Version Control Conventions
- Commit messages must start with the version number: `v0.3.0 description of change`
- Version bumps: patch (x.x.N) for fixes/docs; minor (x.N.0) for completed milestones
- Each milestone completion gets its own `docs/changelog/vX.Y.Z.md`

## Development Notes

- Run backend locally with `uvicorn src.dice_applet.main:app --reload`
- Live testing strategy: TBD (SFTP sync vs. direct WSL mount — decide before Milestone 7)
- MySQL connection string goes in `.env` (never committed); use `python-dotenv` to load it.
- See `docs/claude/ROADMAP.md` for the phased plan.
