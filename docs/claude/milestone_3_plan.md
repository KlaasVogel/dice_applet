# Milestone 3 Plan — Student Activity Flow

Created: 2026-07-01
Status: planning

---

## Goal

A student can join a classroom (or reconnect), see their identity, open one of four activity tiles,
fill in a measurement table, and have their data saved to the backend. The teacher can still see the
classroom but M3 does not touch the teacher dashboard.

**Exit criteria:** Student can complete Activity 1 end-to-end — join, see animal name + personal
code, open Activity 1 tile, enter 12+ rows of dice counts, and the data persists across a page
reload via reconnect.

---

## Key Design Decision — Student Session

Teacher auth already uses a JWT cookie (`dice_session`). Students will get the same treatment:
`POST /student/join` and `POST /student/reconnect` both set a `student_session` HttpOnly JWT cookie
carrying `{student_id}`. All student data endpoints read from this cookie via a `require_student`
dependency. The personal code is still returned in the join/reconnect response so the student can
write it down; it is not used as a request credential.

---

## Animal Icons

No SVG files exist in `frontend/assets/animals/`. For M3 we use a simple emoji lookup table in JS
(one emoji per animal name). SVG icons can be added later without changing the data layer.

---

## No New Alembic Migration Needed

All necessary DB columns already exist (`is_locked`, `unlock_requested`, `is_approved`, `player`,
`roll_number`, `dice_count`). M3 adds no schema changes.

---

## Implementation Phases

### Phase 1 — Student Session & Identity (backend)

**New dependency — `require_student`**
```
src/dice_applet/dependencies.py  (new)
```
Reads `student_session` cookie → decodes JWT → fetches `Student` row → returns it.
Returns `401` if cookie absent or invalid.

**Update `POST /student/join`**
- After creating/fetching the Student row, sign a JWT `{sub: student_id}` and set
  `student_session` HttpOnly cookie (same pattern as `dice_session`, 24 h expiry).
- Response body: `{animal_name, personal_code, suggested_name?, suggested_code?}` (unchanged).

**Update `POST /student/reconnect`**
- After lookup, also set `student_session` cookie.
- Response body: add `personal_code` and `classroom_name` to existing `{animal_name, classroom_id}`.

**New `GET /student/me`**
- Auth: `require_student`.
- Returns: `{student_id, animal_name, personal_code, classroom_id, classroom_name}`.

**New schemas** (add to `src/dice_applet/schemas/student.py`):
```python
class StudentMe(BaseModel):
    student_id: int
    animal_name: str
    personal_code: str
    classroom_id: int
    classroom_name: str

class ReconnectResponse(BaseModel):
    animal_name: str
    personal_code: str
    classroom_id: int
    classroom_name: str
```

---

### Phase 2 — Dataset & Measurement Endpoints (backend)

All routes under `/student/`, all protected by `require_student`.

#### `GET /student/activities`
Returns the status of all 4 activity slots for the current student. Creates missing
`StudentDataset` rows lazily (so the student always sees 4 tiles regardless of whether they've
started each activity).

Response: `list[ActivityStatus]`
```python
class ActivityStatus(BaseModel):
    activity: int          # 1–4
    dataset_id: int
    is_locked: bool
    unlock_requested: bool
    measurement_count: int  # len of measurements for activity
```

#### `GET /student/activities/{activity}`
Returns full dataset detail for one activity.

Response: `DatasetDetail`
```python
class MeasurementOut(BaseModel):
    id: int
    player: int
    roll_number: int
    dice_count: int

class DatasetDetail(BaseModel):
    dataset_id: int
    activity: int
    is_locked: bool
    unlock_requested: bool
    measurements: list[MeasurementOut]
```

#### `PUT /student/activities/{activity}/measurements`
Bulk-replace all measurements for this activity (for one player at a time).
Body: `{player: int, rows: list[{roll_number: int, dice_count: int}]}`

Logic: delete existing Measurement rows for this (dataset_id, player), insert new rows. This
keeps the save simple — frontend sends the full current table on each debounced save.
Returns: updated `DatasetDetail`.

Not allowed if `is_locked=True` → `403`.

#### `POST /student/activities/{activity}/request-unlock`
Sets `unlock_requested=True` on the StudentDataset. No-op if already requested.
Returns `{ok: true}`.
Not allowed if `is_locked=False` (nothing to unlock) → `400`.

**New file:** `src/dice_applet/routers/student_data.py`
Register under `/student` in `main.py`.

**New service file:** `src/dice_applet/services/student_data.py`
Contains all DB logic for the above (keeps routers thin).

---

### Phase 3 — Frontend: Join / Reconnect / Identity

**`student.js` — real fetch calls + module state**

