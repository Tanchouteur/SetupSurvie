/* Presentation only: no delayed action, DOM snapshot, request or saved state. */
(() => {
  const reducedMotion = "(prefers-reduced-motion: reduce)";
  const preference = matchMedia(reducedMotion);
  const active = new Map();
  function cancelAll() {
    for (const animation of active.values()) animation.cancel();
    active.clear();
  }
  function reveal(node) {
    if (!node) return;
    active.get(node)?.cancel();
    // WebKit can deliver a retained MediaQueryList change after a navigation.
    if (matchMedia(reducedMotion).matches || !node.animate || !node.getClientRects().length) return;
    const animation = node.animate(
      // A transformed container changes the containing block of fixed children.
      // Fade only: help, navigation and reader controls keep viewport coordinates.
      [{ opacity: 0.55 }, { opacity: 1 }],
      { duration: 180, easing: "cubic-bezier(.2,.7,.2,1)", id: "survie-reveal" },
    );
    active.set(node, animation);
    animation.finished.catch(() => {}).finally(() => {
      if (active.get(node) === animation) active.delete(node);
    });
  }
  preference.addEventListener("change", ({ matches }) => { if (matches) cancelAll(); });
  document.addEventListener("survie:auth", cancelAll);
  window.addEventListener("pagehide", cancelAll);
  /* Changement d’écran (0.76.0) : la vue apparaît en fondu, et ses blocs glissent
   * de 24 px dans le sens de la navigation (vers la droite dans l’ordre du menu ou
   * des onglets, vers la gauche au retour), en cascade. Les blocs qui contiennent
   * un élément en position fixe (aide, lecteur, message, dialogue) gardent un
   * simple fondu : une translation déplacerait ces éléments pendant l’animation. */
  const SECTIONS = ["accueil", "bibliotheque", "assistant", "cartes", "appareil", "file"];
  const FIXED = ".ux-help, .reader-work, .toast, dialog, [popover], .connection-banner";
  function tabIndex(view, tab) {
    const links = [...(view?.querySelectorAll(".next-tabs a") || [])];
    return links.findIndex((link) => (link.getAttribute("href") || "").split("?")[0].endsWith("/" + tab));
  }
  function slide(view, direction) {
    if (!view || !direction) return;
    const blocks = [...view.children].filter((child) => child.getClientRects().length).slice(0, 6);
    blocks.forEach((block, index) => {
      if (!block.animate) return;
      active.get(block)?.cancel();
      const keyframes = block.querySelector(FIXED) || block.matches(FIXED)
        ? [{ opacity: 0 }, { opacity: 1 }]
        : [{ opacity: 0, transform: `translateX(${direction * 24}px)` }, { opacity: 1, transform: "none" }];
      const animation = block.animate(keyframes, {
        duration: 240, delay: Math.min(index, 4) * 35, easing: "cubic-bezier(.2,.8,.2,1)", fill: "backwards", id: "survie-slide",
      });
      active.set(block, animation);
      animation.finished.catch(() => {}).finally(() => { if (active.get(block) === animation) active.delete(block); });
    });
  }
  let routeKey, routeSection, routeTab;
  document.addEventListener("survie:route", ({ detail }) => {
    const next = detail.section + "/" + detail.tab;
    if (routeKey !== undefined && routeKey !== next) {
      cancelAll();
      const view = document.querySelector(".view:not([hidden])");
      reveal(view);
      if (!matchMedia(reducedMotion).matches) {
        let direction = Math.sign(SECTIONS.indexOf(detail.section) - SECTIONS.indexOf(routeSection));
        if (detail.section === routeSection) direction = Math.sign(tabIndex(view, detail.tab) - tabIndex(view, routeTab)) || 1;
        slide(view, direction || 1);
      }
    }
    routeKey = next;
    routeSection = detail.section;
    routeTab = detail.tab;
  });
  /* Les cartes de collections arrivent en cascade quand l’inventaire s’affiche. */
  document.addEventListener("survie:inventory", () => {
    if (matchMedia(reducedMotion).matches) return;
    requestAnimationFrame(() => {
      const cards = [...document.querySelectorAll("#next-collections .data-card")].filter((card) => card.getClientRects().length).slice(0, 16);
      cards.forEach((card, index) => card.animate?.(
        [{ opacity: 0, transform: "translateY(12px) scale(.98)" }, { opacity: 1, transform: "none" }],
        { duration: 260, delay: index * 30, easing: "cubic-bezier(.2,.8,.2,1)", fill: "backwards", id: "survie-cards" },
      ));
    });
  });
  document.addEventListener("survie:source", () => reveal(document.getElementById("reader")));
  document.addEventListener("survie:results", () => reveal(document.getElementById("search-results")));
  document.addEventListener("toggle", ({ target }) => {
    if (target.tagName !== "DETAILS" || !target.open) return;
    for (const child of target.children) if (child.tagName !== "SUMMARY") reveal(child);
  }, true);
  window.SurvieMotion = Object.freeze({ reveal });
})();
