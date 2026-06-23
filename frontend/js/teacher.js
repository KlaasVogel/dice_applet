function openTeacherModal() {
  document.getElementById("modal-teacher").classList.remove("hidden");
  document.getElementById("input-teacher-password").focus();
}

function closeTeacherModal() {
  document.getElementById("modal-teacher").classList.add("hidden");
  document.getElementById("input-teacher-password").value = "";
  document.getElementById("teacher-error").classList.add("hidden");
}

async function submitTeacherLogin() {
  const password = document.getElementById("input-teacher-password").value;
  document.getElementById("teacher-error").classList.add("hidden");

  try {
    const res = await fetch(`${API_BASE}/teacher/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ password }),
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
