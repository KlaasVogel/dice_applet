document.addEventListener("DOMContentLoaded", () => {
  // Language toggle
  document.getElementById("btn-nl").addEventListener("click", () => { setLang("nl"); _refreshGraphLang(); });
  document.getElementById("btn-en").addEventListener("click", () => { setLang("en"); _refreshGraphLang(); });

  // Teacher modal
  document.getElementById("btn-teacher").addEventListener("click", openTeacherModal);
  document.getElementById("btn-teacher-cancel").addEventListener("click", closeTeacherModal);
  document.getElementById("btn-teacher-submit").addEventListener("click", submitTeacherLogin);
  document.getElementById("tab-btn-teacher").addEventListener("click", () => _switchTab("teacher"));
  document.getElementById("tab-btn-admin").addEventListener("click", () => _switchTab("admin"));
  document.getElementById("input-teacher-password").addEventListener("keydown", (e) => {
    if (e.key === "Enter") submitTeacherLogin();
  });
  document.getElementById("input-teacher-email").addEventListener("keydown", (e) => {
    if (e.key === "Enter") document.getElementById("input-teacher-password").focus();
  });
  document.getElementById("modal-teacher").addEventListener("click", (e) => {
    if (e.target === e.currentTarget) closeTeacherModal();
  });
  document.getElementById("btn-goto-register").addEventListener("click", (e) => {
    e.preventDefault();
    openRegisterView();
  });

  // Registration view
  document.getElementById("btn-reg-cancel").addEventListener("click", () => showView("landing"));
  document.getElementById("btn-reg-submit").addEventListener("click", submitRegistration);
  document.getElementById("radio-new-school").addEventListener("change", () => _showSchoolField("new"));
  document.getElementById("radio-existing-school").addEventListener("change", () => _showSchoolField("existing"));

  // Student join
  document.getElementById("btn-join-classroom").addEventListener("click", joinWithClassroomCode);
  document.getElementById("btn-join-personal").addEventListener("click", joinWithPersonalCode);
  document.getElementById("input-classroom-code").addEventListener("keydown", (e) => {
    if (e.key === "Enter") joinWithClassroomCode();
  });
  document.getElementById("input-personal-code").addEventListener("keydown", (e) => {
    if (e.key === "Enter") joinWithPersonalCode();
  });

  // Student home navigation
  document.getElementById("btn-leave").addEventListener("click", () => showView("landing"));

  // Activity view
  document.getElementById("btn-back-to-home").addEventListener("click", () => {
    _cancelPendingSave();
    if (activityState.graph) {
      activityState.graph.destroy();
      activityState.graph = null;
    }
    renderStudentHome();
  });
  document.getElementById("btn-role-1").addEventListener("click", () => _selectRole(1));
  document.getElementById("btn-role-2").addEventListener("click", () => _selectRole(2));
  document.getElementById("btn-request-unlock").addEventListener("click", _requestUnlock);
  document.getElementById("btn-add-row").addEventListener("click", () => {
    const tbody = document.getElementById("measurement-tbody");
    _appendRow(tbody.querySelectorAll("tr").length + 1, null, activityState.isLocked);
    if (activityState.activity <= 2 && activityState.graph) {
      activityState.graph.update(_graphLines(), { axisLabels: _axisLabels() });
    }
    _scheduleSave();
  });

  document.getElementById("btn-logout").addEventListener("click", submitLogout);

  // Resize the graph canvas on viewport changes, but only while its view is visible —
  // resizing while hidden would read a container width of 0.
  window.addEventListener("resize", () => {
    if (activityState.graph && !document.getElementById("view-student-activity").classList.contains("hidden")) {
      activityState.graph.resize();
    }
  });

  // Init: restore student session if cookie is still valid, otherwise show landing
  setLang("nl");
  restoreStudentSession().then((restored) => {
    if (!restored) showView("landing");
  });
});

function _refreshGraphLang() {
  if (activityState.graph && !document.getElementById("view-student-activity").classList.contains("hidden")) {
    activityState.graph.update(_graphLines(), { axisLabels: _axisLabels() });
  }
}
