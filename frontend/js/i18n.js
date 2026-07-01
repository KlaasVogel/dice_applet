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
    modal_login_title: "Inloggen",
    tab_teacher: "Docent",
    tab_admin: "Admin",
    label_email: "E-mailadres",
    label_password: "Wachtwoord",
    teacher_login_error: "Onjuiste gegevens",
    btn_cancel: "Annuleren",
    btn_login: "Inloggen",
    link_register: "Nog geen account? Verzoek indienen →",
    register_title: "Account aanvragen",
    legend_school: "School",
    radio_new_school: "Nieuwe school aanmaken",
    radio_existing_school: "Aansluiten bij bestaande school",
    label_school_name: "Naam van de school",
    label_select_school: "Kies een school",
    btn_submit: "Versturen",
    register_success: "Verzoek ingediend! Je ontvangt bericht als je account is goedgekeurd.",
    error_network: "Verbindingsfout — probeer het opnieuw.",
    error_join_classroom: "Ongeldige of onbekende code.",
    error_join_full: "Deze klas is vol.",
    error_join_personal: "Code niet gevonden.",
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
    modal_login_title: "Log in",
    tab_teacher: "Teacher",
    tab_admin: "Admin",
    label_email: "Email address",
    label_password: "Password",
    teacher_login_error: "Invalid credentials",
    btn_cancel: "Cancel",
    btn_login: "Log in",
    link_register: "No account yet? Request access →",
    register_title: "Request an account",
    legend_school: "School",
    radio_new_school: "Create a new school",
    radio_existing_school: "Join an existing school",
    label_school_name: "School name",
    label_select_school: "Select a school",
    btn_submit: "Submit",
    register_success: "Request submitted! You will be notified once your account is approved.",
    error_network: "Connection error — please try again.",
    error_join_classroom: "Invalid or unknown code.",
    error_join_full: "This classroom is full.",
    error_join_personal: "Code not found.",
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
