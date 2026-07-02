# Milestone 4 Plan — Interactive Decay Graphs (p5.js)

Created: 2026-07-02
Status: planning

---

## Goal

Build a reusable p5.js graph component for decay curves: single-line (Activities 1 & 2)
and dual-line (Activities 3 & 4), with dot + smooth-curve rendering, NL/EN axis labels,
and a hover/touch crosshair with coordinate readout.

**Exit criteria (per `ROADMAP.md`):** Graph renders correctly from mock data for all
four activity types with working hover.

---

## Key Design Decision — Real Data Deferred to Milestone 4.1

While planning, a real backend gap surfaced: `GET /student/activities/{activity}`
(`src/dice_applet/routers/student_data.py:59`) scopes strictly to the requesting
student's own `StudentDataset` row (`UniqueConstraint(student_id, activity)` in
`db/models.py`). There is no link between two paired students' data — a student can
never see their partner's real measurements today.

The fix is a real feature (a shared workspace two students join via personal code, with
a role toggle), not a quick patch — scoped separately as **Milestone 4.1** (see
`ROADMAP.md`). M4 itself stays scoped to the roadmap's own exit criteria: mock data for
all four activities.

One piece of real wiring *is* possible without touching the backend or M4.1: Activities
1 & 2 are single-student, and the measurement table already fires input events in
`student.js` — so the graph reflects live keystrokes for those two activities by reading
the same on-screen inputs (no network calls). Activities 3 & 4 stay on mock dual-line
data (both lines shown regardless of which role the viewer picked) until M4.1 exists.

---

## Mock Data (fixture)

```js
{
  act1: [100,62,38,23,17,14,10,7,5,3,1,1,1,1,1,0],
  act2: [100,83,66,49,38,27,21,18,14,10,7,5,4,3,3,3,2,1,1,1,1,1,0],
  act3: {
    p1: [100,62,38,23,17,14,10,7,5,3,1,1,1,1,1,0,0,0,0,0,0,0,0,0],
    p2: [0,38,55,64,62,55,56,48,46,40,37,25,21,15,12,11,10,8,7,7,5,4,2,0]
  },
  act4: {
    p1: [100,83,66,49,38,27,21,18,14,10,7,5,4,3,3,3,2,1,1,1,1,1,0,0,0,0,0],
    p2: [0,17,31,32,34,32,30,22,18,16,13,10,7,5,4,1,3,1,1,0,0,0,1,1,1,1,0]
  }
}
```
Index = roll number (x, roll 0 = initial 100-dice state), value = active dice count (y).

---

## Design Decisions

1. **p5.js via CDN `<script>` tag** — matches the project's existing no-build-step
   approach (`config.js`, `i18n.js`, etc. are all plain includes).
2. **Instance-mode p5.js**, one instance per graph, created/destroyed manually tied to
   the existing `showView()` show/hide points in `student.js`/`app.js` — there is no
   framework lifecycle or resize system anywhere in this codebase.
3. **`noLoop()` + manual `redraw()`**, not the default 60fps draw loop — static chart,
   not an animation; matters for battery/CPU on a page open through a class period.