Module-level state object:
```js
const session = { studentId: null, animalName: null, personalCode: null, classroomId: null };
```

`joinWithClassroomCode()`:
1. POST `/student/join` with `{classroom_code}`.
2. On success: store response fields in `session`, call `renderStudentHome()`, `showView("student-home")`.
3. On error: show inline error message below the input.

`joinWithPersonalCode()`:
1. POST `/student/reconnect` with `{personal_code}`.
2. Same success path.

On page load (`app.js`): call `GET /student/me`. If 200 → restore session + `showView("student-home")`.
If 401 → stay on landing.

**`router.js`**: add `student-activity` as a known view name.

---

### Phase 4 — Frontend: Student Home View

Replace the stub `#view-student-home` card in `index.html` with:

```html
<!-- Identity card -->
<div id="identity-card">
  <span id="animal-emoji" class="animal-emoji"></span>
  <span id="animal-name" class="animal-name"></span>
  <div class="personal-code-row">
    <span data-i18n="personal_code_label"></span>
    <code id="personal-code-display"></code>
    <button id="btn-copy-code" data-i18n="copy"></button>
  </div>
  <p class="personal-code-hint" data-i18n="personal_code_hint"></p>
</div>

<!-- Activity tiles grid -->
<div id="activity-tiles" class="tiles-grid">
  <!-- 4 tiles rendered by JS -->
</div>

<button id="btn-leave" data-i18n="leave"></button>
```

`renderStudentHome()` in `student.js`:
- Fills identity card from `session`.
- Calls `GET /student/activities`, renders 4 tiles.
- Each tile: activity number, NL/EN title, status badge (not started / in progress / locked).
- Clicking a tile calls `openActivity(activity)`.

**Emoji map** (in `student.js`):
```js
const ANIMAL_EMOJI = {
  "Aardvark": "🐜", "Albatross": "🐦", "Axolotl": "🦎", ...
};
```
(Full 60-name map — use best-fit emoji for each.)

---

### Phase 5 — Frontend: Activity View

#### Paired activities (3 & 4) — player role

