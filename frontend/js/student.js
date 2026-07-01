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

function renderStudentHome() {
  // Phase 4 will render the identity card and activity tiles here.
  showView("student-home");
}
