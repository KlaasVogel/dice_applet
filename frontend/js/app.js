document.addEventListener("DOMContentLoaded", () => {
  // Language toggle
  document.getElementById("btn-nl").addEventListener("click", () => setLang("nl"));
  document.getElementById("btn-en").addEventListener("click", () => setLang("en"));

  // Teacher modal
  document.getElementById("btn-teacher").addEventListener("click", openTeacherModal);
  document.getElementById("btn-teacher-cancel").addEventListener("click", closeTeacherModal);
  document.getElementById("btn-teacher-submit").addEventListener("click", submitTeacherLogin);
  document.getElementById("input-teacher-password").addEventListener("keydown", (e) => {
    if (e.key === "Enter") submitTeacherLogin();
  });
  document.getElementById("modal-teacher").addEventListener("click", (e) => {
    if (e.target === e.currentTarget) closeTeacherModal();
  });

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
  document.getElementById("btn-logout").addEventListener("click", () => {
    // TODO M5: DELETE /teacher/logout to clear session cookie
    showView("landing");
  });

  // Init
  setLang("nl");
  showView("landing");
});
