const VIEWS = ["landing", "student-home", "teacher"];

function showView(name) {
  VIEWS.forEach((v) => {
    document.getElementById(`view-${v}`).classList.toggle("hidden", v !== name);
  });
}
