// ── Session state ─────────────────────────────────────────────────────────────

const session = {
  animalName: null,
  personalCode: null,
  classroomId: null,
  classroomName: null,
};

function _storeSession(data) {
  session.animalName = data.animal_name;
  session.personalCode = data.personal_code;
  session.classroomId = data.classroom_id;
  session.classroomName = data.classroom_name;
}

// ── Animal emoji map ───────────────────────────────────────────────────────────

const ANIMAL_EMOJI = {
  Albatross:  "🐦",
  Axolotl:    "🦎",
  Badger:     "🦡",
  Barracuda:  "🐟",
  Bison:      "🦬",
  Blobfish:   "🐡",
  Capybara:   "🐭",
  Chameleon:  "🦎",
  Cheetah:    "🐆",
  Chinchilla: "🐭",
  Chipmunk:   "🐿️",
  Condor:     "🦅",
  Coyote:     "🐺",
  Dingo:      "🐕",
  Dolphin:    "🐬",
  Echidna:    "🦔",
  Elephant:   "🐘",
  Flamingo:   "🦩",
  Fox:        "🦊",
  Gecko:      "🦎",
  Giraffe:    "🦒",
  Gorilla:    "🦍",
  Hamster:    "🐹",
  Hedgehog:   "🦔",
  Hyena:      "🐺",
  Iguana:     "🦎",
  Jaguar:     "🐆",
  Jellyfish:  "🪼",
  Kangaroo:   "🦘",
  Kiwi:       "🐦",
  Koala:      "🐨",
  Lemur:      "🐒",
  Leopard:    "🐆",
  Llama:      "🦙",
  Lynx:       "🐱",
  Manatee:    "🐋",
  Meerkat:    "🦡",
  Mongoose:   "🐀",
  Narwhal:    "🦄",
  Numbat:     "🐭",
  Ocelot:     "🐆",
  Octopus:    "🐙",
  Okapi:      "🦒",
  Orca:       "🐋",
  Ostrich:    "🦚",
  Otter:      "🦦",
  Pangolin:   "🦔",
  Parrot:     "🦜",
  Porcupine:  "🦔",
  Quokka:     "🦘",
  Raccoon:    "🦝",
  Rhino:      "🦏",
  Salamander: "🦎",
  Sloth:      "🦥",
  Tapir:      "🐗",
  Tarantula:  "🕷️",
  Toucan:     "🦜",
  Walrus:     "🦭",
  Wombat:     "🦡",
  Zebrafish:  "🐟",
};

// ── Landing: join / reconnect ──────────────────────────────────────────────────

function _showError(elementId, i18nKey) {
  const el = document.getElementById(elementId);
  el.textContent = TRANSLATIONS[currentLang][i18nKey] || i18nKey;
  el.classList.remove("hidden");
}

function _clearErrors() {
  ["join-classroom-error", "join-personal-error"].forEach((id) => {
    document.getElementById(id).classList.add("hidden");
  });
}

async function joinWithClassroomCode() {
  const code = document.getElementById("input-classroom-code").value.trim().toUpperCase();
  if (!code) return;
  _clearErrors();
  try {
    const res = await fetch(`${API_BASE}/student/join`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify({ classroom_code: code }),
    });
    if (res.status === 404) { _showError("join-classroom-error", "error_join_classroom"); return; }
    if (res.status === 409) { _showError("join-classroom-error", "error_join_full"); return; }
    if (!res.ok) { _showError("join-classroom-error", "error_network"); return; }
    _storeSession(await res.json());
    renderStudentHome();
  } catch {
    _showError("join-classroom-error", "error_network");
  }
}

async function joinWithPersonalCode() {
  const code = document.getElementById("input-personal-code").value.trim().toUpperCase();
  if (!code) return;
  _clearErrors();
  try {
    const res = await fetch(`${API_BASE}/student/reconnect`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify({ personal_code: code }),
    });
    if (res.status === 404) { _showError("join-personal-error", "error_join_personal"); return; }
    if (!res.ok) { _showError("join-personal-error", "error_network"); return; }
    _storeSession(await res.json());
    renderStudentHome();
  } catch {
    _showError("join-personal-error", "error_network");
  }
}

