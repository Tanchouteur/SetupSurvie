/* Assistant : état en mots simples près de la zone de saisie, et étapes
 * visibles pendant la préparation d'une réponse.
 *
 * - `#assistant-ready` résume l'état du moteur (prêt, démarre, arrêté, en
 *   pause, injoignable) à partir des événements `survie:inference` et
 *   `survie:connection`. La jauge « Modèle chargé / RAM / VRAM » de l'en-tête
 *   reste la mesure détaillée.
 * - Pendant une réponse, `survie:job` alimente une petite frise d'étapes
 *   (préparer, chercher, lire, rédiger) dans le message en cours.
 * Aucune requête propre.
 */
(() => {
  const form = document.getElementById("chat-form");
  if (!form) return;
  const reduced = matchMedia("(prefers-reduced-motion: reduce)");

  /* ---------- État du moteur ---------- */
  const status = document.createElement("p");
  status.id = "assistant-ready";
  status.className = "assistant-ready";
  status.setAttribute("aria-live", "polite");
  status.hidden = true;
  const dot = document.createElement("span");
  dot.className = "assistant-ready-dot";
  dot.setAttribute("aria-hidden", "true");
  const text = document.createElement("span");
  const action = document.createElement("button");
  action.type = "button";
  action.className = "text-button assistant-ready-action";
  action.hidden = true;
  status.append(dot, text, action);
  form.prepend(status);

  let inference = null;
  let connected = window.SurvieNet ? window.SurvieNet.state().online : true;

  function admin() { return typeof S !== "undefined" && S.user?.role === "admin"; }

  function describe() {
    if (!connected) return ["offline", "L’appareil ne répond pas : l’assistant reviendra avec la connexion."];
    if (!inference) return null;
    if (inference.observation_error) return ["unknown", "État de l’assistant en cours de vérification…"];
    if (inference.operation === "start") return ["busy", "L’assistant démarre. Comptez environ une minute ; la bibliothèque reste utilisable."];
    if (inference.operation === "stop") return ["busy", "Arrêt de l’assistant en cours…"];
    if (inference.operation) return ["busy", "L’assistant change de réglage. Votre question pourra être envoyée ensuite."];
    if (inference.paused) return ["paused", "Assistant en pause (mode jeu). La bibliothèque reste disponible."];
    if (!inference.online) return ["stopped", "Assistant arrêté. Vous pouvez lire et chercher dans la bibliothèque."];
    const models = Array.isArray(inference.models) ? inference.models : [];
    if (models.length) return ["ready", "Assistant prêt."];
    return ["ready", "Assistant prêt. La première réponse peut prendre un peu plus de temps, le temps de charger le modèle."];
  }

  function render() {
    const state = describe();
    if (!state) { status.hidden = true; return; }
    const [tone, message] = state;
    status.hidden = false;
    status.dataset.tone = tone;
    text.textContent = message;
    const canStart = admin() && inference && !inference.online && !inference.operation && inference.control_available !== false;
    action.hidden = !(canStart || tone === "stopped" || tone === "paused");
    action.textContent = canStart ? (inference.paused ? "Reprendre l’assistant" : "Démarrer l’assistant") : "Voir l’état de l’appareil";
    action.dataset.mode = canStart ? "start" : "monitor";
  }

  action.addEventListener("click", () => {
    if (action.dataset.mode === "start") {
      const start = document.getElementById("engine-start");
      if (start && !start.disabled) { start.click(); return; }
    }
    location.hash = "#/appareil/ensemble";
  });

  document.addEventListener("survie:inference", (event) => { inference = event.detail; render(); });
  document.addEventListener("survie:connection", (event) => { connected = event.detail.online; render(); });
  if (typeof S !== "undefined" && S.inference) inference = S.inference;
  render();

  /* ---------- Étapes d'une réponse ---------- */
  const STEPS = [
    ["prepare", "Préparer"],
    ["search", "Chercher"],
    ["read", "Lire"],
    ["write", "Rédiger"],
  ];
  const STAGE = {
    loading: "prepare", switching: "prepare", retrying: "prepare",
    searching: "search",
    reading: "read", illustrating: "read",
    preparing: "write", writing: "write", referencing: "write",
  };
  const FINISHED = new Set(["done", "failed", "cancelled", "interrupted", "incomplete"]);

  function current() {
    const messages = document.querySelectorAll("#chat-messages .message-assistant");
    return messages[messages.length - 1] || null;
  }

  function steps(node) {
    let list = node.querySelector(":scope > .answer-steps");
    if (list) return list;
    list = document.createElement("ol");
    list.className = "answer-steps";
    list.setAttribute("aria-label", "Étapes de la réponse");
    for (const [key, label] of STEPS) {
      const item = document.createElement("li");
      item.dataset.step = key;
      item.textContent = label;
      list.append(item);
    }
    node.querySelector(".message-label")?.after(list);
    return list;
  }

  document.addEventListener("survie:job", (event) => {
    const job = event.detail || {};
    const node = current();
    if (!node) return;
    const list = steps(node);
    if (job.status === "queued") { list.dataset.state = "queued"; return; }
    const finished = FINISHED.has(job.status);
    const stage = STAGE[job.progress?.stage] || (job.answer ? "write" : "prepare");
    const index = STEPS.findIndex(([key]) => key === stage);
    list.dataset.state = finished ? (job.status === "done" ? "done" : "stopped") : "running";
    list.querySelectorAll("li").forEach((item, position) => {
      item.dataset.status = finished && job.status === "done" ? "done"
        : position < index ? "done" : position === index ? (finished ? "stopped" : "active") : "todo";
      if (item.dataset.status === "active") item.setAttribute("aria-current", "step");
      else item.removeAttribute("aria-current");
    });
    if (finished && job.status === "done") {
      setTimeout(() => {
        list.classList.add("answer-steps-leaving");
        setTimeout(() => list.remove(), reduced.matches ? 0 : 320);
      }, reduced.matches ? 400 : 1400);
    }
  });
})();
