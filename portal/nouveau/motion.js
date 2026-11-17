/* Presentation only: no delayed action, DOM snapshot, request or saved state. */
(() => {
  const reduced = matchMedia("(prefers-reduced-motion: reduce)");
  const active = new Map();
  function cancelAll() {
    for (const animation of active.values()) animation.cancel();
    active.clear();
  }
  function reveal(node, distance = 6) {
    if (!node) return;
    active.get(node)?.cancel();
    if (reduced.matches || !node.animate || !node.getClientRects().length) return;
    const animation = node.animate(
      [{ opacity: 0.55, transform: `translateY(${distance}px)` },
       { opacity: 1, transform: "translateY(0)" }],
      { duration: 180, easing: "cubic-bezier(.2,.7,.2,1)", id: "survie-reveal" },
    );
    active.set(node, animation);
    animation.finished.catch(() => {}).finally(() => {
      if (active.get(node) === animation) active.delete(node);
    });
  }
  reduced.addEventListener("change", () => { if (reduced.matches) cancelAll(); });
  document.addEventListener("survie:auth", cancelAll);
  window.addEventListener("pagehide", cancelAll);
  let routeKey;
  document.addEventListener("survie:route", ({ detail }) => {
    const next = detail.section + "/" + detail.tab;
    if (routeKey !== undefined && routeKey !== next) {
      cancelAll();
      reveal(document.querySelector(".view:not([hidden])"));
    }
    routeKey = next;
  });
  document.addEventListener("survie:source", () => reveal(document.getElementById("reader")));
  document.addEventListener("survie:results", () => reveal(document.getElementById("search-results")));
  document.addEventListener("toggle", ({ target }) => {
    if (target.tagName !== "DETAILS" || !target.open) return;
    for (const child of target.children) if (child.tagName !== "SUMMARY") reveal(child, 0);
  }, true);
  window.SurvieMotion = Object.freeze({ reveal });
})();
