/* Task-based settings. Move the original nodes once, preserving IDs, handlers and drafts.
   Runs after the feature panels have been created, before the route adapter. */
(() => {
  const get = (id) => document.getElementById(id),
    settings = get("view-settings");
  const make = (tag, cls, text) => {
    const n = document.createElement(tag);
    n.className = cls;
    if (text) n.textContent = text;
    return n;
  };
  const link = (tab, title, text) =>
    SurvieUI.cardLink("appareil/" + tab, title, text);
  const panes = {};
  for (const [key, title, description] of [
    [
      "reglages",
      "Choisir une rubrique",
      "Choisissez ce que vous voulez faire. Ouvrir une rubrique ne lance aucun travail.",
    ],
    [
      "acces",
      "Profils et connexion",
      "Choisir un espace personnel ou ouvrir SetupSurvie sur un autre appareil.",
    ],
    [
      "bibliotheque",
      "Bibliothèque et préparations",
      "Ajouter des documents et préparer leur consultation hors ligne.",
    ],
    [
      "assistant",
      "Réglages de l’assistant",
      "Garder la main sur l’assistant et la mémoire du PC.",
    ],
    [
      "entretien",
      "Entretien et données",
      "Comprendre un problème et conserver un rapport avant une intervention.",
    ],
    [
      "tests",
      "Tests et diagnostics",
      "Choisissez un test selon votre question. Ouvrir cette page ne lance aucun calcul.",
    ],
    [
      "lieux",
      "Lieux de référence",
      "Le domicile et le point de départ servent aux cartes et à l’assistant.",
    ],
  ]) {
    const pane = make("div", "settings-pane");
    pane.id = "settings-" + key;
    pane.dataset.settingsPane = key;
    pane.hidden = true;
    pane.dataset.title = title;
    pane.dataset.description = description;
    const heading = make("div", "settings-heading");
    heading.append(make("h2", "", title), make("p", "muted", description));
    pane.append(heading);
    settings.append(pane);
    panes[key] = pane;
  }
  settings.querySelector(".page-heading h1").textContent = "Paramètres";
  settings.querySelector(".page-heading p").textContent =
    "Pour les réglages partagés, choisissez le profil Famille, sans mot de passe.";
  const back = make("a", "settings-back", "← Tous les paramètres");
  back.href = "#/appareil/reglages";
  back.dataset.route = "appareil/reglages";
  back.id = "settings-back";
  settings.querySelector(".page-heading").after(back);
  const hub = make("div", "settings-destinations");
  panes.reglages.append(hub);
  for (const [key, title, description] of [
    [
      "acces",
      "Profils et connexion",
      "Gérer les profils, afficher le QR code et l’adresse du site.",
    ],
    [
      "bibliotheque",
      "Bibliothèque et préparations",
      "Ajouter un guide, télécharger des collections, préparer la recherche et les cartes.",
    ],
    [
      "assistant",
      "Assistant",
      "Démarrer ou arrêter l’assistant ; ajuster ses réglages avancés.",
    ],
    [
      "tests",
      "Tests et diagnostics",
      "Mesurer recherche, IA, mémoire ou traduction ; vérifier l’usage hors ligne.",
    ],
    [
      "entretien",
      "Entretien et données",
      "Exporter les classements et gérer les repères de ce navigateur.",
    ],
  ])
    hub.append(link(key, title, description));
  panes.acces.append(
    link(
      "profils",
      "Gérer les profils",
      "Créer un profil pour ranger conversations et favoris, sans mot de passe.",
    ),
    link(
      "connexion",
      "Ouvrir sur un téléphone",
      "Afficher le QR code, copier l’adresse ou imprimer la fiche de connexion.",
    ),
  );
  panes.acces.append(
    make(
      "p",
      "small muted",
      "Les profils organisent les données. Toute personne du réseau peut choisir un autre profil et consulter ses données.",
    ),
  );
  panes.bibliotheque.append(
    link(
      "telechargements",
      "Télécharger des collections et préparer les cartes",
      "Choisir les contenus et suivre les préparations, sans interrompre les travaux en cours.",
    ),
    link(
      "stockage",
      "Voir les fichiers et l’espace disque",
      "Distinguer les documents et modèles enregistrés de la mémoire utilisée par l’assistant.",
    ),
  );
  const move = (id, pane) => {
    const node = get(id).closest("article");
    panes[pane].append(node);
    return node;
  };
  const upload = move("upload-form", "bibliotheque");
  upload.querySelector("details").id = "settings-add-guide";
  get("upload-form").before(
    make(
      "p",
      "next-mobile-note",
      "Pour ajouter un fichier, utilisez un ordinateur.",
    ),
  );
  const index = move("next-index-status", "bibliotheque");
  const advanced = (node, id, title) => {
    const d = make("details", "settings-advanced");
    d.id = id;
    d.append(make("summary", "", title));
    node.before(d);
    d.append(node);
    return d;
  };
  advanced(index, "settings-index", "Préparer la recherche dans les archives");
  get("next-index-settings").before(
    make(
      "p",
      "next-mobile-note",
      "Pour préparer les index ou modifier leur programmation, utilisez un ordinateur. La pause et le rapport restent accessibles ici.",
    ),
  );
  const engine = move("engine-controls", "assistant");
  engine.querySelector("details").open = true;
  engine.querySelector("summary").textContent =
    "Démarrer ou arrêter l’assistant";
  engine.querySelector("details").id = "settings-engine";
  engine.append(
    make(
      "p",
      "small muted",
      "Pour jouer ou libérer la mémoire, arrêtez l’assistant. Sa reprise reste explicite ; les documents restent consultables.",
    ),
  );
  const engineState = make("p", "small");
  engineState.id = "settings-engine-state";
  engine.querySelector("details > summary").after(engineState);
  panes.assistant.append(
    link(
      "ensemble",
      "Voir la RAM, la VRAM et le modèle chargé",
      "Voir les mesures actuelles du PC et de la carte graphique, sans démarrer l’assistant.",
    ),
  );
  advanced(
    move("next-context-form", "assistant"),
    "settings-context",
    "Options avancées : mémoire et essai du modèle",
  );
  const memory = get("next-calibration-form").closest("details");
  memory.id = "settings-test-memory";
  memory.classList.add("settings-advanced");
  panes.tests.append(memory);
  panes.assistant.append(
    link(
      "tests?test=memory",
      "Tester la mémoire de l’assistant",
      "Comparer les contextes 16k/32k avec des mesures, sans changer le réglage automatiquement.",
    ),
  );
  const policy = move("assistant-policy", "assistant").querySelector("details");
  policy.id = "settings-policy";
  policy.querySelector("summary").textContent =
    "Instructions transmises aux modèles";
  panes.assistant.append(
    make(
      "p",
      "small muted",
      "Le temps de réponse se choisit dans la conversation. Les essais avancés utilisent l’IA uniquement après votre commande.",
    ),
  );
  const check = move("next-search-check-open", "tests");
  advanced(
    check,
    "settings-test-search",
    "Recherche : vérifier les résultats et comparer l’aide IA",
  );
  const performance = move("next-performance-start", "tests");
  advanced(
    performance,
    "settings-test-performance",
    "Lenteurs : recherche, IA et ressources du PC",
  );
  // Keep each feature’s article ancestor: its controller may append controls to it.
  const offline = make("article", "panel");
  offline.append(
    make("h2", "", "Vérifier l’usage hors ligne"),
    make(
      "p",
      "",
      "Réunir les contrôles et vos observations dans un rapport, sans IA.",
    ),
    get("next-usage-open"),
  );
  panes.tests.append(offline);
  advanced(
    offline,
    "settings-test-offline",
    "Usage hors ligne : vérifier les fonctions disponibles",
  );
  if (get("next-translation-benchmark")) {
    const translation = move("next-translation-benchmark-start", "tests");
    advanced(
      translation,
      "settings-test-translation",
      "Traduction : mesurer un document de 40 pages",
    );
  }
  panes.entretien.prepend(
    link(
      "tests",
      "Tests et diagnostics",
      "Retrouver les vérifications de recherche, de mémoire, de traduction et d’usage hors ligne.",
    ),
  );
  const exports = make("details", "settings-advanced");
  exports.id = "settings-exports";
  exports.append(
    make("summary", "", "Conserver les classements et les dossiers pratiques"),
  );
  panes.entretien.append(exports);
  for (const id of ["catalogue-metadata-export", "practical-dossiers-export"]) {
    const panel = get(id);
    if (panel) exports.append(panel);
  }
  advanced(
    move("next-clear-memory", "entretien"),
    "settings-navigation-memory",
    "Effacer les repères de ce navigateur",
  );
  const feedback = move("refresh-feedback", "entretien").querySelector(
    "details",
  );
  feedback.id = "settings-old-feedback";
  feedback.querySelector("summary").textContent =
    "Consulter les retours déjà enregistrés";
  const places = move("location-summary", "lieux");
  places.querySelector("h2").remove();
  panes.bibliotheque.append(
    link(
      "lieux",
      "Changer le domicile ou le point de départ",
      "Retrouver les lieux partagés utilisés pour préparer une zone.",
    ),
  );
  // Remove navigation duplicates only, after moving all original feature panels.
  settings.querySelector(".settings-links")?.remove();
  settings.querySelector(".next-settings-links")?.remove();
  settings.querySelector(".next-mobile-note")?.remove();
  const oldProfiles = [...settings.querySelectorAll("article")].find((n) =>
    n.querySelector('[data-view="users"]'),
  );
  oldProfiles?.remove();
  settings.querySelector(".admin-grid")?.remove();
  for (const pane of Object.values(panes)) {
    const links = [...pane.children].filter((n) =>
      n.matches("a.settings-destination"),
    );
    if (!links.length) continue;
    const group = make("div", "settings-card-grid");
    links[0].before(group);
    group.append(...links);
  }
  const tabs = get("next-machine-tabs");
  tabs.replaceChildren();
  for (const [key, title] of [
    ["ensemble", "Vue d’ensemble"],
    ["activite", "Travaux en cours"],
    ["reglages", "Paramètres"],
  ]) {
    const a = link(key, title, "");
    a.className = "";
    a.replaceChildren(document.createTextNode(title));
    a.dataset.route = "appareil/" + key;
    tabs.append(a);
  }
  get("admin-nav").textContent = "Paramètres";
  const engineShortcut = get("view-monitor").querySelector(
    '[data-view="settings"]',
  );
  engineShortcut.removeAttribute("data-view");
  engineShortcut.dataset.route = "appareil/assistant";
  engineShortcut.textContent = "Gérer l’assistant";
  get("view-monitor").querySelector(".page-heading h1").textContent =
    "État de l’appareil";
  const metrics = make("section", "server-metrics");
  metrics.id = "settings-server-metrics";
  metrics.setAttribute("aria-labelledby", "server-metrics-title");
  const metricsTitle = make("h2", "", "Mémoire et modèle chargé");
  metricsTitle.id = "server-metrics-title";
  metrics.append(metricsTitle, make("p", "muted small", "Mesures du PC qui héberge SetupSurvie. Le stockage se consulte séparément dans les paramètres de la bibliothèque."));
  get("view-monitor").querySelector(".page-heading").after(metrics);
  metrics.append(
    get("monitor-models").closest("article"),
    get("monitor-stats"),
    get("monitor-updated"),
  );
  get("view-activity").append(
    link(
      "telechargements",
      "Voir les téléchargements et leurs commandes",
      "Consulter la sélection et les préparations de documents ou de cartes.",
    ),
  );
  for (const name of ["data", "storage", "users", "connect"]) {
    const a = make(
      "a",
      "settings-back",
      "← Paramètres · " +
        {
          data: "Bibliothèque",
          storage: "Bibliothèque",
          users: "Profils et connexion",
          connect: "Profils et connexion",
        }[name],
    );
    a.href =
      "#/appareil/" +
      (["data", "storage"].includes(name) ? "bibliotheque" : "acces");
    a.dataset.route = a.hash.slice(2);
    get("view-" + name)
      .querySelector(".page-heading")
      .after(a);
  }
  const geo = get("geo-datasets").closest("article");
  advanced(
    geo,
    "settings-map-preparation",
    "Préparer des cartes, adresses et itinéraires",
  );
  // Primary mobile actions remain usable; only long preparation forms stay on PC.
  for (const [target, text] of [
    [
      "view-data",
      "Sur téléphone, consultez le suivi et mettez en pause les préparations du portail. Le choix de nouveaux contenus ou de zones se fait sur ordinateur.",
    ],
    [
      "settings-bibliotheque",
      "L’ajout d’un fichier et la préparation des archives se font sur ordinateur. Le suivi et les rapports restent accessibles sur téléphone.",
    ],
    [
      "settings-lieux",
      "Les lieux enregistrés restent consultables ici. Pour modifier une adresse ou ses coordonnées, utilisez un ordinateur.",
    ],
  ])
    get(target).append(make("p", "next-mobile-note", text));
  const cardDescriptions = {
    "settings-add-guide":
      "Ajouter un fichier personnel à la bibliothèque locale.",
    "settings-index":
      "Rendre le texte des collections disponible dans la recherche.",
    "settings-engine":
      "Libérer la mémoire du PC ou rendre l’assistant disponible.",
    "settings-context":
      "Régler le contexte par modèle ; les essais se lancent séparément.",
    "settings-policy":
      "Consulter le contexte et les consignes utilisés pour les réponses.",
    "settings-exports":
      "Télécharger les noms corrigés et les repères documentaires examinés.",
    "settings-navigation-memory":
      "Effacer les repères locaux sans supprimer les données du serveur.",
    "settings-old-feedback":
      "Relire les observations déjà enregistrées sur cet appareil.",
    "settings-test-memory":
      "Comparer les contextes possibles avec les ressources de ce PC.",
    "settings-test-search":
      "Vérifier les résultats locaux avant d’évaluer une aide IA facultative.",
    "settings-test-performance":
      "Mesurer les délais et retrouver les étapes lentes d’une réponse.",
    "settings-test-offline":
      "Rassembler les contrôles et observations de lecture sans Internet.",
    "settings-test-translation":
      "Mesurer une traduction progressive avec pause, reprise et rapport.",
  };
  for (const [id, description] of Object.entries(cardDescriptions)) {
    const card = get(id);
    if (card) SurvieUI.describeDisclosure(card, description);
  }
  // The card header stays outside the generated fields and their event handlers.
  window.SettingsLayout = {
    show(tab, test) {
      for (const [key, pane] of Object.entries(panes)) {
        pane.hidden = key !== tab;
        pane.querySelector(".settings-heading").hidden = key !== "reglages";
      }
      const pane = panes[tab] || panes.reglages;
      settings.querySelector(".page-heading h1").textContent =
        tab === "reglages"
          ? "Paramètres"
          : {
              acces: "Profils et connexion",
              bibliotheque: "Bibliothèque et préparations",
              assistant: "Assistant",
              tests: "Tests et diagnostics",
              entretien: "Entretien et données",
              lieux: "Vos lieux de référence",
            }[tab] || "Paramètres";
      document.title =
        settings.querySelector(".page-heading h1").textContent +
        " · SetupSurvie";
      settings.querySelector(".page-heading p").textContent =
        tab === "reglages"
          ? "Pour les réglages partagés, choisissez le profil Famille, sans mot de passe."
          : pane.dataset.description;
      back.hidden = tab === "reglages";
      if (
        tab === "tests" &&
        ["performance", "search", "memory", "translation", "offline"].includes(
          test,
        )
      )
        get("settings-test-" + test).open = true;
      get("settings-engine-state").textContent =
        get("engine-state").textContent +
        " · " +
        get("engine-detail").textContent;
    },
  };
  new MutationObserver(() => {
    get("settings-engine-state").textContent =
      get("engine-state").textContent +
      " · " +
      get("engine-detail").textContent;
  }).observe(get("view-monitor").querySelector(".engine-panel"), {
    childList: true,
    subtree: true,
    characterData: true,
  });
})();
