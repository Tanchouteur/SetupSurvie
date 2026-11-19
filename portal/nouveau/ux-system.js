/* Shared interface primitives. No inference, job creation or data migration. */
(() => {
  document.addEventListener("DOMContentLoaded", () => {
    const profileAvatar = document.querySelector("#account-button .avatar");
    function drawAvatar() {
      if (profileAvatar)
        profileAvatar.textContent = (S.user?.name || "P")
          .slice(0, 1)
          .toLocaleUpperCase("fr");
    }
    drawAvatar();
    document.addEventListener("survie:auth", drawAvatar);
    const title = document.querySelector("#view-library h1");
    if (title) title.textContent = "Bibliothèque";
    const welcome = document.querySelector("#view-home h1");
    if (welcome) welcome.textContent = "Que souhaitez-vous faire ?";
    for (const label of document.querySelectorAll(
      "label:has(input[type=checkbox])",
    ))
      label.classList.add("ux-checkbox-label");
    const mode = document.querySelector('label[for="chat-mode"]');
    if (mode) {
      mode.textContent = "Réponse";
      mode.classList.add("assistant-mode-label");
    }
    const domain = document.querySelector("#next-domain-controls");
    if (domain) {
      const explanation = SurvieUI.help(
        "Comprendre les espaces documentaires",
        "Les espaces orientent la recherche. Choisissez Toute la bibliothèque pour inclure aussi les documents non classés.",
      );
      domain.append(explanation);
    }
    const label = document.querySelector('label[for="collection-filter"]');
    if (label) {
      label.textContent = "Filtrer les collections";
      const caption = element("div", undefined, "ux-label-row");
      label.before(caption);
      caption.append(
        label,
        SurvieUI.help(
          "Comprendre le filtre des collections",
          "Ce champ cherche dans les titres et descriptions. Pour chercher un sujet dans les articles et les livres, utilisez Rechercher.",
        ),
      );
    }
  });
  const resumeBox = element("section", undefined, "ux-resume");
  resumeBox.setAttribute("aria-label", "Reprendre une activité");
  const home = document.getElementById("view-home");
  home.querySelector(".welcome").after(resumeBox);
  function recentReading() {
    if (!S.user) return null;
    try {
      const saved = JSON.parse(
        localStorage.getItem("survie-next-v1:" + S.user.id + ":last-document"),
      );
      return saved && Date.now() - saved.at < 7 * 86400000 ? saved : null;
    } catch (_) {
      return null;
    }
  }
  function drawResume() {
    resumeBox.replaceChildren();
    if (!S.user) return;
    const document = recentReading(),
      conversation = readingState().selected;
    if (document)
      resumeBox.append(
        button(
          "Reprendre la lecture : " + document.title,
          () => readSource(document.id),
          "secondary",
        ),
      );
    if (conversation)
      resumeBox.append(
        button(
          "Reprendre la discussion",
          () => openConversation(conversation),
          "secondary",
        ),
      );
    resumeBox.hidden = !resumeBox.children.length;
  }
  document.addEventListener("survie:source", (event) => {
    if (S.user)
      try {
        localStorage.setItem(
          "survie-next-v1:" + S.user.id + ":last-document",
          JSON.stringify({
            id: event.detail.id,
            title: event.detail.title,
            at: Date.now(),
          }),
        );
      } catch (_) {}
    drawResume();
  });
  document.addEventListener("survie:conversation", drawResume);
  document.addEventListener("survie:auth", drawResume);
  document.addEventListener("survie:route", (event) => {
    if (event.detail.section === "accueil") drawResume();
  });
  // Opened content takes priority over the search form, especially on phones.
  document.addEventListener("survie:source", () => {
    const reader = document.getElementById("reader"),
      heading = reader?.querySelector("h2");
    if (!heading) return;
    heading.tabIndex = -1;
    requestAnimationFrame(() => {
      heading.focus({ preventScroll: true });
      reader.scrollIntoView({ block: "start", behavior: "instant" });
    });
  });
})();
