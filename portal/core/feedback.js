/* Retours visuels communs : connexion à l'appareil, boutons occupés.
 *
 * - Le bandeau `#connection-banner` (balisage dans `interface/modele.html`)
 *   suit `SurvieNet` : il annonce la perte de connexion, compte les secondes
 *   avant le prochain essai, propose « Réessayer maintenant » et confirme
 *   le retour.
 * - L'état du pied de page (`#service-status`) suit la même source.
 * - Un bouton désactivé juste après un clic montre qu'il travaille
 *   (`.is-busy`), sans que chaque module ait à le prévoir.
 * Aucune requête propre hormis le contrôle de santé de `SurvieNet`.
 */
(() => {
  const net = window.SurvieNet;
  if (!net) return;
  const reduced = matchMedia("(prefers-reduced-motion: reduce)");

  /* ---------- Connexion ---------- */
  let countdown = null;
  let restoredTimer = null;

  function banner() { return document.getElementById("connection-banner"); }

  function renderConnection(state) {
    const root = banner();
    const footer = document.getElementById("service-status");
    if (footer) {
      footer.dataset.state = state.online ? "online" : "offline";
      const label = footer.querySelector(".service-status-label") || footer;
      if (label === footer) {
        footer.replaceChildren(Object.assign(document.createElement("span"), { className: "status-dot" }),
          Object.assign(document.createElement("span"), { className: "service-status-label" }));
      }
      footer.querySelector(".service-status-label").textContent =
        state.online ? "Appareil connecté" : "Appareil injoignable";
    }
    if (!root) return;
    const title = root.querySelector("[data-connection-title]");
    const text = root.querySelector("[data-connection-text]");
    const retry = root.querySelector("[data-connection-retry]");
    const timerText = root.querySelector("[data-connection-timer]");
    clearInterval(countdown);
    if (!state.online) {
      clearTimeout(restoredTimer);
      root.hidden = false;
      root.dataset.state = "offline";
      document.documentElement.classList.add("survie-offline");
      title.textContent = "Connexion à l’appareil perdue";
      text.textContent = net.OFFLINE + " Ce qui est déjà affiché reste lisible.";
      retry.hidden = false;
      root.querySelector("[data-connection-help]")?.removeAttribute("hidden");
      retry.disabled = !!state.checking;
      const tick = () => {
        const current = net.state();
        if (current.checking) { timerText.textContent = "Vérification…"; return; }
        const seconds = Math.max(0, Math.ceil((current.retryAt - Date.now()) / 1000));
        timerText.textContent = seconds ? `Nouvel essai dans ${seconds} s` : "Vérification…";
      };
      tick();
      countdown = setInterval(tick, 500);
      return;
    }
    document.documentElement.classList.remove("survie-offline");
    if (root.hidden || root.dataset.state !== "offline") return;
    root.dataset.state = "restored";
    title.textContent = "Connexion rétablie";
    text.textContent = "L’appareil répond de nouveau. Vous pouvez reprendre où vous en étiez.";
    timerText.textContent = "";
    retry.hidden = true;
    root.querySelector("[data-connection-help]")?.setAttribute("hidden", "");
    restoredTimer = setTimeout(() => { root.hidden = true; delete root.dataset.state; }, 3500);
  }

  function bindConnection() {
    const root = banner();
    root?.querySelector("[data-connection-retry]")?.addEventListener("click", async (event) => {
      event.currentTarget.disabled = true;
      await net.retryNow();
    });
    net.onChange(renderConnection);
    renderConnection(net.state());
  }

  /* ---------- Boutons occupés ----------
   * Beaucoup de modules désactivent leur bouton pendant une opération.
   * Si cela arrive juste après un clic sur ce bouton, on affiche un
   * indicateur dans le bouton jusqu'à sa réactivation. */
  let pressed = null;
  let pressedAt = 0;
  function remember(event) {
    const target = event.target.closest?.("button, input[type=submit]");
    if (!target) return;
    pressed = target;
    pressedAt = performance.now();
  }
  addEventListener("click", remember, true);
  addEventListener("submit", (event) => {
    const submitter = event.submitter || event.target.querySelector("button[type=submit], button:not([type])");
    if (submitter) { pressed = submitter; pressedAt = performance.now(); }
  }, true);

  const busyObserver = new MutationObserver((records) => {
    for (const record of records) {
      const button = record.target;
      if (!(button instanceof HTMLElement)) continue;
      if (button.disabled) {
        if (button === pressed && performance.now() - pressedAt < 1500 && !button.classList.contains("no-busy")) {
          button.classList.add("is-busy");
          button.setAttribute("aria-busy", "true");
        }
      } else if (button.classList.contains("is-busy")) {
        button.classList.remove("is-busy");
        button.removeAttribute("aria-busy");
        if (!reduced.matches && button.isConnected) {
          button.classList.add("is-done");
          setTimeout(() => button.classList.remove("is-done"), 700);
        }
      }
    }
  });

  /* Utilitaire explicite pour les actions qui ne désactivent pas leur bouton. */
  async function busy(button, task) {
    if (!button) return task;
    button.classList.add("is-busy");
    button.setAttribute("aria-busy", "true");
    try { return await task; }
    finally {
      button.classList.remove("is-busy");
      button.removeAttribute("aria-busy");
    }
  }

  function start() {
    bindConnection();
    busyObserver.observe(document.body, { subtree: true, attributes: true, attributeFilter: ["disabled"] });
  }

  window.SurvieFeedback = Object.freeze({ busy });
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", start, { once: true });
  else start();
})();
