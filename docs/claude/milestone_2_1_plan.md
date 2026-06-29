# Milestone 2.1 — Multi-Teacher Auth & School Model

**Status:** Planning (2026-06-23)
**Intended reader:** A fresh Claude Code session with no prior conversation context.
**Branch:** `milestone-2-frontend-skeleton` (continues from M2; M2.1 is not a separate branch)

---

## Read these first

1. `CLAUDE.md` — project overview, tech stack, directory structure
2. `docs/claude/ROADMAP.md` — milestone overview
3. `docs/claude/milestone_1_plan.md` — what was built in M1 (current DB schema, auth, endpoints)

---

## Goal

Replace the single `.env`-hash teacher with a proper multi-teacher auth system backed by the
database. Introduce `School` as the top-level organisational unit that groups classrooms and
links to teachers. The existing admin (`.env` hash) is preserved as a superuser.

**Not in scope for M2.1:**
- Student flow changes (M3)
- Classroom management UI (M5)
- Any changes to `Student`, `StudentDataset`, or `Measurement` models
- WebSocket / live updates

---

## 1. Database changes

### 1a. New table: `schools`

```
id            INT PK AUTO_INCREMENT
name          VARCHAR(100) NOT NULL UNIQUE
is_active     BOOLEAN DEFAULT TRUE
created_at    DATETIME DEFAULT now()
```

### 1b. New table: `teachers`

```
id            INT PK AUTO_INCREMENT
email         VARCHAR(254) NOT NULL UNIQUE   -- must be @carmelhengelo.nl
password_hash VARCHAR(60) NOT NULL           -- bcrypt
created_at    DATETIME DEFAULT now()
```

No `is_active` column — a teacher is effectively active when they have at least one approved
`TeacherSchool` row. Checked at login time.

### 1c. New table: `teacher_schools`

Junction table linking teachers to schools, with an approval workflow.

```
id                    INT PK AUTO_INCREMENT
teacher_id            INT FK → teachers.id NOT NULL
school_id             INT FK → schools.id NOT NULL
status                ENUM('pending_admin','pending_school','approved','rejected') NOT NULL
resolved_by           INT FK → teachers.id NULLABLE   -- teacher who approved/rejected
resolved_at           DATETIME NULLABLE
requested_at          DATETIME DEFAULT now()
UNIQUE (teacher_id, school_id)
```

`status` values:
- `pending_admin` — teacher requested a new school; awaiting admin approval
- `pending_school` — teacher requested to join an existing school; awaiting any approved
  teacher at that school
- `approved` — link is active; teacher can manage classrooms at this school
- `rejected` — request denied

### 1d. Modified table: `classrooms`

Add a nullable `school_id` FK (nullable so existing rows are not broken):

```
school_id     INT FK → schools.id NULLABLE
```

Future classrooms created after M2.1 will always have a `school_id`. Existing rows remain
NULL and are treated as legacy/admin-owned.

### Alembic migration

One new migration file: `milestone_2_1_auth_and_schools`.

Steps:
1. Create `schools`
2. Create `teachers`
3. Create `teacher_schools`
4. `ALTER TABLE classrooms ADD COLUMN school_id INT NULL REFERENCES schools(id)`

---

## 2. Auth rework

### Two roles, one cookie

Keep the `dice_session` JWT cookie. Extend the payload:

| Scenario | JWT payload |
|---|---|
| Admin login | `{"role": "admin", "exp": ...}` |
| Teacher login | `{"role": "teacher", "teacher_id": 42, "exp": ...}` |

### `services/auth.py` changes

- `create_admin_token() -> str` — replaces `create_teacher_token()`
- `create_teacher_token(teacher_id: int) -> str` — new, includes `teacher_id`
- `verify_password` — unchanged
- `require_admin` dependency — checks `role == "admin"`
- `require_teacher` dependency — checks `role == "teacher"`, returns `teacher_id: int`
- `require_admin_or_teacher` dependency — accepts either role (for shared endpoints)

### Email validation

In the registration endpoint (not a reusable function — just an inline check):
```python
if not email.lower().endswith("@carmelhengelo.nl"):
    raise HTTPException(400, "Only @carmelhengelo.nl addresses are accepted")
```

---

## 3. API endpoints

### 3a. Auth router — `routers/auth.py` (new file)

**`POST /auth/login`** — unified login

Request:
```json
{ "email": "teacher@carmelhengelo.nl", "password": "..." }
```
Or admin (email omitted / empty):
```json
{ "password": "..." }
```

Logic:
- If `email` is absent or empty → compare password against `settings.teacher_password_hash`
  (admin path); set cookie with `role: admin`
- If `email` present → look up `Teacher` by email, `verify_password`, check they have at
  least one `approved` `TeacherSchool` row; set cookie with `role: teacher, teacher_id`
- Both return `{"ok": true}` on success; `401` on failure

**`POST /auth/register`** — teacher self-registration

Request:
```json
{
  "email": "teacher@carmelhengelo.nl",
  "password": "...",
  "school_id": 3          // existing school — omit if requesting new school
  "new_school_name": null // new school name — omit if joining existing school
}
```

Exactly one of `school_id` / `new_school_name` must be provided.

Logic:
- Validate email domain
- Check email not already registered
- Hash password with bcrypt
- Insert `Teacher` row
- If `new_school_name`:
  - Insert `School(name=new_school_name, is_active=False)` (inactive until admin approves)
  - Insert `TeacherSchool(status='pending_admin')`
- If `school_id`:
  - Verify school exists and `is_active=True`
  - Insert `TeacherSchool(status='pending_school')`
- Return `202 {"ok": true, "pending": true}`

**`POST /auth/logout`** — replaces `DELETE /teacher/logout`

