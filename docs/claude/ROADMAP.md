# Roadmap — Dice Applet

Last updated: 2026-06-16
Status key: ⬜ not started · 🔵 in progress · ✅ done

---

## Milestone 0 — Project Foundation ✅

- [x] Tech stack confirmed (FastAPI, SQLAlchemy async, aiomysql, bcrypt, python-jose)
- [x] `.gitignore` created
- [x] Animal names compiled (60 names — see `milestone_1_plan.md`)
- [x] NUC infrastructure complete: Docker service slot added, DuckDNS subdomain `vogel-api.duckdns.org` live, NPM SSL cert issued, 502 confirmed
- [x] `CLAUDE.md` written with full project context
- [x] `docs/claude/fastapi_nuc_setup.md` — step-by-step NUC setup guide

---

## Milestone 1 — Database Schema & Backend Skeleton ✅ COMPLETE (2026-06-23)

**Detailed plan:** `docs/claude/milestone_1_plan.md`
**Deployment record:** `docs/claude/milestone_1_deployment_steps.md`

Goal: All data models exist and the API surface is stubbed out.

- [x] `pyproject.toml` + venv
- [x] `src/dice_applet/` package: `config.py`, `main.py`, `db/`, `routers/`, `schemas/`, `services/`
- [x] SQLAlchemy models: `Classroom`, `Student`, `StudentDataset`, `Measurement`
- [x] Alembic migrations (`alembic upgrade head` verified against NUC MySQL)
- [x] Health endpoint: `GET /health`
- [x] Teacher auth: `POST /teacher/login` → session cookie; `GET /teacher/classrooms`
- [x] Student join: `POST /student/join` → animal name + personal code
- [x] `Dockerfile` built and running on NUC
- [x] `.env.example`
- [x] Deployed to NUC — `curl https://vogel-api.duckdns.org/health` → `{"status":"ok"}`

---

## Milestone 2 — Frontend Skeleton 🔵 IN PROGRESS

Goal: A navigable single-page app with the correct layout and language switching.

- [x] `index.html` base layout (header with flags + gear icon, main content area)
- [x] i18n dictionary (`nl` / `en`) in `i18n.js`; language toggle wires up to all static text
- [x] Teacher login modal (gear icon → password field)
- [x] Student landing view (enter classroom code or personal code)
- [ ] IP-recognition shortcut: "Log in as <name>" when IP is known — **deferred to M3**
- [x] Routing between views (student home, activity tile, teacher dashboard) — no framework, plain JS

**Exit criteria:** Can switch language; clicking gear shows login; entering a code routes to student view (mocked data ok). ✅ Live at https://www.klaasvogel.nl/natuurkunde/dobbelstenen/

---

## Milestone 2.1 — Multi-Teacher Auth & School Model ✅ COMPLETE (2026-06-29)

Goal: Replace the single `.env`-hash teacher with a proper multi-teacher auth system backed
by the database. Introduce `School` as the top-level unit grouping classrooms and teachers.

**Detailed plan:** `docs/claude/milestone_2_1_plan.md`
**Changelog:** `docs/changelog/v0.3.0.md`

- [x] DB: `schools`, `teachers`, `teacher_schools` tables; `school_id` added to `classrooms`
- [x] Alembic migration: `milestone_2_1_auth_and_schools`
- [x] Auth: `POST /auth/login` (unified admin + teacher), `POST /auth/register`, `GET /auth/me`, `POST /auth/logout`
- [x] Admin: `GET /admin/requests`, approve/reject endpoints, schools + teachers list
- [x] Teacher: school-scoped classroom creation; pending-request approval endpoints
- [x] Frontend: admin/teacher tabs in login modal; registration form view

**Exit criteria:** See `milestone_2_1_plan.md` checklist.

---

## Milestone 3 — Student Activity Flow 🔵 IN PROGRESS

**Detailed plan:** `docs/claude/milestone_3_plan.md`

Goal: A student can join a classroom, see their identity, and enter measurements.

- [x] Student session cookie (`student_session` JWT, 24 h) — set on join + reconnect
- [x] `GET /student/me` — returns identity from session cookie
- [x] Dataset + measurement endpoints (`/student/activities`, `/student/activities/{activity}`,
  PUT measurements, POST request-unlock)
- [x] Real join/reconnect fetch calls with inline error display; session cookie restored on page load
- [x] Animal name + emoji displayed after login
- [x] Personal code shown with copy button and hint text (NL + EN)
- [x] Four activity tiles with status badges (not started / in progress / locked)
- [x] Clicking a tile opens the activity view
- [x] Activity view: task description (per activity), data entry table
  - Rows auto-extend on non-zero input; stop at 0 entered at row ≥ 12
  - Role selector shown for activities 3 & 4 (Player 1 / Player 2)
- [x] Lock/unlock state: locked shows warning banner + "Request unlock" button
- [x] Data saved to backend on each cell change (debounced 800 ms)

**Exit criteria:** Student can fill in a full solo activity (Activity 1) end-to-end.

---

