/* Mon appareil → Vue d'ensemble : une réponse avant les mesures.
 *
 * « Tout fonctionne » ou « N points à regarder », chaque point avec une
 * explication et une action. Les mesures détaillées (modèle chargé, RAM,
 * VRAM, services) restent affichées en dessous, inchangées.
 * Sources : événements `survie:connection`, `survie:inference`,
 * `survie:work-queue`, et `/api/health` pour les fonctions dégradées.
 */
(() => {
  const view = document.getElementById("view-monitor");
  if (!view) return;
  const card = document.createElement("section");
  card.id = "device-summary";
  card.className = "device-summary";
  card.setAttribute("aria-live", "polite");
  card.setAttribute("aria-labelledby", "device-summary-title");
  card.innerHTML = `
    <div class="device-summary-head">
      <span class="device-summary-icon" aria-hidden="true"></span>
      <div>
        <h2 id="device-summary-title">Vérification en cours…</h2>
        <p class="device-summary-sub muted"></p>
      </div>
    </div>
    <ul class="device-summary-list"></ul>`;
  view.querySelector(".page-heading")?.after(card);
  const title = card.querySelector("h2");
  const sub = card.querySelector(".device-summary-sub");
  const list = card.querySelector(".device-summary-list");

  const facts = { online: window.SurvieNet ? window.SurvieNet.state().online : true, inference: null, queue: undefined, degraded: [] };
  const admin = () => typeof S !== "undefined" && S.user?.role === "admin";
  const ratio = (item) => item && Number.isFinite(item.used) && Number.isFinite(item.total) && item.total > 0 ? item.used / item.total : null;

  function points() {
    const out = [];
    if (!facts.online) {
      out.push({ tone: "danger", title: "L’appareil ne répond pas", text: "Vérifiez qu’il est allumé et que vous êtes sur le même réseau Wi-Fi. La page se mettra à jour seule dès son retour.", action: ["Documents de secours", "/secours.html"] });
      return out;
    }
    const inf = facts.inference;
    if (inf && !inf.observation_error) {
      if (inf.operation === "start") out.push({ tone: "info", title: "L’assistant démarre", text: "Comptez environ une minute. La bibliothèque reste utilisable." });
      else if (inf.paused) out.push({ tone: "warn", title: "Assistant en pause (mode jeu)", text: "Les questions attendront la reprise. La bibliothèque reste disponible.", action: admin() ? ["Reprendre l’assistant", "#engine-start"] : null });
      else if (!inf.online && !inf.operation) out.push({ tone: "warn", title: "Assistant arrêté", text: "Vous pouvez lire et chercher dans la bibliothèque. Démarrez l’assistant pour poser des questions.", action: admin() ? ["Démarrer l’assistant", "#engine-start"] : null });
      if (inf.control_available === false) out.push({ tone: "info", title: "Mesures du PC indisponibles", text: "Le service qui mesure la mémoire et le modèle chargé ne répond pas. Cela n’empêche pas forcément l’assistant de répondre." });
      const ram = ratio(inf.memory);
      const gpus = Array.isArray(inf.gpus) && inf.gpus.length ? inf.gpus : null;
      const vram = gpus ? ratio({ used: gpus.reduce((s, g) => s + (g.used || 0), 0), total: gpus.reduce((s, g) => s + (g.total || 0), 0) }) : null;
      if (ram !== null && ram >= 0.9) out.push({ tone: "warn", title: `Mémoire du PC presque pleine (${Math.round(ram * 100)} %)`, text: "Les réponses peuvent ralentir. Fermez les applications inutiles sur le PC si possible." });
      if (vram !== null && vram >= 0.95) out.push({ tone: "info", title: `Carte graphique très occupée (${Math.round(vram * 100)} %)`, text: "Un jeu ou un modèle chargé utilise la mémoire vidéo ; les réponses peuvent être plus lentes." });
    } else if (inf?.observation_error) {
      out.push({ tone: "info", title: "État de l’assistant inconnu", text: "La vérification n’a pas abouti ; elle sera refaite automatiquement." });
    }
    if (facts.queue) {
      const jobs = (Array.isArray(facts.queue.jobs) ? facts.queue.jobs : []).filter((job) => !(job.dismissible && job.seen));
      const errors = jobs.filter((job) => ["error", "failed"].includes(job.status)).length;
      if (errors) out.push({ tone: "danger", title: errors === 1 ? "Une tâche a échoué" : `${errors} tâches ont échoué`, text: "Ouvrez la file pour lire le message et la marche à suivre.", action: ["Ouvrir les tâches", "#/file"] });
      if (facts.queue.paused) out.push({ tone: "warn", title: "La file des tâches est en pause", text: "Les téléchargements et préparations attendent sa reprise.", action: ["Ouvrir les tâches", "#/file"] });
    }
    for (const feature of facts.degraded) {
      out.push({ tone: "warn", title: "Fonction réduite : " + feature, text: "Le reste du portail fonctionne. Un redémarrage de l’appareil peut suffire." });
    }
    return out;
  }

  function place() {
    /* Les mesures sont rangées par d'autres modules au chargement : le résumé se
     * place juste avant elles, sous les onglets de Mon appareil. */
    const metrics = document.getElementById("settings-server-metrics");
    if (metrics && metrics.parentElement && card.nextElementSibling !== metrics) metrics.before(card);
  }

  function render() {
    place();
    const items = points();
    const serious = items.filter((item) => item.tone !== "info");
    card.dataset.state = !facts.online ? "danger" : serious.some((i) => i.tone === "danger") ? "danger" : serious.length ? "warn" : "ok";
    title.textContent = !facts.online ? "L’appareil ne répond pas"
      : serious.length ? (serious.length === 1 ? "Un point à regarder" : `${serious.length} points à regarder`)
      : "Tout fonctionne";
    sub.textContent = serious.length || !facts.online ? "Chaque point indique quoi faire."
      : "Bibliothèque, recherche et cartes sont disponibles." + (facts.inference?.online ? " L’assistant est prêt." : "");
    list.replaceChildren(...items.map((item) => {
      const li = document.createElement("li");
      li.dataset.tone = item.tone;
      const strong = document.createElement("strong");
      strong.textContent = item.title;
      const p = document.createElement("p");
      p.textContent = item.text;
      li.append(strong, p);
      if (item.action) {
        const [label, target] = item.action;
        const link = document.createElement(target.startsWith("#engine") ? "button" : "a");
        link.className = target.startsWith("#engine") ? "secondary" : "text-button";
        link.textContent = label;
        if (link.tagName === "A") { link.href = target; if (target.startsWith("/")) link.target = "_blank"; }
        else { link.type = "button"; link.addEventListener("click", () => document.querySelector(target)?.click()); }
        li.append(link);
      }
      return li;
    }));
    list.hidden = !items.length;
  }

  async function health() {
    try {
      const data = await (await fetch("/api/health", { cache: "no-store" })).json();
      facts.degraded = Array.isArray(data.degraded_features) ? data.degraded_features : [];
    } catch (_) { /* la connexion est suivie par SurvieNet */ }
    render();
  }

  document.addEventListener("survie:connection", (e) => { facts.online = e.detail.online; render(); if (facts.online) health(); });
  document.addEventListener("survie:inference", (e) => { facts.inference = e.detail; render(); });
  document.addEventListener("survie:work-queue", (e) => { facts.queue = e.detail; render(); });
  document.addEventListener("survie:view", () => { if (!view.hidden) health(); });
  if (typeof S !== "undefined" && S.inference) facts.inference = S.inference;
  render();
  health();
})();
