/* Mon appareil : espace disque.
 *
 * Vue d'ensemble : une carte pleine largeur, une barre par disque concerné
 * (SetupSurvie, copies de sécurité, autres fichiers du PC, espace libre).
 * Stockage : l'analyse détaillée (catégories → éléments → plus gros fichiers).
 * Source : `/api/storage`, mesuré par le contrôleur du PC serveur. Repli sur
 * `disk` de `/api/inference` (total, utilisé, libre) quand l'analyse manque.
 */
(() => {
  const monitor = document.getElementById("view-monitor");
  const storage = document.getElementById("view-storage");
  if (!monitor) return;
  const UNITS = ["octets", "Ko", "Mo", "Go", "To"];
  const number = (value, digits) => new Intl.NumberFormat("fr-FR", { maximumFractionDigits: digits, minimumFractionDigits: 0 }).format(value);
  // Base 1024, comme l'Explorateur Windows, pour que les chiffres se comparent.
  function size(value) {
    if (!Number.isFinite(value) || value < 0) return "taille inconnue";
    let unit = 0;
    while (value >= 1024 && unit < UNITS.length - 1) { value /= 1024; unit++; }
    return number(value, unit < 2 ? 0 : value >= 100 ? 0 : 1) + " " + UNITS[unit];
  }
  const percent = (part, total) => total > 0 ? Math.max(0, Math.min(100, (part / total) * 100)) : 0;
  const make = (tag, cls, text) => { const node = document.createElement(tag); if (cls) node.className = cls; if (text !== undefined) node.textContent = text; return node; };
  const admin = () => typeof S !== "undefined" && S.user?.role === "admin";
  function ago(seconds) {
    const minutes = Math.round((Date.now() / 1000 - seconds) / 60);
    if (minutes < 1) return "à l’instant";
    if (minutes < 60) return `il y a ${minutes} min`;
    const hours = Math.round(minutes / 60);
    if (hours < 48) return `il y a ${hours} h`;
    return `il y a ${Math.round(hours / 24)} jours`;
  }

  let data = null, inferenceDisk = null, timer = 0, loading = null;

  /* Une barre segmentée + sa légende pour un disque. */
  function parts(disk) {
    const survie = disk.setupsurvie ?? null, backups = disk.backups || 0;
    const other = survie === null ? disk.used : Math.max(0, disk.used - survie - backups);
    const list = [];
    if (survie !== null) list.push({ key: "survie", label: "SetupSurvie", bytes: survie });
    if (backups) list.push({ key: "backups", label: "Copies de sécurité", bytes: backups });
    list.push({ key: "other", label: survie === null ? "Utilisé" : "Autres fichiers du PC", bytes: other });
    list.push({ key: "free", label: "Libre", bytes: disk.free });
    return list;
  }
  function tone(disk) {
    const free = disk.total > 0 ? disk.free / disk.total : 1;
    return free < 0.05 ? "danger" : free < 0.1 ? "warn" : "ok";
  }
  function bar(disk) {
    const wrap = make("div", "storage-disk");
    wrap.dataset.tone = tone(disk);
    const head = make("div", "storage-disk-head");
    head.append(make("strong", "", disk.data ? `Disque ${disk.label}` : `Disque ${disk.label} · copies de sécurité`),
      make("span", "muted", `${size(disk.total)} · ${number(percent(disk.used, disk.total), 0)} % occupé`));
    const track = make("div", "storage-bar");
    track.setAttribute("role", "img");
    const legend = make("ul", "storage-legend");
    const items = parts(disk);
    track.setAttribute("aria-label", items.map((p) => `${p.label} ${size(p.bytes)}`).join(", "));
    for (const part of items) {
      const share = percent(part.bytes, disk.total);
      if (part.key !== "free" && share > 0) {
        const segment = make("span", "storage-segment");
        segment.dataset.part = part.key;
        segment.style.flexBasis = Math.max(share, 0.6) + "%";
        segment.title = `${part.label} : ${size(part.bytes)}`;
        track.append(segment);
      }
      const entry = make("li");
      entry.dataset.part = part.key;
      entry.append(make("span", "storage-dot"), make("span", "", part.label + " "), make("strong", "", size(part.bytes)));
      legend.append(entry);
    }
    wrap.append(head, track, legend);
    return wrap;
  }
  function concerned(disks) {
    /* La vue d'ensemble montre le disque des données et ceux qui portent des copies. */
    const list = (disks || []).filter((disk) => disk.total > 0 && (disk.data || disk.backups));
    return list.length ? list : (disks || []).filter((disk) => disk.total > 0).slice(0, 1);
  }
  function fallbackDisks() {
    const disk = inferenceDisk;
    return disk && disk.total > 0 ? [{ id: "data", label: "des données", total: disk.total, used: disk.used, free: disk.free, data: true }] : [];
  }

  /* ---------- Carte de la vue d'ensemble ---------- */
  const card = make("a", "storage-summary");
  card.id = "storage-summary";
  card.href = "#/appareil/stockage";
  card.dataset.route = "appareil/stockage";
  card.setAttribute("aria-labelledby", "storage-summary-title");
  const cardHead = make("div", "storage-summary-head");
  const cardTitle = make("h2", "", "Espace disque");
  cardTitle.id = "storage-summary-title";
  const cardSentence = make("p", "muted storage-summary-sentence", "Mesure de l’espace disque…");
  const cardTitles = make("div");
  cardTitles.append(cardTitle, cardSentence);
  cardHead.append(cardTitles, make("span", "storage-summary-open", "Analyser le stockage"));
  const cardDisks = make("div", "storage-disks");
  card.append(cardHead, cardDisks);

  function place() {
    // Après « Mémoire et modèle chargé » : le résumé puis les mesures restent en tête.
    const metrics = document.getElementById("settings-server-metrics");
    const summary = document.getElementById("device-summary");
    const anchor = [metrics, summary].find((node) => node && node.parentElement === monitor) || monitor.querySelector(".page-heading");
    if (anchor && anchor.nextElementSibling !== card) anchor.after(card);
  }
  function sentence(report, disks) {
    const main = disks.find((disk) => disk.data) || disks[0];
    if (!main) return data?.available === false ? "Le PC serveur ne transmet pas encore la mesure du disque." : "Mesure de l’espace disque…";
    let text = `${size(main.free)} libres sur ${size(main.total)}`;
    if (report) text += ` — SetupSurvie occupe ${size(report.total)}`;
    if (report?.backups) text += `, ses copies de sécurité ${size(report.backups)}`;
    if (tone(main) === "danger") text = "Disque presque plein : " + text;
    else if (tone(main) === "warn") text = "Peu d’espace libre : " + text;
    return text + ".";
  }
  function renderCard() {
    place();
    const report = data?.report || null;
    const disks = concerned(report ? report.disks : data?.disks?.length ? data.disks : fallbackDisks());
    card.dataset.tone = disks.length ? tone(disks.find((disk) => disk.data) || disks[0]) : "ok";
    cardSentence.textContent = sentence(report, disks) + (data?.scanning && !report ? " Analyse détaillée en cours…" : "");
    cardDisks.replaceChildren(...disks.map(bar));
    document.dispatchEvent(new CustomEvent("survie:storage", { detail: { disks } }));
  }

  /* ---------- Analyse détaillée (page Stockage) ---------- */
  const analysis = make("section", "storage-analysis");
  analysis.id = "storage-analysis";
  analysis.setAttribute("aria-labelledby", "storage-analysis-title");
  const analysisHead = make("div", "storage-analysis-head");
  const analysisTitle = make("h2", "", "Analyse de l’espace");
  analysisTitle.id = "storage-analysis-title";
  const analysisMeta = make("p", "muted small");
  analysisMeta.setAttribute("aria-live", "polite");
  const rescan = make("button", "secondary", "Analyser à nouveau");
  rescan.type = "button";
  const headText = make("div");
  headText.append(analysisTitle, analysisMeta);
  analysisHead.append(headText, rescan);
  const analysisDisks = make("div", "storage-disks");
  const totals = make("ul", "storage-totals");
  const categories = make("div", "storage-categories");
  analysis.append(analysisHead, analysisDisks, totals, categories);
  if (storage) {
    // Sous le titre et le retour « ← Paramètres · Bibliothèque ».
    const anchor = storage.querySelector(":scope > .settings-back") || storage.querySelector(".page-heading");
    if (anchor) anchor.after(analysis); else storage.prepend(analysis);
  }
  const opened = new Set();
  categories.addEventListener("toggle", (event) => {
    const node = event.target;
    if (node.tagName !== "DETAILS" || !node.dataset.key) return;
    if (node.open) opened.add(node.dataset.key); else opened.delete(node.dataset.key);
  }, true);

  function disclosure(key, summaryNodes, body, cls) {
    const details = make("details", cls);
    details.dataset.key = key;
    details.open = opened.has(key);
    const summary = make("summary");
    summary.append(...summaryNodes);
    details.append(summary, body);
    return details;
  }
  function meter(share) {
    const track = make("span", "storage-meter");
    const fill = make("span");
    fill.style.width = Math.max(share, share > 0 ? 1 : 0) + "%";
    track.append(fill);
    track.setAttribute("aria-hidden", "true");
    return track;
  }
  function itemRow(item, total) {
    const name = make("span", "storage-row-name");
    name.append(make("strong", "", item.label));
    if (item.rebuildable) name.append(make("span", "storage-badge", "reconstructible"));
    if (item.estimated) name.append(make("span", "storage-badge", "taille déclarée"));
    if (item.unreadable) name.append(make("span", "storage-badge", "accès partiel"));
    const nodes = [name, meter(percent(item.bytes, total)), make("span", "storage-row-size", size(item.bytes))];
    const body = make("div", "storage-item-body");
    const facts = [item.note, `${number(item.files, 0)} fichier${item.files > 1 ? "s" : ""}`];
    if (item.unreadable) facts.push(`${number(item.unreadable, 0)} dossier(s) illisible(s) par le service : taille minimale.`);
    body.append(make("p", "muted small", facts.filter(Boolean).join(" · ")));
    if (item.top?.length) {
      const list = make("ol", "storage-top");
      for (const entry of item.top) {
        const row = make("li");
        row.append(make("span", "storage-top-name", entry.name), meter(percent(entry.bytes, item.bytes)), make("span", "storage-row-size", size(entry.bytes)));
        list.append(row);
      }
      body.append(list);
    }
    return disclosure("item:" + item.id, nodes, body, "storage-item");
  }
  function renderAnalysis() {
    if (!storage) return;
    const report = data?.report || null;
    rescan.hidden = !admin() || data?.available === false;
    rescan.disabled = !!data?.scanning;
    rescan.textContent = data?.scanning ? "Analyse en cours…" : "Analyser à nouveau";
    if (data?.available === false) {
      analysisMeta.textContent = data.reason === "controller_update_required"
        ? "Le service du PC serveur doit être mis à jour pour analyser le disque."
        : "Le service du PC serveur ne répond pas : l’analyse détaillée est indisponible.";
    } else if (!report) {
      analysisMeta.textContent = data?.error || (data?.scanning ? "Première analyse en cours : de quelques secondes à quelques minutes selon le nombre de fichiers." : "Aucune analyse pour le moment.");
    } else {
      analysisMeta.textContent = `Dernière analyse ${ago(report.scanned_at)} (${number(report.duration_ms / 1000, 1)} s). L’espace libre est mis à jour en direct.` + (data.scanning ? " Nouvelle analyse en cours…" : "") + (data.error ? " " + data.error : "");
    }
    const disks = report ? report.disks : data?.disks?.length ? data.disks : fallbackDisks();
    analysisDisks.replaceChildren(...disks.filter((disk) => disk.total > 0).map(bar));
    totals.replaceChildren();
    categories.replaceChildren();
    if (!report) return;
    const total = report.total + report.backups;
    const chip = (label, value, part) => { const li = make("li"); if (part) li.dataset.part = part; li.append(make("span", "muted", label), make("strong", "", size(value))); return li; };
    totals.append(chip("SetupSurvie", report.total, "survie"));
    if (report.backups) totals.append(chip("Copies de sécurité", report.backups, "backups"));
    if (report.rebuildable) totals.append(chip("Dont reconstructible", report.rebuildable));
    const largest = Math.max(...report.categories.map((category) => category.bytes), 1);
    for (const category of report.categories) {
      const members = report.items.filter((item) => item.category === category.id);
      const nodes = [make("strong", "storage-row-name", category.label), meter(percent(category.bytes, largest)),
        make("span", "storage-row-size", `${size(category.bytes)} · ${number(percent(category.bytes, total), 1)} %`)];
      const body = make("div", "storage-items");
      body.append(...members.map((item) => itemRow(item, category.bytes)));
      categories.append(disclosure("category:" + category.id, nodes, body, "storage-category"));
    }
  }

  /* ---------- Données ---------- */
  function visible() {
    return !document.hidden && ((!monitor.hidden) || (storage && !storage.hidden));
  }
  async function load() {
    if (loading) return loading;
    loading = (async () => {
      try { data = await api("/storage"); }
      catch (_) { data = data || { available: false, reason: "controller_unavailable" }; }
      finally { loading = null; }
      renderCard();
      renderAnalysis();
      clearTimeout(timer);
      // Pendant une analyse, l'état est relu souvent ; sinon une fois par minute.
      if (visible()) timer = setTimeout(load, data?.scanning ? 3000 : 60000);
    })();
    return loading;
  }
  rescan.addEventListener("click", async () => {
    rescan.disabled = true;
    try {
      await api("/admin/storage/scan", {});
      if (data) data.scanning = true;
      renderAnalysis();
      clearTimeout(timer);
      timer = setTimeout(load, 1500);
    } catch (error) {
      rescan.disabled = false;
      if (typeof toast === "function") toast(error.message);
    }
  });
  document.addEventListener("survie:inference", (event) => {
    const disk = event.detail?.disk;
    if (disk && disk.total > 0) { inferenceDisk = disk; if (!data?.report && !data?.disks?.length) { renderCard(); renderAnalysis(); } }
  });
  document.addEventListener("survie:route", (event) => {
    const { section, tab } = event.detail || {};
    if (section === "appareil" && (tab === "ensemble" || tab === "stockage")) load();
    else clearTimeout(timer);
  });
  document.addEventListener("survie:auth", renderAnalysis);
  document.addEventListener("visibilitychange", () => { if (document.hidden) clearTimeout(timer); else if (visible()) load(); });
  renderCard();
  renderAnalysis();
})();
