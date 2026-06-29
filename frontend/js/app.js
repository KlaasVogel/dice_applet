document.addEventListener("DOMContentLoaded", () => {
  // Language toggle
  document.getElementById("btn-nl").addEventListener("click", () => setLang("nl"));
  document.getElementById("btn-en").addEventListener("click", () => setLang("en"));

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

  // Navigation
  document.getElementById("btn-leave").addEventListener("click", () => showView("landing"));
  document.getElementById("btn-logout").addEventListener("click", submitLogout);

  // Init
  setLang("nl");
  showView("landing");
});