Each student enters only their own data from their own browser. For activities 3 & 4, a role
selector is shown before the table: "Ik ben Speler 1 / I am Player 1" vs "Ik ben Speler 2 / I am
Player 2". The selected role is stored in module state and sent as the `player` field in every PUT
request. The table itself is single-column (the student's own count). No read-only partner column
in M3 — the combined view is a graph concern (M4/M5).

Activities 1 & 2 always use `player=1`; no selector shown.

Add `#view-student-activity` to `index.html`:

```html
<div id="view-student-activity" class="hidden">
  <button id="btn-back-to-home" data-i18n="back"></button>
  <h2 id="activity-title"></h2>
  <p id="activity-description"></p>

  <!-- Lock banner (hidden when unlocked) -->
  <div id="lock-banner" class="lock-banner hidden">
    <span data-i18n="locked_notice"></span>
    <button id="btn-request-unlock" data-i18n="request_unlock"></button>
  </div>

  <!-- Measurement table -->
  <div class="table-wrapper">
    <table id="measurement-table">
      <thead>
        <tr>
          <th data-i18n="col_roll"></th>
          <th data-i18n="col_dice"></th>
        </tr>
      </thead>
      <tbody id="measurement-tbody"></tbody>
    </table>
    <button id="btn-add-row" data-i18n="add_row">+</button>
  </div>
</div>
```

`openActivity(activity)` in `student.js`:
1. Calls `GET /student/activities/{activity}`.
2. Renders activity title + description from i18n.
3. Shows/hides lock banner based on `is_locked`.
4. Renders table rows from `measurements`; pads to at least 12 empty rows.
5. `showView("student-activity")`.

**Auto-extend rows:**
The table always starts with at least 12 rows (handles Player 2 in activities 3 & 4, whose first
entries are 0 but the experiment is not yet over). After that, a new empty row is appended
automatically whenever a value is entered in the last row, *unless* that value is 0 — entering 0
in any row at position ≥ 12 signals the end of the experiment and stops auto-extend. The "+"
button is still present to manually add a row at any point (useful if a student needs to correct
the end of their series).

**Debounced save:**
- Each `<input>` cell fires `onDiceCountChange()` on `input` event.
- On change in the last row: run auto-extend logic first, then schedule save.
- Debounce 800 ms, then `PUT /student/activities/{activity}/measurements` with all rows that
  have a value (skip trailing empty rows).
- Show a small "Opgeslagen" / "Saved" indicator for 2 s after success.
- On error: show "Opslaan mislukt" / "Save failed" indicator.

**"+" button:** appends a new row with the next roll number; triggers a save.

**Lock banner:**
- Visible when `is_locked=True`.
- All inputs get `disabled` attribute.
- "Request unlock" calls `POST /student/activities/{activity}/request-unlock`; on success, button
  changes to disabled "Verzoek verzonden" / "Request sent".

---

### Phase 6 — i18n Keys

Add to `i18n.js` (both `nl` and `en`):

```
personal_code_label     "Jouw code:" / "Your code:"
personal_code_hint      "Schrijf deze code op om later verder te gaan of samen te werken."
                        "Write this code down to continue later or work with a partner."
copy                    "Kopieer" / "Copy"
copied                  "Gekopieerd!" / "Copied!"
leave                   "Verlaten" / "Leave"
back                    "Terug" / "Back"
activity_1_title        "Activiteit 1 — Blauw" / "Activity 1 — Blue"
activity_2_title        "Activiteit 2 — Wit" / "Activity 2 — White"
activity_3_title        "Activiteit 3 — Samen blauw" / "Activity 3 — Paired blue"
activity_4_title        "Activiteit 4 — Samen wit" / "Activity 4 — Paired white"
activity_1_desc         NL: "Begin met 100 dobbelstenen. Gooi alle dobbelstenen. Verwijder alle
                            dobbelstenen met een blauwe kant naar boven. Tel de overblijvende
                            dobbelstenen en noteer het aantal. Herhaal dit totdat er geen
                            dobbelstenen meer over zijn."
                        EN: "Start with 100 dice. Roll all dice. Remove every die showing a blue
                            face on top. Count the remaining dice and record the number. Repeat
                            until no dice remain."

activity_2_desc         NL: "Begin met 100 dobbelstenen. Gooi alle dobbelstenen. Verwijder alle
                            dobbelstenen met een witte kant naar boven. Tel de overblijvende
                            dobbelstenen en noteer het aantal. Herhaal dit totdat er geen
                            dobbelstenen meer over zijn."
                        EN: "Start with 100 dice. Roll all dice. Remove every die showing a white
                            face on top. Count the remaining dice and record the number. Repeat
                            until no dice remain."

activity_3_desc         NL (Player 1): "Jij begint met alle 100 dobbelstenen. Gooi al jouw
                            dobbelstenen. Geef alle dobbelstenen met een blauwe kant naar boven aan
                            Speler 2. Tel jouw overblijvende dobbelstenen en noteer het aantal
                            vóór elke worp. Herhaal dit totdat jij geen dobbelstenen meer hebt."
                        NL (Player 2): "Jij begint met nul dobbelstenen. Na elke worp van Speler 1
                            ontvang jij de blauwe dobbelstenen. Gooi daarna jouw dobbelstenen en
                            verwijder alle dobbelstenen met een witte kant naar boven. Tel jouw
                            dobbelstenen en noteer het aantal vóór elke worp."
                        EN (Player 1): "You start with all 100 dice. Roll all your dice. Give every
                            die showing blue on top to Player 2. Count your remaining dice and
                            record the number before each roll. Repeat until you have no dice left."
                        EN (Player 2): "You start with zero dice. After each of Player 1's rolls you
                            receive the blue dice. Then roll your dice and remove every die showing
                            white on top. Count your dice and record the number before each roll."

activity_4_desc         NL (Player 1): "Jij begint met alle 100 dobbelstenen. Gooi al jouw
                            dobbelstenen. Geef alle dobbelstenen met een witte kant naar boven aan
                            Speler 2. Tel jouw overblijvende dobbelstenen en noteer het aantal
                            vóór elke worp. Herhaal dit totdat jij geen dobbelstenen meer hebt."
                        NL (Player 2): "Jij begint met nul dobbelstenen. Na elke worp van Speler 1
                            ontvang jij de witte dobbelstenen. Gooi daarna jouw dobbelstenen en
                            verwijder alle dobbelstenen met een blauwe kant naar boven. Tel jouw
                            dobbelstenen en noteer het aantal vóór elke worp."
                        EN (Player 1): "You start with all 100 dice. Roll all your dice. Give every
                            die showing white on top to Player 2. Count your remaining dice and
                            record the number before each roll. Repeat until you have no dice left."
                        EN (Player 2): "You start with zero dice. After each of Player 1's rolls you
                            receive the white dice. Then roll your dice and remove every die showing
                            blue on top. Count your dice and record the number before each roll."
status_not_started      "Nog niet begonnen" / "Not started"
status_in_progress      "Bezig" / "In progress"
status_locked           "Vergrendeld" / "Locked"
Note: activity_3_desc and activity_4_desc use separate keys per player role:
  `activity_3_desc_p1` / `activity_3_desc_p2` etc. The role selector sets a module variable
  `currentPlayer` (1 or 2) which determines which description key is rendered.

choose_role             "Wat is jouw rol?" / "What is your role?"
role_player1            "Ik ben Speler 1" / "I am Player 1"
role_player2            "Ik ben Speler 2" / "I am Player 2"
col_roll                "Worp" / "Roll"
col_dice                "Dobbelstenen" / "Dice count"
col_player1             "Speler 1" / "Player 1"
col_player2             "Speler 2" / "Player 2"
add_row                 "+ Rij toevoegen" / "+ Add row"
saved                   "Opgeslagen ✓" / "Saved ✓"
save_failed             "Opslaan mislukt" / "Save failed"
locked_notice           "Je gegevens zijn vergrendeld door de docent."
                        "Your data has been locked by the teacher."
request_unlock          "Ontgrendelverzoek sturen" / "Request unlock"
unlock_requested        "Verzoek verzonden" / "Request sent"
```

---

### Phase 7 — CSS

New rules to add to `style.css`:

- `.animal-emoji` — large emoji display (font-size ~3rem)
- `.animal-name` — animal name, prominent
- `.personal-code-row` — flex row with label + `<code>` + copy button
- `.tiles-grid` — 2×2 CSS grid, responsive (single column on narrow screens)
- `.activity-tile` — card with hover state, status badge in corner
- `.status-badge` — small pill; colour variants: `.not-started` (grey), `.in-progress` (blue), `.locked` (orange)
- `.lock-banner` — full-width warning bar with amber background
- `.table-wrapper` — scrollable container for measurement table
- `#measurement-table` — clean bordered table; inputs borderless inside cells
- `.save-indicator` — small transient text, fades out after 2 s

---

## Files Changed / Created

| File | Action |
|---|---|
| `src/dice_applet/dependencies.py` | **new** — `require_student` |
| `src/dice_applet/routers/student.py` | update join + reconnect (set cookie; update response) |
| `src/dice_applet/routers/student_data.py` | **new** — activities + measurements endpoints |
| `src/dice_applet/services/student_data.py` | **new** — DB logic for datasets + measurements |
| `src/dice_applet/schemas/student.py` | add `StudentMe`, `ReconnectResponse`, `ActivityStatus`, `DatasetDetail`, `MeasurementOut`, `MeasurementIn` |
| `src/dice_applet/main.py` | register `student_data` router |
| `frontend/index.html` | replace student-home stub; add student-activity view |
| `frontend/js/student.js` | full rewrite — session state, real fetches, render functions |
| `frontend/js/app.js` | add page-load session restore; back-button handler |
| `frontend/js/i18n.js` | add ~20 new keys (NL + EN) |
| `frontend/css/style.css` | add ~8 new rule groups |

No Alembic migration needed.

---

## Out of Scope for M3

- Teacher dashboard (M5)
- Class aggregate graph (M4)
- Approve / unapprove student datasets (M6)
- SVG animal icons — emoji placeholder used instead
- QR codes (M5)
- WebSocket live updates (M4/M5)
- IP-recognition shortcut (deferred from M2)

---

## Exit Criteria Checklist

- [ ] `POST /student/join` sets `student_session` cookie
- [ ] `POST /student/reconnect` sets cookie + returns `personal_code` + `classroom_name`
- [ ] `GET /student/me` returns identity from cookie (401 without cookie)
- [ ] `GET /student/activities` returns 4 activity status objects (creates datasets lazily)
- [ ] `GET /student/activities/{activity}` returns dataset + measurements
- [ ] `PUT /student/activities/{activity}/measurements` bulk-replaces measurements; returns 403 if locked
- [ ] `POST /student/activities/{activity}/request-unlock` sets flag; 400 if not locked
- [ ] Page-load session restore: visiting the page while cookie is valid skips landing
- [ ] Identity card shows animal emoji + name + personal code with copy button
- [ ] 4 activity tiles shown with correct status badges
- [ ] Activity view shows task description (NL + EN), measurement table (≥12 rows on load)
- [ ] Table auto-extends when a non-zero value is entered in the last row
- [ ] Table stops auto-extending when 0 is entered at row ≥ 12 (end of experiment signal)
- [ ] Player 2 in activities 3 & 4 always sees at least 12 rows on open (initial zeros don't stop extend)
- [ ] Inputs are disabled when dataset is locked; lock banner visible
- [ ] "Request unlock" button sends request; button changes to "Verzoek verzonden"
- [ ] Cell changes trigger debounced save; success/fail indicator shown
- [ ] "+" adds a row and saves
- [ ] Page reload + reconnect with personal code restores table data
- [ ] Language toggle works on all new UI text
- [ ] Activity 1 full flow works end-to-end
