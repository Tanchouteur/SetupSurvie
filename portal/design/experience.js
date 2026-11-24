/* Presentation helpers only: position cues, reading progress and the quick-access
   palette. No API call or stored state; every action reuses an existing route or control. */
(() => {
  const $ = (id) => document.getElementById(id);
  const reduced = matchMedia("(prefers-reduced-motion: reduce)");
  const isMac = /Mac|iPhone|iPad/.test(navigator.platform || "");
  const fold = (text) => text.normalize("NFD").replace(/\p{M}/gu, "").toLowerCase();

  /* A marker that travels to the current item of a navigation group. */
  function indicator(container, className, selector) {
    let mark = container.querySelector(":scope > ." + className);
    if (!mark) {
      mark = document.createElement("span");
      mark.className = className;
      mark.setAttribute("aria-hidden", "true");
      container.prepend(mark);
      container.classList.add("ds-has-indicator");
    }
    const target = container.querySelector(selector);
    if (!target || !target.offsetWidth) { mark.style.opacity = "0"; return; }
    mark.style.opacity = "";
    mark.style.setProperty("--ds-x", target.offsetLeft + "px");
    mark.style.setProperty("--ds-w", target.offsetWidth + "px");
    requestAnimationFrame(() => mark.classList.add("ds-ready"));
    if (container.scrollWidth > container.clientWidth) {
      container.scrollTo({ left: target.offsetLeft - 24, behavior: reduced.matches ? "auto" : "smooth" });
    }
  }
  function placeIndicators() {
    const nav = $("navigation");
    if (nav) indicator(nav, "ds-nav-indicator", ".nav-item.active");
    document.querySelectorAll(".view:not([hidden]) .next-tabs").forEach((tabs) =>
      indicator(tabs, "ds-tab-indicator", 'a[aria-current="page"]'));
  }

  /* Reading progress of the open document. */
  let progress, ticking = false;
  function measure() {
    ticking = false;
    document.body.classList.toggle("ds-scrolled", scrollY > 6);
    const reader = $("reader");
    const open = reader && !reader.hidden && reader.offsetParent !== null;
    if (progress) progress.hidden = !open;
    if (!open || !progress) return;
    const box = reader.getBoundingClientRect();
    const span = box.height - innerHeight * 0.6;
    const done = span > 0 ? Math.min(1, Math.max(0, -box.top / span)) : 0;
    progress.style.setProperty("--ds-progress", done.toFixed(4));
  }
  const schedule = () => { if (!ticking) { ticking = true; requestAnimationFrame(measure); } };

  /* Quick access */
  const go = (hash) => () => { location.hash = hash; };
  const actions = [
    ["Aller à", "Accueil", go("#/accueil")],
    ["Aller à", "Rechercher dans la bibliothèque", () => { focusLater("library-query"); location.hash = "#/bibliotheque/recherche"; }],
    ["Aller à", "Collections", go("#/bibliotheque/collections")],
    ["Aller à", "Apprendre par thème", go("#/bibliotheque/parcours")],
    ["Aller à", "Mes favoris", go("#/bibliotheque/favoris")],
    ["Aller à", "Traductions", go("#/bibliotheque/traductions")],
    ["Aller à", "Assistant", () => { focusLater("chat-input"); location.hash = "#/assistant"; }],
    ["Aller à", "Nouvelle discussion", () => { afterRoute(() => { $("chat-reset")?.click(); $("chat-input")?.focus(); }); location.hash = "#/assistant"; }],
    ["Aller à", "Cartes hors ligne", () => { location.href = "/cartes.html"; }],
    ["Aller à", "État de l’appareil", go("#/appareil/ensemble")],
    ["Aller à", "File d’attente", go("#/file")],
    ["Aller à", "Paramètres", go("#/appareil/reglages")],
    ["Aller à", "Documents de secours", () => { location.href = "/secours.html"; }],
  ].map(([group, label, run]) => ({ group, label, run, key: fold(label) }));
  /* The router moves focus to the page once it has changed: act just after it. */
  function afterRoute(action) {
    let done = false;
    const finish = () => { if (done) return; done = true; requestAnimationFrame(() => setTimeout(action, 0)); };
    document.addEventListener("survie:route", finish, { once: true });
    setTimeout(finish, 180);
  }
  function focusLater(id) { afterRoute(() => $(id)?.focus()); }

  let dialog, input, list, shown = [], selected = 0, opener = null;
  function results(query) {
    const text = query.trim();
    const wanted = fold(text);
    const found = actions.filter((item) => !wanted || wanted.split(/\s+/).every((word) => item.key.includes(word)));
    if (!text) return found;
    return [
      { group: "Avec votre texte", kind: "search", label: "Chercher « " + text + " » dans la bibliothèque",
        run: () => { location.hash = "#/bibliotheque/recherche?" + new URLSearchParams({ q: text, lang: "" }); } },
      { group: "Avec votre texte", kind: "ask", label: "Préparer la question « " + text + " » pour l’assistant",
        run: () => { afterRoute(() => { const box = $("chat-input"); if (box) { box.value = text; box.dispatchEvent(new Event("input", { bubbles: true })); box.focus(); } }); location.hash = "#/assistant"; } },
      ...found,
    ];
  }
  function select(index) {
    selected = (index + shown.length) % shown.length;
    list.querySelectorAll(".ds-palette-item").forEach((row, position) => {
      const on = position === selected;
      row.setAttribute("aria-selected", String(on));
      if (on) { input.setAttribute("aria-activedescendant", row.id); row.scrollIntoView({ block: "nearest" }); }
    });
  }
  function draw() {
    shown = results(input.value);
    list.replaceChildren();
    let group = "";
    shown.forEach((item, position) => {
      if (item.group !== group) {
        group = item.group;
        const title = document.createElement("li");
        title.className = "ds-palette-group";
        title.setAttribute("role", "presentation");
        title.textContent = group;
        list.append(title);
      }
      const row = document.createElement("li");
      row.className = "ds-palette-item";
      row.id = "ds-palette-" + position;
      row.setAttribute("role", "option");
      if (item.kind) row.dataset.kind = item.kind;
      row.textContent = item.label;
      row.addEventListener("pointermove", () => { if (selected !== position) select(position); });
      row.addEventListener("click", () => run(position));
      list.append(row);
    });
    if (shown.length) select(0);
  }
  function run(position) {
    const item = shown[position];
    if (!item) return;
    opener = null;
    dialog.close();
    item.run();
  }
  function build() {
    dialog = document.createElement("dialog");
    dialog.className = "ds-palette";
    dialog.setAttribute("aria-label", "Accès rapide");
    const field = document.createElement("div");
    field.className = "ds-palette-field";
    input = document.createElement("input");
    input.type = "text";
    input.placeholder = "Chercher, poser une question, aller à…";
    input.setAttribute("aria-label", "Accès rapide");
    input.setAttribute("role", "combobox");
    input.setAttribute("aria-expanded", "true");
    input.setAttribute("aria-controls", "ds-palette-list");
    input.autocomplete = "off";
    field.append(input);
    list = document.createElement("ul");
    list.className = "ds-palette-list";
    list.id = "ds-palette-list";
    list.setAttribute("role", "listbox");
    const foot = document.createElement("div");
    foot.className = "ds-palette-foot";
    for (const [key, label] of [["↑↓", "parcourir"], ["Entrée", "ouvrir"], ["Échap", "fermer"]]) {
      const hint = document.createElement("span");
      const mark = document.createElement("kbd");
      mark.textContent = key;
      hint.append(mark, " " + label);
      foot.append(hint);
    }
    dialog.append(field, list, foot);
    document.body.append(dialog);
    input.addEventListener("input", draw);
    input.addEventListener("keydown", (event) => {
      if (event.key === "ArrowDown") { event.preventDefault(); select(selected + 1); }
      else if (event.key === "ArrowUp") { event.preventDefault(); select(selected - 1); }
      else if (event.key === "Enter") { event.preventDefault(); run(selected); }
    });
    dialog.addEventListener("click", (event) => { if (event.target === dialog) dialog.close(); });
    dialog.addEventListener("close", () => { opener?.focus?.(); opener = null; });
  }
  function openPalette() {
    if (!dialog) build();
    if (dialog.open) return;
    opener = document.activeElement;
    input.value = "";
    draw();
    dialog.showModal();
    input.focus();
  }
  function trigger() {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "ds-search-trigger";
    button.setAttribute("aria-label", "Accès rapide : chercher ou aller à une page");
    button.title = "Accès rapide (" + (isMac ? "⌘" : "Ctrl") + " K)";
    const icon = document.createElement("span");
    icon.className = "ds-icon";
    const label = document.createElement("span");
    label.className = "ds-label";
    label.textContent = "Accès rapide";
    const key = document.createElement("kbd");
    key.textContent = (isMac ? "⌘" : "Ctrl ") + "K";
    button.append(icon, label, key);
    button.addEventListener("click", openPalette);
    return button;
  }
  document.addEventListener("keydown", (event) => {
    if ((event.ctrlKey || event.metaKey) && !event.altKey && event.key.toLowerCase() === "k") {
      event.preventDefault();
      openPalette();
      return;
    }
    const target = event.target;
    const typing = target instanceof Element && target.closest("input, textarea, select, [contenteditable]");
    if (event.key === "/" && !typing && !event.ctrlKey && !event.metaKey && !event.altKey && !document.querySelector("dialog[open]")) {
      event.preventDefault();
      openPalette();
    }
  });

  function markCurrentResult(reveal) {
    const rail = $("search-results");
    if (!rail) return;
    const current = rail.parentElement.classList.contains("reading") && !$("reader").hidden ? S.reader : null;
    const rows = [...rail.querySelectorAll(":scope > .result")];
    const active = rows.find((row) => row.dataset.source === current) ||
      rows.find((row) => [...row.querySelectorAll("[data-result-passage]")].some((link) => link.dataset.resultPassage === current));
    for (const row of rows) {
      row.classList.toggle("selected", row === active);
      if (row === active) row.setAttribute("aria-current", "true");
      else row.removeAttribute("aria-current");
    }
    if (reveal && active && rail.clientHeight && rail.scrollHeight > rail.clientHeight) {
      const frame = rail.getBoundingClientRect();
      const row = active.getBoundingClientRect();
      if (row.top < frame.top + 8 || row.bottom > frame.bottom - 8) {
        const target = rail.scrollTop + row.top - frame.top - 8;
        rail.scrollTo({ top: target, behavior: reduced.matches ? "instant" : "smooth" });
      }
    }
  }

  function start() {
    /* La version et l’état de connexion sont écrits dans le pied de page de modele.html. */
    document.querySelector(".sidebar-bottom")?.prepend(trigger());
    document.querySelector(".top-actions")?.prepend(trigger());
    /* A few sparks above the fire. */
    const welcome = document.querySelector(".next-welcome");
    if (welcome && !reduced.matches) {
      const sparks = document.createElement("div");
      sparks.className = "ds-embers";
      sparks.setAttribute("aria-hidden", "true");
      sparks.innerHTML = "<i></i><i></i><i></i><i></i>";
      welcome.append(sparks);
    }
    progress = document.createElement("div");
    progress.className = "ds-read-progress";
    progress.hidden = true;
    progress.setAttribute("aria-hidden", "true");
    document.body.append(progress);
    addEventListener("scroll", schedule, { passive: true });
    addEventListener("resize", () => { placeIndicators(); schedule(); }, { passive: true });
    for (const name of ["survie:route", "survie:source", "survie:results"]) {
      document.addEventListener(name, () => requestAnimationFrame(() => { placeIndicators(); schedule(); }));
    }
    document.addEventListener("survie:source", () => requestAnimationFrame(() => markCurrentResult(true)));
    document.addEventListener("survie:route", () => requestAnimationFrame(() => markCurrentResult(false)));
    document.addEventListener("survie:results", () => requestAnimationFrame(() => markCurrentResult(false)));
    document.fonts?.ready.then(placeIndicators);
    placeIndicators();
    schedule();
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", start, { once: true });
  else start();
  window.SurvieDesign = Object.freeze({ openPalette });
})();
