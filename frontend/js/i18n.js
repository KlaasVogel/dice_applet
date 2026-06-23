const TRANSLATIONS = {
  nl: {
    page_title: "Dobbelstenen — Radioactief verval",
    app_title: "Dobbelstenen",
    landing_new: "Meedoen aan een klas",
    landing_return: "Ik heb al een code",
    label_classroom_code: "Klassikale code",
    label_personal_code: "Persoonlijke code",
    btn_join: "Meedoen",
    btn_continue: "Verdergaan",
    btn_leave: "Terug",
    or: "of",
    student_home_stub: "Welkom! Activiteiten volgen in de volgende fase.",
    teacher_title: "Docentendashboard",
    teacher_stub: "Klasbeheer volgt in een latere fase.",
    btn_logout: "Uitloggen",
    teacher_login_title: "Docent inloggen",
    label_password: "Wachtwoord",
    teacher_login_error: "Ongeldig wachtwoord",
    btn_cancel: "Annuleren",
    btn_login: "Inloggen",
  },
  en: {
    page_title: "Dice — Radioactive decay",
    app_title: "Dice",
    landing_new: "Join a classroom",
    landing_return: "I already have a code",
    label_classroom_code: "Classroom code",
    label_personal_code: "Personal code",
    btn_join: "Join",
    btn_continue: "Continue",
    btn_leave: "Back",
    or: "or",
    student_home_stub: "Welcome! Activities coming in the next phase.",
    teacher_title: "Teacher dashboard",
    teacher_stub: "Classroom management coming in a later phase.",
    btn_logout: "Log out",
    teacher_login_title: "Teacher login",
    label_password: "Password",
    teacher_login_error: "Invalid password",
    btn_cancel: "Cancel",
    btn_login: "Log in",
  },
};

let currentLang = "nl";

function setLang(lang) {
  currentLang = lang;
  document.documentElement.lang = lang;

  document.querySelectorAll("[data-i18n]").forEach((el) => {
    const key = el.dataset.i18n;
    const text = TRANSLATIONS[lang][key];
    if (text !== undefined) {
      el.tagName === "TITLE" ? (document.title = text) : (el.textContent = text);
    }
  });

  document.getElementById("btn-nl").classList.toggle("active", lang === "nl");
  document.getElementById("btn-en").classList.toggle("active", lang === "en");
}
