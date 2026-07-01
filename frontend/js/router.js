const VIEWS = ["landing", "student-home", "student-activity", "teacher", "register"];

function showView(name) {
  VIEWS.forEach((v) => {
    document.getElementById(`view-${v}`).classList.toggle("hidden", v !== name);
  });
}