4. **Curve rendering: monotone cubic Hermite (Steffen's method) → `bezierVertex()`, not
   `curveVertex()`/Catmull-Rom.** Verified against the actual fixture: `act3.p2`'s
   `...,62,55,56,48,...` segment is a real local wiggle that Catmull-Rom's automatic
   tangents would overshoot on — a false bump on a measurement chart. Steffen's method
   guarantees each segment stays within `[min(Pi,Pi+1), max(Pi,Pi+1)]`.
5. **Hover snaps to the nearest data index — no curve evaluation needed.** A dot already
   exists at every measured point, so the crosshair intersection is just that dot's
   already-computed pixel position.
6. **Touch support is in scope, not optional** — the page layout is mobile-first,
   single-column, capped at 480px, and will be used on phones/tablets in a classroom.
   `touchMoved`/`touchEnded` mirror `mouseMoved`/`mouseOut`; `preventDefault()` only
   while inside the plot area so page scroll still works everywhere else.
7. **y-axis domain fixed from `options.totalDice` (default 100)**, not derived from
   `Math.max(data)` — keeps scale stable across `update()` calls and across activities;
   incidentally future-proofs the backlog item "configurable number of starting dice."
8. **Colors:** `--color-primary` (`#2563eb`) for the single line / Player 1. Player 2
   gets a new accent, `#f59e0b` (amber) — kept distinct from `--color-error` red, which
   stays reserved for the crosshair only.

---

## Component API — `frontend/js/graph.js`

```js
function createDecayGraph(containerEl, options) {
  // options: { lines: [{ data: number[], color: string, key: string }], lang: 'nl'|'en', totalDice: 100 }
  // returns:
  //   destroy()                        -> instance.remove()
  //   resize()                         -> recompute width from containerEl.clientWidth, resizeCanvas, redraw
  //   update(newLinesData, { lang })   -> swap closure data (+lang if passed), redraw
}
```
- `destroy()` → `p.remove()`.
- `resize()`/creation **must only be called while `containerEl` is visible** — this
  codebase's `.hidden { display: none !important; }` means `clientWidth` reads `0`
  otherwise. Precondition of the API, not detectable reliably by the component itself.
- `update()` carries an optional `lang` in its second argument, since axis labels are
  canvas-drawn text invisible to the existing DOM-scanning `setLang()`.
- Defensive against mismatched line lengths — compute `n = max(line lengths)`, skip
  drawing points beyond a given line's own length.

### Hover math

```js
function pixelXToIndex(px, plotX, plotW, n) {
  const t = clamp((px - plotX) / plotW, 0, 1);
  return Math.round(t * (n - 1));
}
```
No curve-parameter inversion needed — snap to nearest index, then read that line's
already-computed pixel position for the dot.

### Curve tangents (Steffen's method, one pass)

```js
function monotoneTangents(ys) {
  const n = ys.length, m = new Array(n);
  const s = i => ys[i+1] - ys[i];
  m[0] = s(0);
  m[n-1] = s(n-2);
  for (let i = 1; i < n - 1; i++) {
    const sPrev = s(i-1), sNext = s(i);
    if (sPrev === 0 || sNext === 0 || (sPrev > 0) !== (sNext > 0)) {
      m[i] = 0; // local extremum -> flat tangent, no overshoot
    } else {
      const avg = (sPrev + sNext) / 2;
      const sign = Math.sign(sPrev);
      m[i] = sign * Math.min(Math.abs(avg), 2 * Math.abs(sPrev), 2 * Math.abs(sNext));
    }
  }
  return m;
}
```
Convert tangents to Bezier control points per segment. Tangents are computed with an
implicit dx of 1 index-step, so only the **x** offset uses the real pixel spacing —
the y offset is just `tangent / 3` (multiplying by pixel `dx` again double-counts the
spacing and blows up the curve — caught during manual verification, see exit checklist):
`cp1 = (p_i.x + dx/3, p_i.y + tangent_i/3)`, `cp2 = (p_{i+1}.x - dx/3, p_{i+1}.y - tangent_{i+1}/3)`.
Draw with `beginShape()`/`vertex()`/`bezierVertex()`.

---

## Files Changed / Created

| File | Action |
|---|---|
| `frontend/index.html` | Add p5.js CDN `<script>` tag; add `#activity-graph` card (with legend for dual-line activities) inside `#activity-content`, above the measurement table |
| `frontend/js/graph.js` | **New** — `createDecayGraph()` component |
| `frontend/js/graph-mock-data.js` | **New** — fixture data above |
| `frontend/js/student.js` | Create/destroy graph in `openActivity`/`_loadAndRenderActivity`; feed mock data for all 4 activities; live-update for Activities 1 & 2 from `_onCellChange` using on-screen values |
| `frontend/js/app.js` | Destroy graph handle in `btn-back-to-home` handler; `window.resize` listener scoped to visible activity view; language-toggle hook |
| `frontend/js/i18n.js` | Add `graph_axis_x` ("Worp"/"Throw"), `graph_axis_y` ("Actieve dobbelstenen"/"Active dice") — reuse existing `col_player1`/`col_player2` for the dual-line legend |
| `frontend/css/style.css` | `.graph-card`, `#activity-graph` sizing, `.graph-legend` swatch+label styling |
| `docs/claude/ROADMAP.md` | Note on M4's live-update checklist item; new Milestone 4.1 section |

No Alembic migration, no backend changes.

---

## Out of Scope for M4

- Shared workspace / partner join flow, real dual-line data (→ M4.1)
- Teacher dashboard aggregate graph (M5/M6) — `graph.js` should stay generic enough to
  be reused there later, but no teacher-side work now
- CSV export, print view (backlog, unrelated)

---

## Exit Criteria Checklist

- [ ] p5.js loaded via CDN, no console errors
- [x] `createDecayGraph()` renders single-line mock data (Activities 1 & 2) with dots +
  smooth curve
- [x] Dual-line mock data (Activities 3 & 4) renders both lines simultaneously, correct
  colors, legend visible
- [x] Curve does not visibly overshoot at `act3.p2`'s `62,55,56,48` wiggle
- [x] Hover (mouse) shows red crosshair + coordinate label, snapped to nearest point
- [ ] Touch (drag) shows the same crosshair behavior on a touch-emulated viewport —
  **not yet verified**, browser automation only exercised mouse events
- [x] Activities 1 & 2: graph updates live as the student types in the table (no
  network dependency for the graph update itself)
- [ ] Resize / hide-then-show cycle leaves no stale or blank canvas — **not yet
  verified**, worth a manual pass
- [x] Language toggle updates axis labels and legend text while an activity view is open
- [x] `pytest` still passes unchanged (no backend touched) — 21/21 passing

Verified 2026-07-02 via Playwright against a headless Chromium (screenshots + console
check), driving the real bootstrapped classroom flow. Full details in
`docs/changelog/v0.4.0.md`.
