function joinWithClassroomCode() {
  const code = document.getElementById("input-classroom-code").value.trim().toUpperCase();
  if (!code) return;
  // TODO M3: POST /student/join with classroom_code, store personal code, route to student home
  showView("student-home");
}

function joinWithPersonalCode() {
  const code = document.getElementById("input-personal-code").value.trim().toUpperCase();
  if (!code) return;
  // TODO M3: POST /student/reconnect with personal_code, restore session, route to student home
  showView("student-home");
}
