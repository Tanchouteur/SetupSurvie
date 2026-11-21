/* Accueil : ligne « Sur cet appareil » (contenus disponibles et état de l’assistant).
 * Lit l’inventaire et l’état du moteur déjà publiés par le portail ; demande
 * l’inventaire une seule fois si l’accueil est ouvert avant la bibliothèque. */
(() => {
  const link = document.querySelector("#view-home .home-device");
  const text = link?.querySelector("[data-home-device]");
  if (!link || !text) return;
  const facts = { inventory: null, inference: null, online: true };
  const plural = (n, one, many) => `${n} ${n > 1 ? many : one}`;

  function render() {
    const parts = [];
    const inv = facts.inventory;
    if (inv) {
      const books = (inv.books || []).filter((item) => item.ready).length;
      const guides = (inv.guides || []).filter((item) => item.ready).length;
      if (books) parts.push(plural(books, "collection", "collections"));
      if (guides) parts.push(plural(guides, "guide", "guides"));
      if (!books && !guides) parts.push("aucun contenu prêt pour l’instant");
    }
    const inf = facts.inference;
    let state = "ok";
    if (!facts.online) { parts.length = 0; parts.push("appareil injoignable"); state = "danger"; }
    else if (inf && !inf.observation_error) {
      if (inf.operation === "start") { parts.push("assistant en démarrage"); state = "busy"; }
      else if (inf.paused) { parts.push("assistant en pause"); state = "warn"; }
      else if (!inf.online) { parts.push("assistant arrêté"); state = "warn"; }
      else parts.push("assistant prêt");
    }
    link.hidden = !parts.length;
    link.dataset.state = state;
    text.textContent = parts.join(" · ");
  }

  async function loadInventory() {
    if (facts.inventory || typeof api !== "function") return;
    try { facts.inventory = await api("/inventory"); render(); } catch (_) { /* le bandeau de connexion informe déjà */ }
  }

  document.addEventListener("survie:inventory", (event) => { facts.inventory = event.detail; render(); });
  document.addEventListener("survie:inference", (event) => { facts.inference = event.detail; render(); });
  document.addEventListener("survie:connection", (event) => { facts.online = event.detail.online; render(); });
  document.addEventListener("survie:auth", () => setTimeout(loadInventory, 400));
  if (typeof S !== "undefined" && S.inference) facts.inference = S.inference;
  render();
})();