## Milestone 4 — Graphs (p5.js) ✅ COMPLETE (2026-07-02)

Goal: Interactive decay graphs for all four activities.

- [x] p5.js sketch base: axis labels (NL/EN), grid, margins
- [x] Single-line graph: dots + smooth curve (Activities 1 & 2)
- [x] Dual-line graph: two datasets, two colours (Activities 3 & 4)
- [x] Hover interaction:
  - Thin red vertical + horizontal crosshair lines
  - Coordinate tooltip near crossing
  - Second crosshair for dual-line graph
- [x] Graph updates live as table data changes — Activities 1 & 2 only (single-student,
  reads the on-screen table). Activities 3 & 4 use mock data until Milestone 4.1 gives
  a real source for both players' data.

**Exit criteria:** Graph renders correctly from mock data for all four activity types with working hover. ✅ Verified in a real browser (Playwright); see `docs/changelog/v0.4.0.md`.

**Detailed plan:** `docs/claude/milestone_4_plan.md`

---

## Milestone 4.1 — Shared Activity Workspace (Activities 3 & 4) ⬜

Goal: Replace the current per-student-isolated dataset for paired activities with a
real shared workspace, so both students see and can edit all the paired data — and so
the M4 dual-line graph can eventually show real data instead of mock data for
Activities 3 & 4.

- [ ] One student creates a shared workspace for Activity 3 or 4; partner joins using
  the first student's personal code, linking both students to the same dataset
- [ ] Both students can toggle between "Player 1" / "Player 2" at any time; toggling
  changes displayed instructions and highlights the column they're currently recording
  — both continue to see all data (both columns) regardless of current role
- [ ] Backend: replace the `UniqueConstraint(student_id, activity)` model for activities
  3 & 4 with a sharing mechanism (join table or workspace concept); new "join by
  personal code" endpoint; authorization updated so both linked students can read/write
  the same StudentDataset row
- [ ] Layout changes to the activity view to accommodate both columns + role toggle

**Exit criteria:** Two students in different browser tabs can both see and edit the same
Activity 3 (or 4) dataset after one joins the other's workspace via personal code.

---

## Milestone 5 — Teacher Dashboard ⬜

Goal: Teacher can manage classrooms and see an overview.

- [ ] Teacher dashboard: list of classrooms (active / inactive)
- [ ] Create new classroom → generates join code → opens classroom view
- [ ] Classroom view:
  - Aggregate graph of all approved student data
  - Join code prominently displayed
  - Two QR codes (site URL only; site URL + code pre-filled)
  - "All-time graph" toggle
  - Gear icon → opens classroom settings in new tab
- [ ] Logout

**Exit criteria:** Teacher can create a classroom, share the join code, and see a (mocked) class graph.

---

## Milestone 6 — Classroom Settings & Data Approval ⬜

Goal: Teacher has full control over which student data appears on the class graph.

- [ ] Classroom settings page: list of students with their data + individual graphs
- [ ] Per-student approve / unapprove toggle (updates class graph)
- [ ] Lock / unlock data per student
- [ ] Unlock request workflow: student requests → teacher sees red indicator → approve (unlock) or deny (keep locked)
- [ ] Class graph filters to approved data only

**Exit criteria:** Full approval/lock flow works end-to-end between a student and teacher in different browser tabs.

---

## Milestone 7 — Deployment & Live Testing ⬜

Goal: App runs on the production server at the correct URL.

- [ ] Decide live testing strategy (SFTP sync vs. direct WSL mount vs. Docker)
- [ ] Production `.env` on server with real MySQL credentials
- [ ] Nginx reverse-proxy config for `https://www.klaasvogel.nl/natuurkunde/dobbelstenen`
- [ ] `systemd --user` service file for the FastAPI/Uvicorn process
- [ ] Final QA pass: full student + teacher flow in production environment

**Exit criteria:** App is reachable at the production URL; full flow works; service survives reboot.

---

## Backlog / Nice-to-have

- [ ] Export classroom data as CSV
- [ ] Print-friendly graph view
- [ ] Teacher can rename a student's animal (if name is offensive or duplicate in small classes)
- [ ] Configurable number of starting dice per classroom (default 100)
- [ ] Dark mode
- [ ] Animated dice roll on the student activity view
- [ ] Smoke-test the new `docker-compose.yml` (API + MySQL) end-to-end — `docker compose up -d --build`,
  run migrations, verify `/health` and a full teacher/student flow; written but not yet run since no
  Docker daemon was available when it was added
- [ ] Fix `#activity-title` not re-translating on language toggle — it's set via
  `textContent` in `student.js`'s `openActivity()`/`_loadAndRenderActivity()` rather
  than a `data-i18n` attribute, so switching NL/EN while an activity view is open
  leaves the title stale until the next navigation. Found during M4 verification,
  pre-existing since M3, out of scope for M4.
- [ ] Verify graph touch/drag crosshair behavior and canvas resize/hide-then-show
  cycle on a real or touch-emulated device — M4's automated verification only
  exercised mouse events on a fixed viewport (see `docs/claude/milestone_4_plan.md`)
