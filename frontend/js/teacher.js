let _activeTab = "teacher";

function openTeacherModal() {
  document.getElementById("modal-teacher").classList.remove("hidden");
  _switchTab("teacher");
  document.getElementById("input-teacher-email").focus();
}

function closeTeacherModal() {
  document.getElementById("modal-teacher").classList.add("hidden");
  document.getElementById("input-teacher-email").value = "";
  document.getElementById("input-teacher-password").value = "";
  document.getElementById("teacher-error").classList.add("hidden");
}

function _switchTab(tab) {
  _activeTab = tab;
  const isTeacher = tab === "teacher";
  document.getElementById("tab-btn-teacher").classList.toggle("active", isTeacher);
  document.getElementById("tab-btn-admin").classList.toggle("active", !isTeacher);
  document.getElementById("tab-btn-teacher").setAttribute("aria-selected", String(isTeacher));
  document.getElementById("tab-btn-admin").setAttribute("aria-selected", String(!isTeacher));
  document.getElementById("tab-teacher-fields").classList.toggle("hidden", !isTeacher);
  document.getElementById("register-link").classList.toggle("hidden", !isTeacher);
  if (isTeacher) {
    document.getElementById("input-teacher-email").focus();
  } else {
    document.getElementById("input-teacher-password").focus();
  }
}

async function submitTeacherLogin() {
  const password = document.getElementById("input-teacher-password").value;
  const email = _activeTab === "teacher" ? document.getElementById("input-teacher-email").value.trim() : "";
  document.getElementById("teacher-error").classList.add("hidden");

  try {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
      credentials: "include",
    });
    if (res.ok) {
      closeTeacherModal();
      showView("teacher");
    } else {
      document.getElementById("teacher-error").classList.remove("hidden");
    }
  } catch {
    document.getElementById("teacher-error").classList.remove("hidden");
  }
}

async function submitLogout() {
  try {
    await fetch(`${API_BASE}/auth/logout`, { method: "POST", credentials: "include" });
  } finally {
    showView("landing");
  }
}

async function openRegisterView() {
  closeTeacherModal();
  document.getElementById("register-error").classList.add("hidden");
  document.getElementById("register-success").classList.add("hidden");
  document.getElementById("input-reg-email").value = "";
  document.getElementById("input-reg-password").value = "";
  document.getElementById("input-school-name").value = "";
  document.getElementById("radio-new-school").checked = true;
  _showSchoolField("new");
  await _loadSchools();
  showView("register");
}

async function _loadSchools() {
  try {
    const res = await fetch(`${API_BASE}/admin/schools`, { credentials: "include" });
    if (!res.ok) return;
    const schools = await res.json();
    const sel = document.getElementById("select-school");
    sel.innerHTML = "";
    schools
      .filter((s) => s.is_active)
      .forEach((s) => {
        const opt = document.createElement("option");
        opt.value = s.id;
        opt.textContent = s.name;
        sel.appendChild(opt);
      });
  } catch {
    // Schools list unavailable — user can still create a new school
  }
}

function _showSchoolField(choice) {
  document.getElementById("field-new-school").classList.toggle("hidden", choice !== "new");
  document.getElementById("field-existing-school").classList.toggle("hidden", choice !== "existing");
}

async function submitRegistration() {
  const email = document.getElementById("input-reg-email").value.trim();
  const password = document.getElementById("input-reg-password").value;
  const choice = document.querySelector('input[name="school-choice"]:checked').value;
  const errEl = document.getElementById("register-error");
  const successEl = document.getElementById("register-success");

  errEl.classList.add("hidden");
  successEl.classList.add("hidden");

  const body = { email, password };
  if (choice === "new") {
    body.new_school_name = document.getElementById("input-school-name").value.trim();
  } else {
    const sel = document.getElementById("select-school");
    body.school_id = parseInt(sel.value, 10);
  }

  try {
    const res = await fetch(`${API_BASE}/auth/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
      credentials: "include",
    });
    if (res.status === 202) {
      successEl.classList.remove("hidden");
      document.getElementById("btn-reg-submit").disabled = true;
    } else {
      const data = await res.json().catch(() => ({}));
      errEl.textContent = data.detail || `Error ${res.status}`;
      errEl.classList.remove("hidden");
    }
  } catch {
    errEl.textContent = "Verbindingsfout — probeer opnieuw.";
    errEl.classList.remove("hidden");
  }
}