async function restoreStudentSession() {
  try {
    const res = await fetch(`${API_BASE}/student/me`, { credentials: "include" });
    if (!res.ok) return false;
    _storeSession(await res.json());
    renderStudentHome();
    return true;
  } catch {
    return false;
  }
}

// ── Student home ───────────────────────────────────────────────────────────────

async function renderStudentHome() {
  document.getElementById("animal-emoji").textContent = ANIMAL_EMOJI[session.animalName] || "🐾";
  document.getElementById("animal-name").textContent = session.animalName;
  document.getElementById("personal-code-display").textContent = session.personalCode;
  document.getElementById("btn-copy-code").onclick = _copyPersonalCode;

  showView("student-home");

  try {
    const res = await fetch(`${API_BASE}/student/activities`, { credentials: "include" });
    if (res.ok) _renderActivityTiles(await res.json());
  } catch {
    // tiles remain empty on network error
  }
}

function _copyPersonalCode() {
  navigator.clipboard.writeText(session.personalCode).then(() => {
    const btn = document.getElementById("btn-copy-code");
    btn.textContent = TRANSLATIONS[currentLang].copied;
    setTimeout(() => { btn.textContent = TRANSLATIONS[currentLang].copy; }, 2000);
  });
}

function _renderActivityTiles(activities) {
  const container = document.getElementById("activity-tiles");
  container.innerHTML = "";
  activities.forEach((a) => {
    const statusKey = a.is_locked ? "status_locked"
      : a.measurement_count > 0 ? "status_in_progress"
      : "status_not_started";
    const statusClass = a.is_locked ? "locked"
      : a.measurement_count > 0 ? "in-progress"
      : "not-started";

    const tile = document.createElement("button");
    tile.className = "activity-tile";
    tile.innerHTML = `
      <div class="tile-header">
        <span class="tile-number">${a.activity}</span>
        <span class="status-badge ${statusClass}">${TRANSLATIONS[currentLang][statusKey]}</span>
      </div>
      <div class="tile-title">${TRANSLATIONS[currentLang][`activity_${a.activity}_title`]}</div>
    `;
    tile.addEventListener("click", () => openActivity(a.activity));
    container.appendChild(tile);
  });
}

// ── Activity view ──────────────────────────────────────────────────────────────

const activityState = {
  activity: null,
  player: null,
  isLocked: false,
  saveTimer: null,
};

const MIN_ROWS = 12;

async function openActivity(activity) {
  activityState.activity = activity;
  activityState.player = null;
  _cancelPendingSave();

  document.getElementById("activity-title").textContent =
    TRANSLATIONS[currentLang][`activity_${activity}_title`];
  document.getElementById("activity-content").classList.add("hidden");
  document.getElementById("save-indicator").classList.add("hidden");

  if (activity >= 3) {
    document.getElementById("role-selector").classList.remove("hidden");
    showView("student-activity");
  } else {
    activityState.player = 1;
    document.getElementById("role-selector").classList.add("hidden");
    await _loadAndRenderActivity();
    showView("student-activity");
  }
}

async function _selectRole(player) {
  activityState.player = player;
  document.getElementById("role-selector").classList.add("hidden");
  await _loadAndRenderActivity();
}

