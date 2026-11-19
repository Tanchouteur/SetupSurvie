/* Local UI primitives. No API calls, profile data or feature state. */
(() => {
  function icon(path) {
    const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    svg.setAttribute("viewBox", "0 0 24 24");
    svg.setAttribute("aria-hidden", "true");
    svg.setAttribute("fill", "none");
    svg.setAttribute("stroke", "currentColor");
    svg.setAttribute("stroke-width", "1.6");
    svg.setAttribute("stroke-linecap", "round");
    svg.setAttribute("stroke-linejoin", "round");
    const p = document.createElementNS(svg.namespaceURI, "path");
    p.setAttribute("d", path);
    svg.append(p);
    return svg;
  }
  function help(label, text) {
    const root = document.createElement("span");
    root.className = "ux-help";
    const trigger = document.createElement("button");
    trigger.type = "button";
    trigger.className = "ux-help-trigger";
    trigger.append(
      icon(
        "M9.5 9a2.5 2.5 0 115 0c0 2-2.5 2-2.5 4 M12 17h.01 M12 2a10 10 0 100 20 10 10 0 000-20",
      ),
    );
    trigger.setAttribute("aria-label", label);
    trigger.setAttribute("aria-expanded", "false");
    const content = document.createElement("span");
    content.className = "ux-help-content";
    content.hidden = true;
    content.id = "ux-help-" + ++help.count;
    content.textContent = text;
    trigger.setAttribute("aria-controls", content.id);
    trigger.setAttribute("aria-describedby", content.id);
    let dismissed = false,
      pinned = false;
    const show = () => {
      if (dismissed) return;
      content.hidden = false;
      trigger.setAttribute("aria-expanded", "true");
    };
    const hide = () => {
      content.hidden = true;
      trigger.setAttribute("aria-expanded", "false");
    };
    trigger.addEventListener("click", () => {
      dismissed = false;
      pinned = !pinned;
      if (pinned) show();
      else hide();
    });
    root.addEventListener("pointerenter", (event) => {
      if (event.pointerType === "mouse") {
        dismissed = false;
        show();
      }
    });
    root.addEventListener("pointerleave", () => {
      if (!pinned && !root.contains(document.activeElement)) hide();
      dismissed = false;
    });
    trigger.addEventListener("focus", show);
    root.addEventListener("focusout", (event) => {
      if (!root.contains(event.relatedTarget)) {
        pinned = false;
        hide();
      }
    });
    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape" && !content.hidden) {
        pinned = false;
        hide();
        dismissed = true;
      }
    });
    document.addEventListener("pointerdown", (event) => {
      if (!root.contains(event.target)) {
        pinned = false;
        hide();
      }
    });
    root.append(trigger, content);
    return root;
  }
  help.count = 0;
  function cardLink(route, title, description) {
    const card = document.createElement("a");
    card.className = "settings-destination";
    card.href = "#/" + route;
    card.dataset.route = route;
    const heading = document.createElement("strong");
    heading.textContent = title;
    const copy = document.createElement("span");
    copy.className = "muted";
    copy.textContent = description;
    const action = document.createElement("span");
    action.className = "settings-arrow";
    action.textContent = "Ouvrir →";
    card.append(heading, copy, action);
    return card;
  }
  function describeDisclosure(details, description) {
    const summary = details.querySelector(":scope > summary");
    if (!summary) return;
    const heading = document.createElement("span");
    heading.className = "settings-card-title";
    heading.textContent = summary.textContent;
    const copy = document.createElement("span");
    copy.className = "settings-card-description";
    copy.textContent = description;
    summary.classList.add("settings-card-summary");
    summary.replaceChildren(heading, copy);
  }
  window.SurvieUI = Object.freeze({ help, icon, cardLink, describeDisclosure });
})();
