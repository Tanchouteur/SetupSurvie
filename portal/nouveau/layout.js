/* Reorganise les contrôles existants sans les recopier ni changer leurs actions. */
(() => {
  const get = (id) => document.getElementById(id);
  const make = (tag, cls, html = "") => {
    const n = document.createElement(tag);
    n.className = cls;
    n.innerHTML = html;
    return n;
  };
  const route = (path, label) =>
    `<a href="#/${path}" data-route="${path}">${label}</a>`;
  const header = (title, text) =>
    make("div", "page-heading", `<h1>${title}</h1><p>${text}</p>`);
  const nav = make("nav", "next-main-nav");
  nav.id = "navigation";
  nav.setAttribute("aria-label", "Navigation principale");
  for (const [path, icon, label] of [
    ["accueil", "⌂", "Accueil"],
    ["bibliotheque", "▤", "Bibliothèque"],
    ["assistant", "◌", "Assistant"],
    ["cartes", "⌖", "Cartes"],
    ["appareil", "◴", "Mon appareil"],
  ]) {
    const a = make(
      "a",
      "nav-item",
      `<span aria-hidden="true">${icon}</span><span>${label}</span>`,
    );
    a.href = path === "cartes" ? "/cartes.html?interface=nouveau" : "#/" + path;
    if (path !== "cartes") a.dataset.route = path;
    nav.append(a);
  }
  const navIcons = {
    accueil: "M3 10l9-7 9 7 M5 9v12h14V9 M9 21v-7h6v7",
    bibliotheque:
      "M3 5h7c1 0 2 1 2 2v14c0-2-2-3-4-3H3z M21 5h-7c-1 0-2 1-2 2v14c0-2 2-3 4-3h5z",
    assistant: "M4 4h16v12H9l-5 4z M8 8h8 M8 12h5",
    cartes: "M3 5l6-2 6 2 6-2v16l-6 2-6-2-6 2z M9 3v16 M15 5v16",
    appareil: "M3 4h18v13H3z M8 21h8 M12 17v4",
  };
  for (const item of nav.children) {
    const section = item.dataset.route || "cartes";
    item.firstElementChild.replaceChildren(SurvieUI.icon(navIcons[section]));
  }
  get("main-navigation").querySelector("nav").replaceWith(nav);
  const history = make("dialog", "next-history-dialog");
  history.id = "next-history-dialog";
  history.setAttribute("aria-labelledby", "next-history-title");
  history.append(make("h2", "", "Vos conversations"));
  history.firstChild.id = "next-history-title";
  history.append(document.querySelector(".sidebar-section"));
  history.append(
    make(
      "div",
      "actions",
      '<a class="native-webui" href="/">Assistant avancé · Open WebUI ↗</a><a href="/secours.html">Documents de secours ↗</a>',
    ),
  );
  const close = make("button", "secondary", "Fermer");
  close.dataset.close = "next-history-dialog";
  history.append(close);
  document.body.append(history);
  const actions = make("div", "next-chat-actions"),
    historyButton = make("button", "secondary", "Conversations");
  historyButton.id = "next-history-open";
  historyButton.setAttribute("aria-haspopup", "dialog");
  historyButton.onclick = () => history.showModal();
  actions.append(historyButton, get("chat-reset"));
  get("view-chat").querySelector(".chat-top").append(actions);
  get("view-chat").querySelector(".native-help")?.remove();
  get("feedback-button").hidden = true;
  document.addEventListener("click", (event) => {
    if (history.open && event.target.closest(".conversation-link"))
      history.close();
  });
  get("admin-nav")?.remove(); // Its ID is recreated as a visible-in-Famille settings shortcut.
  const admin = make("button", "quiet", "Réglages de l’appareil");
  admin.id = "admin-nav";
  admin.dataset.view = "settings";
  admin.hidden = true;
  document.querySelector(".sidebar-bottom").prepend(admin);
  const brand = document.querySelector(".brand");
  brand.href = "#/accueil";
  brand.dataset.route = "accueil";
  brand.setAttribute("aria-label", "SetupSurvie");
  brand.lastElementChild.classList.add("ds-brand-name");
  for (const host of [brand, get("breadcrumb").parentElement]) {
    const version = make("span", "ds-nav-version");
    if (host === brand) version.setAttribute("aria-hidden", "true");
    host.append(version);
  }
  document
    .querySelectorAll(
      'a[href="/maquette/"],a[href="/nouveau/"],a[href^="/classique/"]',
    )
    .forEach((a) => a.remove());
  get("view-home").querySelector("h1").innerHTML =
    "Qu’avez-vous<br>envie d’apprendre ?";
  get("view-home").querySelector(".welcome").classList.add("next-welcome");
  const lib = get("view-library"),
    oldHeading = lib.querySelector(".page-heading");
  oldHeading.replaceWith(
    header(
      "Bibliothèque",
      "Ouvrez une collection directement ou recherchez une information dans les documents.",
    ),
  );
  const libTabs = make("nav", "next-tabs");
  libTabs.setAttribute("aria-label", "Rubriques de la bibliothèque");
  libTabs.innerHTML = [
    ["collections", "Collections"],
    ["recherche", "Rechercher"],
    ["parcours", "Apprendre par thème"],
    ["favoris", "Mes favoris"],
    ["traductions", "Traductions"],
  ]
    .map(([p, l]) => route("bibliotheque/" + p, l))
    .join("");
  lib.querySelector(".page-heading").after(libTabs);
  const scope = make("select", "");
  scope.id = "search-collection";
  scope.setAttribute("aria-label", "Chercher dans une collection");
  scope.append(new Option("Toutes les collections", ""));
  scope.addEventListener("change", () => {
    scope.dataset.requested = scope.value;
  });
  const language = get("search-language");
  language.before(scope);
  language.options[0].textContent = "Français + anglais";
  language.options[1].textContent = "Français";
  language.options[2].textContent = "Anglais";
  // Videos are hard to find among thousands of articles: let people ask for
  // them only. With « Vidéos uniquement », an empty search lists them all.
  const kind = make("select", "");
  kind.id = "search-kind";
  kind.setAttribute("aria-label", "Type de résultat");
  kind.append(
    new Option("Tous les types", "all"),
    new Option("Vidéos", "videos"),
    new Option("Documents", "documents"),
  );
  const query = get("library-query");
  const fitKind = () => {
    query.required = kind.value !== "videos";
    query.placeholder =
      kind.value === "videos"
        ? "Sujet, ou vide pour toutes les vidéos"
        : "Ex. : loi d’Ohm, compost, conserver des légumes…";
  };
  kind.addEventListener("change", fitKind);
  kind.fitKind = fitKind;
  language.after(kind);
  const domain = make(
    "div",
    "next-domain",
    '<label for="search-domain">Chercher dans</label><select id="search-domain" aria-label="Espace documentaire"><option value="resilience">Autonomie et résilience</option><option value="culture">Savoirs et culture</option><option value="all">Toute la bibliothèque</option></select>',
  );
  libTabs.after(domain);
  domain.id = "next-domain-controls";
  domain.after(
    make(
      "p",
      "small muted",
      "Les espaces orientent la recherche à partir du texte disponible. Toute la bibliothèque permet de retrouver aussi les documents non classés. Les collections restent directement ouvrables.",
    ),
  );
  const chatDomain = make(
    "label",
    "next-chat-domain",
    '<span class="sr-only">Sources de l’assistant</span><select id="chat-domain" aria-label="Espace des sources de l’assistant"><option value="resilience">Autonomie et résilience</option><option value="culture">Savoirs et culture</option><option value="all">Toute la bibliothèque</option></select>',
  );
  actions.append(chatDomain);
  domain.nextElementSibling.id = "next-domain-help";
  const learningBrowser = get("learning-browser");
  learningBrowser.querySelector("summary").textContent =
    "Choisissez un sujet à apprendre";
  const help = make(
    "p",
    "",
    "Choisissez un sujet, puis ouvrez les documents disponibles. Vous pouvez aussi préparer une question à l’assistant. Cette liste de thèmes ne garantit pas qu’un guide complet soit présent.",
  );
  learningBrowser.querySelector("summary").after(help);
  get("learning-level").closest("label").firstChild.textContent =
    "Ce que vous souhaitez apprendre";

  const search = make("div", "next-library-pane");
  search.id = "next-search";
  for (const child of [...lib.children])
    if (
      child !== lib.querySelector(".page-heading") &&
      child !== libTabs &&
      child !== domain &&
      child !== domain.nextElementSibling
    )
      search.append(child);
  const learning = make("div", "next-library-pane");
  learning.id = "next-learning";
  learningBrowser.open = false;
  learning.append(learningBrowser);
  const collections = make("div", "next-library-pane");
  collections.id = "next-collections";
  const categories = make("nav", "next-collection-types");
  categories.setAttribute("aria-label", "Types de ressources");
  for (const [key, label] of [
    ["", "Tout"],
    ["videos", "Vidéos"],
    ["guides", "Guides"],
    ["livres", "Livres et encyclopédies"],
  ]) {
    const link = make("a", "secondary", label);
    link.dataset.collectionType = key;
    categories.append(link);
  }
  collections.append(categories);
  collections.append(
    make(
      "p",
      "muted",
      "Ces collections sont réellement présentes sur le serveur. Leur disponibilité de lecture est vérifiée séparément de leur téléchargement.",
    ),
  );
  const filter = make("form", "next-collection-filter");
  filter.id = "collection-filter-form";
  filter.innerHTML =
    '<label for="collection-filter">Chercher une ressource installée</label><div class="next-collection-search"><input id="collection-filter" type="search" maxlength="160" autocomplete="off" placeholder="Ex. : Wikipédia, jardin, Anses…" aria-describedby="collection-filter-help"><button id="collection-filter-clear" class="secondary" type="button">Effacer le filtre</button></div><p id="collection-filter-help" class="small muted">Filtre les noms et les descriptions des ressources affichées.</p><p id="collection-filter-count" class="small" role="status" aria-live="polite"></p><a id="collection-search-inside" href="#/bibliotheque/recherche">Chercher aussi à l’intérieur des documents →</a>';
  const empty = make(
    "p",
    "empty-panel",
    "Aucun livre ni guide ne correspond à ces mots. Un article ou un chapitre peut toutefois traiter ce sujet : essayez la recherche dans les documents.",
  );
  empty.id = "collection-filter-empty";
  empty.hidden = true;
  collections.append(filter, empty);
  for (const [key, label, content] of [
    ["livres", "Livres et encyclopédies", get("data-books")],
    ["guides", "Guides et fiches pratiques", get("data-guides")],
    ["videos", "Vidéos de la bibliothèque", null],
  ]) {
    const section = make("details", "next-collection-section");
    section.id = "collection-section-" + key;
    section.dataset.collectionSection = key;
    section.open = true;
    const summary = make("summary", "collection-section-title");
    summary.append(make("h2", "", label));
    section.append(summary);
    if (content) section.append(content);
    collections.append(section);
  }
  const invNotice = make("p", "small muted");
  invNotice.id = "next-inventory-notice";
  invNotice.setAttribute("role", "status");
  collections.prepend(invNotice);
  lib.append(collections, search, learning);
  const storage = make("section", "view");
  storage.id = "view-storage";
  storage.hidden = true;
  const copy = make("article", "panel");
  const copyLink = make("a", "secondary-link", "Copier l’installation");
  copyLink.href = "/suivi-copie.html";
  copy.append(
    make("h2", "", "Copier SetupSurvie vers un autre disque"),
    make("p", "", "Choisissez le dossier de destination sur le PC serveur et suivez la copie depuis le navigateur."),
    copyLink,
  );
  storage.append(
    header(
      "L’espace de votre bibliothèque.",
      "Les fichiers sur disque sont distincts des modèles chargés en mémoire.",
    ),
    get("data-summary"),
    copy,
    make("h2", "", "Modèles enregistrés sur le disque"),
    get("data-models"),
    get("data-preparation"),
  );
  get("main").append(storage);
  const maps = make("section", "view");
  maps.id = "view-maps";
  maps.hidden = true;
  maps.append(
    header(
      "Vos repères, autour de vous.",
      "Retrouvez les cartes locales, vos points et les itinéraires préparés.",
    ),
  );
  maps.append(
    make(
      "article",
      "panel next-map-intro",
      '<h2>Cartes hors ligne</h2><p>Le fond de carte, les adresses, le relief et le réseau d’itinéraires sont préparés séparément. La présence d’un fond ne signifie pas que toutes ces données sont disponibles.</p><a class="button" href="/cartes.html?interface=nouveau">Ouvrir les cartes et mes repères →</a><p class="next-mobile-note">Sur téléphone, privilégiez la consultation des lieux et trajets préparés. Les outils complexes de création restent sur ordinateur.</p>',
    ),
  );
  get("main").append(maps);
  get("view-monitor")
    .querySelector(".page-heading")
    .replaceWith(
      header(
        "État de l’appareil",
        "Ce sont les mesures du PC qui héberge SetupSurvie, même lorsque vous consultez cette page depuis un téléphone.",
      ),
    );
  get("view-data")
    .querySelector(".page-heading")
    .replaceWith(
      header(
        "Téléchargements et préparations",
        "Suivez les transferts en cours avant d’ajouter de nouveaux contenus.",
      ),
    );
  // Inventory grids moved to Library/Storage; remove only the now-empty headings.
  for (const node of [...get("view-data").children]) {
    if (node.tagName === "H2" || node.classList.contains("section-top"))
      node.remove();
    else if (node.tagName === "P") storage.append(node);
  }
  const machineTabs = make("nav", "next-tabs");
  machineTabs.id = "next-machine-tabs";
  machineTabs.setAttribute("aria-label", "Rubriques de l’appareil");
  machineTabs.innerHTML = [
    ["ensemble", "Vue d’ensemble"],
    ["telechargements", "Téléchargements"],
    ["stockage", "Stockage"],
    ["reglages", "Réglages"],
  ]
    .map(([p, l]) => route("appareil/" + p, l))
    .join("");
  get("view-monitor").querySelector(".page-heading").after(machineTabs);
  for (const target of ["view-monitor", "view-data"]) {
    const block = make("article", "panel next-activity");
    block.innerHTML =
      '<h2 class="next-transfer-title">Lecture de l’activité…</h2><p class="next-transfer-message" role="status"></p><progress class="next-transfer-progress" max="1" aria-label="Volume du plan déjà vérifié" hidden></progress><div class="next-transfer-files"></div><p class="next-transfer-time small muted"></p><p class="small muted">Les fichiers partiels ne sont pas encore vérifiés. Un reçu de vérification ne prouve pas la disponibilité dans le lecteur ou la recherche.</p>';
    get(target).querySelector(".page-heading").after(block);
  }
  const services = make("article", "panel");
  services.id = "next-services";
  services.innerHTML =
    '<h2>Les fonctions disponibles</h2><p id="next-service-health" role="status">Vérification des services…</p>';
  get("view-monitor").querySelector(".engine-panel").before(services);
  const settings = get("view-settings");
  settings.querySelector(".page-heading h1").textContent = "Paramètres";
  settings.querySelector(".page-heading p").textContent =
    "Ces commandes sont proposées dans le profil Famille, librement accessible sur le réseau local.";
  for (const h of settings.querySelectorAll(
    "article:has([data-view=users]) h2",
  )) {
    h.textContent = "Profils de la famille";
    h.nextElementSibling.textContent =
      "Créez un profil pour ranger les conversations et les favoris de chaque personne.";
    h.parentElement.querySelector("button").textContent = "Gérer les profils";
  }
  const tools = make("div", "next-settings-links");
  tools.innerHTML =
    route("appareil/profils", "Profils") +
    route("appareil/connexion", "Ouvrir sur un téléphone") +
    route("appareil/telechargements", "Téléchargements");
  settings.querySelector(".page-heading").after(tools);
  tools.after(
    make(
      "p",
      "next-mobile-note",
      "Les opérations complexes de préparation et les réglages du moteur se font depuis un ordinateur. Les profils et le suivi restent consultables ici.",
    ),
  );
  const searchCheck = make("article", "panel");
  searchCheck.innerHTML =
    '<h2>Vérifier la recherche</h2><p>Essayez les recherches pratiques de Marc sur les documents de cet appareil, sans lancer l’assistant IA.</p><label>Étendue du contrôle<select id="next-search-check-suite"><option value="short">Contrôle court · 10 recherches</option><option value="extended">Contrôle complet · 32 recherches</option></select></label><p class="small muted">Le contrôle complet peut prendre plusieurs minutes. Vous pourrez l’arrêter et conserver les résultats reçus.</p><button id="next-search-check-open" class="secondary">Vérifier la recherche</button>';
  settings.append(searchCheck);
  const searchDialog = make("dialog", "next-search-check-dialog");
  searchDialog.id = "next-search-check-dialog";
  searchDialog.setAttribute("aria-labelledby", "next-search-check-title");
  searchDialog.innerHTML =
    '<h2 id="next-search-check-title">Vérifier la recherche</h2><p>Ouvrez les résultats pour vérifier qu’ils répondent au besoin. Une recherche terminée ne garantit pas la qualité du document.</p><p id="next-search-check-status" role="status" aria-live="polite"></p><progress id="next-search-check-progress" max="10" value="0" aria-label="Recherches de test terminées"></progress><div class="actions"><button id="next-search-check-cancel" class="secondary">Arrêter la vérification</button><button id="next-search-check-export" class="secondary" hidden>Télécharger le rapport</button><button data-close="next-search-check-dialog" class="secondary">Fermer</button></div><p class="small muted">Le rapport liste les recherches de test, leurs délais et les titres trouvés.</p><div id="next-search-check-results"></div>';
  document.body.append(searchDialog);
  const usageOpen = make("button", "secondary", "Tester l’usage hors ligne");
  usageOpen.id = "next-usage-open";
  searchCheck.append(usageOpen);
  const usage = make("dialog", "next-search-check-dialog usage-recipe");
  usage.id = "next-usage-dialog";
  usage.setAttribute("aria-labelledby", "next-usage-title");
  usage.innerHTML = `<h2 id="next-usage-title">Tester l’usage hors ligne</h2>
    <p>Pour un essai hors ligne, coupez l’accès à Internet du serveur et de l’appareil utilisé, en conservant leur réseau local. Pour tester aussi sans IA, arrêtez l’assistant depuis Mon appareil lorsque personne ne l’utilise.</p>
    <p class="small muted">Deux recherches et deux aperçus au maximum, sans appel à l’IA. Arrêt possible ; durée limitée à 90 secondes. Les étapes humaines restent à vérifier.</p>
    <div class="usage-context"><label>Connexion pendant cet essai<select id="next-usage-network"><option value="unknown">Non précisée</option><option value="connected">Internet disponible</option><option value="disconnected">Internet coupé, réseau local conservé</option></select></label><label>Appareil utilisé<select id="next-usage-device"><option value="unknown">Non précisé</option><option value="windows">Ordinateur Windows</option><option value="linux">Ordinateur Linux</option><option value="ios">iPhone ou iPad</option><option value="android">Téléphone ou tablette Android</option><option value="other">Autre appareil</option></select></label></div>
    <p id="next-usage-status" role="status" aria-live="polite"></p>
    <div class="actions"><button id="next-usage-run">Lancer les contrôles</button><button id="next-usage-cancel" class="secondary" hidden>Arrêter</button><button id="next-usage-export" class="secondary">Télécharger le rapport d’usage</button><button id="next-usage-new" class="secondary">Nouvel essai</button><button data-close="next-usage-dialog" class="secondary">Fermer</button></div>
    <details open><summary>Contrôles automatiques</summary><div id="next-usage-results"></div></details>
    <details><summary>Étapes vérifiées par vous</summary><p class="small muted">Gardez « Non effectué » pour les essais non faits. Ouvrir un document dans un autre onglet conserve ce contrôle.</p><div id="next-usage-manual"></div></details>
    <details><summary>Après une maintenance prévue ou sur une copie d’essai</summary><p class="small muted">Ces étapes ne sont pas nécessaires à chaque essai. Les pannes de disque, index abîmés et coupures forcées se testent sur une copie jetable.</p><div id="next-usage-maintenance"></div></details>
    <label>Observation à joindre au rapport<textarea id="next-usage-note" rows="3" maxlength="600" placeholder="Un problème, le résultat attendu… sans mot de passe ni contenu de conversation."></textarea></label>
    <p class="small muted">Les étapes sont mémorisées dans ce navigateur pour ce profil et cette version. Les mesures sont à relancer après rechargement. Le rapport inclut votre observation, les mesures et les titres trouvés, sans conversation ni texte des documents.</p>`;
  document.body.append(usage);
  const indexTools = make("article", "panel");
  indexTools.innerHTML =
    '<h2>Rendre les archives recherchables</h2><p>Préparez l’outil une fois avec Internet, puis créez les index de texte sur ce PC, hors ligne et sans IA. Cette préparation peut durer longtemps ; les index déjà terminés restent utilisables.</p><p id="next-index-status" role="status"></p><div class="actions"><button id="next-index-prepare" class="secondary">Préparer l’outil · Internet requis</button><button id="next-index-start" class="secondary">Créer ou reprendre les index</button><button id="next-index-pause" class="secondary">Mettre en pause</button><button id="next-index-export" class="secondary">Télécharger le rapport d’indexation</button></div><details><summary>Préparation automatique après téléchargement</summary><form id="next-index-settings"><label><input type="checkbox" id="next-index-auto"> Préparer automatiquement les nouvelles archives vérifiées</label><label>À partir de (heure du PC serveur)<select id="next-index-from"></select></label><label>Jusqu’à<select id="next-index-until"></select></label><p class="small muted">Deux heures identiques : préparation possible à toute heure. Une pause volontaire reste prioritaire.</p><label>Processus en parallèle<select id="next-index-workers"><option value="0">Automatique selon les ressources</option><option value="1">1</option><option value="2">2</option><option value="4">4</option><option value="8">8</option><option value="16">16</option></select></label><button>Enregistrer</button><p id="next-index-settings-status" role="status"></p></form></details>';
  settings.append(indexTools);
  const contextTools = make("article", "panel");
  contextTools.innerHTML =
    '<h2>Mémoire de l’assistant</h2><p>Un contexte plus grand conserve davantage de conversation et de sources. Commencez à 16k ; augmentez après un essai sur ce PC en surveillant la mémoire et le délai. Le réglage s’applique à la prochaine réponse, sans démarrer l’IA.</p><form id="next-context-form"><label>Modèle<select id="next-context-model"></select></label><label>Contexte<select id="next-context-size"><option value="8192">8k</option><option value="16384">16k</option><option value="32768">32k</option><option value="65536">64k</option></select></label><button>Enregistrer</button><p id="next-context-status" role="status"></p></form>';
  settings.append(contextTools);
  const memory = make("article", "panel");
  memory.innerHTML =
    '<h2>Mémoire de navigation</h2><p>Effacez seulement les onglets, filtres et brouillons mémorisés sur ce navigateur. Vos conversations et favoris sur le serveur sont conservés.</p><button id="next-clear-memory" class="secondary">Effacer la mémoire de navigation</button>';
  settings.append(memory);
  get("view-chat").querySelector("h1").textContent =
    "Prenons le temps de comprendre.";
  const context = make("div", "next-chat-context");
  for (const selector of [
    "#inference-banner",
    "#chat-source",
    "#translation-panel",
    "#conversation-picker",
  ]) {
    const node = get("view-chat").querySelector(selector);
    if (node) context.append(node);
  }
  get("view-chat").querySelector(".chat-top").after(context);
  const bottom = make(
    "div",
    "next-mobile-tools",
    '<a class="native-webui" href="/">Open WebUI ↗</a><a href="/secours.html">Documents de secours ↗</a>',
  );
  document.querySelector("footer").before(bottom);
})();