async function _loadAndRenderActivity() {
  const { activity, player } = activityState;
  const descKey = activity >= 3
    ? `activity_${activity}_desc_p${player}`
    : `activity_${activity}_desc`;
  document.getElementById("activity-description").textContent =
    TRANSLATIONS[currentLang][descKey] || "";

  try {
    const res = await fetch(`${API_BASE}/student/activities/${activity}`, {
      credentials: "include",
    });
    if (!res.ok) return;
    const data = await res.json();

    activityState.isLocked = data.is_locked;

    // Lock banner
    document.getElementById("lock-banner").classList.toggle("hidden", !data.is_locked);
    const unlockBtn = document.getElementById("btn-request-unlock");
    if (data.unlock_requested) {
      unlockBtn.textContent = TRANSLATIONS[currentLang].unlock_requested;
      unlockBtn.disabled = true;
    } else {
      unlockBtn.disabled = false;
    }

    // Add-row button: hide when locked
    document.getElementById("btn-add-row").classList.toggle("hidden", data.is_locked);

    // Table
    const myMeasurements = data.measurements.filter((m) => m.player === player);
    _renderTable(myMeasurements, data.is_locked);

    document.getElementById("activity-content").classList.remove("hidden");
  } catch {
    // content stays hidden on error
  }
}

function _renderTable(measurements, isLocked) {
  const tbody = document.getElementById("measurement-tbody");
  tbody.innerHTML = "";
  const values = measurements.map((m) => m.dice_count);
  while (values.length < MIN_ROWS) values.push(null);
  values.forEach((val, i) => _appendRow(i + 1, val, isLocked));
}

function _appendRow(rollNumber, value, isLocked) {
  const tbody = document.getElementById("measurement-tbody");
  const tr = document.createElement("tr");
  tr.innerHTML = `
    <td class="col-roll">${rollNumber}</td>
    <td><input type="number" class="dice-input" min="0" value="${value !== null ? value : ""}" ${isLocked ? "disabled" : ""}></td>
  `;
  const input = tr.querySelector(".dice-input");
  input.addEventListener("input", () => _onCellChange(input, rollNumber));
  tbody.appendChild(tr);
}

function _onCellChange(input, rollNumber) {
  const tbody = document.getElementById("measurement-tbody");
  const totalRows = tbody.querySelectorAll("tr").length;

  if (rollNumber === totalRows) {
    const val = input.value === "" ? null : parseInt(input.value, 10);
    if (val !== null && (val > 0 || totalRows < MIN_ROWS)) {
      _appendRow(totalRows + 1, null, activityState.isLocked);
    }
  }
  _scheduleSave();
}

function _scheduleSave() {
  if (activityState.saveTimer) clearTimeout(activityState.saveTimer);
  activityState.saveTimer = setTimeout(_save, 800);
}

function _cancelPendingSave() {
  if (activityState.saveTimer) {
    clearTimeout(activityState.saveTimer);
    activityState.saveTimer = null;
  }
}

async function _save() {
  activityState.saveTimer = null;
  const rows = [];
  document.getElementById("measurement-tbody").querySelectorAll("tr").forEach((tr, i) => {
    const val = tr.querySelector(".dice-input")?.value;
    if (val !== "" && val !== undefined) {
      rows.push({ roll_number: i + 1, dice_count: parseInt(val, 10) });
    }
  });

  try {
    const res = await fetch(
      `${API_BASE}/student/activities/${activityState.activity}/measurements`,
      {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ player: activityState.player, rows }),
      }
    );
    _showSaveIndicator(res.ok ? "saved" : "save_failed");
  } catch {
    _showSaveIndicator("save_failed");
  }
}

function _showSaveIndicator(key) {
  const el = document.getElementById("save-indicator");
  el.textContent = TRANSLATIONS[currentLang][key];
  el.classList.remove("hidden", "save-ok", "save-err");
  el.classList.add(key === "saved" ? "save-ok" : "save-err");
  setTimeout(() => el.classList.add("hidden"), 2000);
}

async function _requestUnlock() {
  const btn = document.getElementById("btn-request-unlock");
  try {
    const res = await fetch(
      `${API_BASE}/student/activities/${activityState.activity}/request-unlock`,
      { method: "POST", credentials: "include" }
    );
    if (res.ok) {
      btn.textContent = TRANSLATIONS[currentLang].unlock_requested;
      btn.disabled = true;
    }
  } catch {
    // silently fail
  }
}
