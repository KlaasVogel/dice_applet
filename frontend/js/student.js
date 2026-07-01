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

// ── Activity view (Phase 5) ────────────────────────────────────────────────────

function openActivity(activity) {
  // Phase 5 will implement this.
}