Clears the `dice_session` cookie. No auth required (clearing an invalid cookie is harmless).

**`GET /auth/me`** — identity check for frontend state restore

Returns current session info or `401`. Useful on page load to restore logged-in state.

Response (teacher):
```json
{ "role": "teacher", "teacher_id": 42, "email": "..." }
```
Response (admin):
```json
{ "role": "admin" }
```

---

### 3b. Admin router — `routers/admin.py` (new file)

All routes require `require_admin`.

**`GET /admin/requests`** — list all pending requests

Returns pending `TeacherSchool` rows (both `pending_admin` and `pending_school`), joined
with teacher email, school name.

**`POST /admin/requests/{teacher_school_id}/approve`**

- If `pending_admin`: set `School.is_active=True`, set `TeacherSchool.status='approved'`
- If `pending_school`: set `TeacherSchool.status='approved'`
- Sets `resolved_by=None` (admin has no teacher row), `resolved_at=now()`

**`POST /admin/requests/{teacher_school_id}/reject`**

- Sets `TeacherSchool.status='rejected'`, `resolved_at=now()`

**`GET /admin/schools`** — list all schools (active and inactive)

**`GET /admin/teachers`** — list all teachers with their school links and statuses

---

### 3c. Teacher router — `routers/teacher.py` (updated)

- Remove `POST /teacher/login` and `DELETE /teacher/logout` (moved to `/auth/`)
- All routes: swap `require_teacher` dependency to return `teacher_id`
- `POST /teacher/classrooms` — add `school_id: int` to request body; verify caller is
  approved for that school before creating
- `GET /teacher/classrooms` — filter to classrooms belonging to the teacher's schools
- **New:** `GET /teacher/schools` — list schools where caller is approved
- **New:** `GET /teacher/pending-requests` — `TeacherSchool` rows with `pending_school`
  status where the caller is an approved teacher at that school
- **New:** `POST /teacher/pending-requests/{teacher_school_id}/approve` — set status to
  `approved`, `resolved_by=caller_teacher_id`
- **New:** `POST /teacher/pending-requests/{teacher_school_id}/reject`

---

## 4. Schemas

### `schemas/auth.py` (new)
```python
class LoginRequest(BaseModel):
    email: str = ""
    password: str

class RegisterRequest(BaseModel):
    email: str
    password: str
    school_id: int | None = None
    new_school_name: str | None = None

class MeResponse(BaseModel):
    role: str
    teacher_id: int | None = None
    email: str | None = None
```

### `schemas/teacher.py` (updated)
- Remove `TeacherLoginRequest`
- Add `school_id` to `ClassroomCreateRequest`

### `schemas/admin.py` (new)
```python
class PendingRequestItem(BaseModel):
    id: int
    teacher_email: str
    school_name: str
    status: str
    requested_at: datetime
```

---

## 5. Frontend changes

### Login modal update (`js/teacher.js`, `index.html`)

The existing modal gains:
- An **email field** (shown for teacher login, hidden for admin mode)
- A toggle: "Docent" / "Admin" (two small tabs inside the modal)
- Admin tab: password only — existing behaviour
- Teacher tab: email + password

New i18n keys needed:
```
tab_teacher / tab_admin
label_email / email_placeholder
```

### New: registration form

A new view `view-register` (stub sufficient for M2.1 — full wiring in M2.1 implementation):
- Email input
- Password input
- Radio: "Nieuwe school aanmaken" / "Aansluiten bij bestaande school"
- Conditional: school name text field OR school selector dropdown (populated via
  `GET /admin/schools` — schools list is public for the registration flow)
- Submit → `POST /auth/register`
- On success: show a "Verzoek ingediend" confirmation message

Link from the teacher login modal: "Nog geen account? Verzoek indienen →"

---

## 6. Implementation order

Work in this sequence to keep the app functional at each step:

1. **DB models + migration** — add `School`, `Teacher`, `TeacherSchool`; add `school_id` to
   `Classroom`; run `alembic revision` + `alembic upgrade head` on NUC
2. **Auth service** — update `services/auth.py` (new token functions, new dependencies)
3. **Auth router** — `routers/auth.py` with `/auth/login`, `/auth/logout`, `/auth/register`,
   `/auth/me`; update `main.py` to include it
4. **Admin router** — `routers/admin.py`
5. **Teacher router** — remove old login/logout, update dependencies, add school-scoped
   endpoints
6. **Schemas** — update throughout
7. **Tests** — update `conftest.py` fixtures; add `tests/test_auth.py`,
   `tests/test_admin.py`; update `tests/test_teacher.py` (existing tests will break when
   login endpoint moves)
8. **Frontend** — update login modal (admin/teacher tabs); add registration view

---

## 7. Exit criteria

- [ ] `alembic upgrade head` succeeds — 3 new tables + classrooms.school_id column
- [ ] `POST /auth/login` (no email) with correct `.env` password → 200 + admin cookie
- [ ] `POST /auth/login` (no email) with wrong password → 401
- [ ] `POST /auth/register` with non-carmelhengelo email → 400
- [ ] `POST /auth/register` (new school) → 202; school row `is_active=False`; `TeacherSchool.status='pending_admin'`
- [ ] `POST /auth/register` (existing school) → 202; `TeacherSchool.status='pending_school'`
- [ ] `GET /admin/requests` (admin cookie) → lists both pending types
- [ ] Admin approves new-school request → school becomes active; teacher can log in
- [ ] Teacher approves school-join request → requesting teacher can log in
- [ ] `GET /auth/me` returns correct role/identity for admin and teacher sessions
- [ ] Old `/teacher/login` endpoint removed (returns 404)
- [ ] Frontend: admin tab and teacher tab in login modal both functional
- [ ] Frontend: registration form submits and shows confirmation
- [ ] `pytest` passes
