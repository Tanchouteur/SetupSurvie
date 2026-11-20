/* Écran de départ de l'onglet Rechercher : idées et dernières recherches.
 * Visible tant qu'aucune recherche n'est affichée. Les dernières recherches
 * restent dans ce navigateur, rangées par profil. */
(() => {
  const start = document.getElementById("search-start");
  const results = document.getElementById("search-results");
  const message = document.getElementById("search-message");
  const form = document.getElementById("library-search");
  if (!start || !results || !message) return;
  const recentBox = start.querySelector("[data-search-recent]");
  const recentList = start.querySelector("[data-search-recent-list]");
  const key = () => "survie-recent-searches:" + (typeof S !== "undefined" && S.user ? S.user.id : "anonyme");

  function read() {
    try { return JSON.parse(localStorage.getItem(key())) || []; } catch (_) { return []; }
  }
  function remember(query) {
    const text = String(query || "").trim();
    if (!text) return;
    const list = [text, ...read().filter((item) => item.toLowerCase() !== text.toLowerCase())].slice(0, 6);
    try { localStorage.setItem(key(), JSON.stringify(list)); } catch (_) { /* stockage plein ou refusé */ }
  }
  function renderRecent() {
    const list = read();
    recentBox.hidden = !list.length;
    recentList.replaceChildren(...list.map((query) => {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "secondary search-start-recent";
      button.textContent = query;
      button.addEventListener("click", () => typeof search === "function" && search(query));
      return button;
    }));
  }
  function sync() {
    const idle = !results.children.length && !message.textContent.trim();
    if (idle && start.hidden) renderRecent();
    start.hidden = !idle;
  }

  form?.addEventListener("submit", () => remember(document.getElementById("library-query")?.value), true);
  document.getElementById("home-search")?.addEventListener("submit", () => remember(document.getElementById("home-query")?.value), true);
  document.addEventListener("click", (event) => {
    const chip = event.target.closest?.("[data-search]");
    if (chip) remember(chip.dataset.search);
  }, true);
  new MutationObserver(sync).observe(results, { childList: true });
  new MutationObserver(sync).observe(message, { childList: true, characterData: true, subtree: true });
  document.addEventListener("survie:profile", renderRecent);

  /* Téléphone : les filtres (collection, langue, type) se replient sous
   * « Filtres » pour laisser le champ de recherche en premier. */
  if (form) {
    const toggle = document.createElement("button");
    toggle.type = "button";
    toggle.className = "secondary search-filters-toggle no-busy";
    toggle.setAttribute("aria-expanded", "false");
    const label = () => {
      const changed = [...form.querySelectorAll("select")].filter((select) => select.selectedIndex > 0).length;
      toggle.textContent = changed ? `Filtres (${changed})` : "Filtres";
    };
    toggle.addEventListener("click", () => {
      const open = form.classList.toggle("filters-open");
      toggle.setAttribute("aria-expanded", String(open));
    });
    form.addEventListener("change", label);
    const submit = form.querySelector("button[type=submit], button:not([type])");
    form.insertBefore(toggle, submit || null);
    label();
  }
  renderRecent();
  sync();
})();
