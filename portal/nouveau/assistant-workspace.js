/* One set of controls, profile-owned organization and independent evidence. */
(() => {
  const chat = $("view-chat"),
    context = chat.querySelector(".next-chat-context");
  const tools = element("details", undefined, "assistant-tools");
  tools.append(element("summary", "Outils"));
  const bottom = document.querySelector(".sidebar-bottom");
  tools.append($("admin-nav"), bottom.querySelector(".sidebar-tools"));
  bottom.prepend(tools);

  const body = element("div", undefined, "assistant-workspace");
  body.id = "assistant-workspace";
  const left = element("aside", undefined, "assistant-history");
  left.id = "assistant-history";
  left.setAttribute("aria-label", "Conversations et dossiers");
  const center = element("div", undefined, "assistant-discussion");
  center.id = "assistant-discussion";
  const right = element("aside", undefined, "assistant-documents");
  right.id = "assistant-documents";
  right.setAttribute("aria-label", "Documents de la discussion");
  const title = element("h2", "Conversations");
  const create = $("chat-reset");
  create.textContent = "Nouvelle discussion";
  const resetHome = chat.querySelector(".next-chat-actions");
  left.append(title, create);
  const search = element("input");
  search.type = "search";
  search.maxLength = 160;
  search.placeholder = "Rechercher…";
  search.setAttribute("aria-label", "Rechercher une conversation");
  const folders = element("div", undefined, "assistant-folders");
  folders.setAttribute("aria-label", "Dossiers personnels");
  const add = button("Créer un projet", () =>
    edit("Créer un projet", "Nom du dossier", "", (value) =>
      api("/conversation-folders", { name: value }),
    ),
  );
  add.id = "assistant-folder-create";
  const folderState = element("p", "", "small muted");
  folderState.setAttribute("role", "status");
  const dragStatus = element("p", "", "sr-only");
  dragStatus.setAttribute("role", "status");
  const list = $("conversation-list");
  left.append(search, folders, add, folderState, dragStatus, list);
  const previous = button(
    "Conversations précédentes",
    () => {
      offset = Math.max(0, offset - 100);
      void histories();
    },
    "secondary",
  );
  previous.hidden = true;
  left.append(previous);
  const more = button(
    "Voir la suite",
    () => {
      offset += 100;
      void histories();
    },
    "secondary",
  );
  more.hidden = true;
  left.append(more);
  const banner = $("inference-banner");
  center.append(banner, $("translation-panel"), $("chat-messages"), $("chat-form"));
  body.append(left, center, right);
  chat.append(body);
  const selectedTitle = element("h2", "Documents choisis"),
    usedTitle = element("h2", "Sources consultées");
  const used = element("div");
  used.id = "assistant-consulted-sources";
  context.append($("summary-panel"));
  right.append(selectedTitle, context, usedTitle, used);
  const responseOptions = element("details");
  responseOptions.append(element("summary", "Options de réponse"));
  const modelTrials = element("input");
  modelTrials.type = "checkbox";
  modelTrials.id = "assistant-model-trials";
  const trialsLabel = element("label", undefined, "assistant-check");
  trialsLabel.htmlFor = modelTrials.id;
  trialsLabel.append(
    modelTrials,
    element("span", "Afficher les modèles d’essai"),
  );
  responseOptions.append(trialsLabel);
  const modelSelect = $("chat-mode");
  function trialVisibility() {
    for (const group of modelSelect.querySelectorAll("optgroup"))
      if (group.label === "Autres modèles à comparer")
        group.hidden = !modelTrials.checked;
  }
  modelTrials.onchange = trialVisibility;
  new MutationObserver(trialVisibility).observe(modelSelect, {
    childList: true,
  });
  responseOptions.append(
    element(
      "p",
      "Les modes rapide, moyen et approfondi règlent le travail demandé. Le délai dépend du PC et des documents.",
      "small muted",
    ),
  );
  const scope = $("chat-domain").closest("label");
  scope.querySelector("span").classList.remove("sr-only");
  scope.querySelector("span").textContent = "Rechercher des sources dans";
  responseOptions.append(scope);
  right.append(responseOptions);

  const empty = element(
    "p",
    "Aucun document choisi. Vous pouvez en sélectionner dans la bibliothèque.",
    "small muted",
  );
  context.prepend(empty);
  const library = element("a", "Choisir dans la bibliothèque");
  library.href = "#/bibliotheque";
  library.dataset.route = "bibliotheque";
  context.prepend(library);
  const reopen = element("div", undefined, "assistant-panel-openers");
  const reopenDocuments = element("div", undefined, "assistant-document-opener");
  const toggleButtons = new Map();
  for (const [zone, label, path] of [
    ["history", "Conversations", "M3 4h18v16H3z M9 4v16 M13 8h4 M13 12h4"],
    ["documents", "Documents", "M3 4h18v16H3z M15 4v16 M6 8h5 M6 12h5"],
  ]) {
    const open = button("", () => select(zone), "assistant-panel-button");
    open.append(SurvieUI.icon(path), element("span", label));
    open.dataset.assistantZone = zone;
    open.setAttribute(
      "aria-controls",
      zone === "history" ? "assistant-history" : "assistant-documents",
    );
    (zone === "documents" ? reopenDocuments : reopen).append(open);
    toggleButtons.set(zone, open);
    const panel = zone === "history" ? left : right,
      panelTitle = zone === "history" ? title : selectedTitle;
    const head = element("div", undefined, "assistant-panel-heading");
    const close = button("", () => closePanel(zone), "assistant-panel-close");
    close.dataset.closePanel = zone;
    close.setAttribute(
      "aria-label",
      "Fermer le volet " + label.toLocaleLowerCase("fr"),
    );
    close.title = close.getAttribute("aria-label");
    close.append(
      SurvieUI.icon(zone === "history" ? "M14 6l-6 6 6 6" : "M10 6l6 6-6 6"),
    );
    panelTitle.before(head);
    head.append(panelTitle, close);
  }
  chat.querySelector(".chat-top").prepend(reopen);
  chat.querySelector(".chat-top").append(reopenDocuments);
  $("next-history-open").hidden = true;
  let folder = "all",
    offset = 0,
    generation = 0,
    folderItems = [],
    evidence = new Map(),
    timer = 0;
  body.dataset.zone = "discussion";
  body.dataset.left = "open";
  body.dataset.right = "open";
  function select(zone) {
    if (innerWidth <= 1000) body.dataset.zone = zone;
    else body.dataset[zone === "history" ? "left" : "right"] = "open";
    refreshZones();
    if (innerWidth <= 1000) window.SurvieMotion?.reveal(zone === "history" ? left : right);
    requestAnimationFrame(() => {
      if (zone === "history") search.focus();
      else right.querySelector("button,a,summary")?.focus();
    });
  }
  function closePanel(zone) {
    if (innerWidth <= 1000) body.dataset.zone = "discussion";
    else body.dataset[zone === "history" ? "left" : "right"] = "closed";
    refreshZones();
    if (innerWidth <= 1000) window.SurvieMotion?.reveal(center);
    toggleButtons.get(zone).focus();
  }
  function refreshZones() {
    for (const [zone, open] of toggleButtons) {
      const expanded =
        innerWidth <= 1000
          ? body.dataset.zone === zone
          : body.dataset[zone === "history" ? "left" : "right"] === "open";
      open.setAttribute("aria-expanded", String(expanded));
      open.hidden = innerWidth > 1000 && expanded;
      const panel = zone === "history" ? left : right;
      panel.inert = !expanded;
      panel.setAttribute("aria-hidden", String(!expanded));
    }
    chat.dataset.history = body.dataset.left;
    if (innerWidth > 1000 && body.dataset.left === "open") {
      if (create.parentElement !== left) left.insertBefore(create, search);
    } else if (create.parentElement !== resetHome) {
      resetHome.append(create);
    }
  }
  window.addEventListener("resize", refreshZones);
  refreshZones();
  const resize = element('div',undefined,'assistant-resize');
  resize.tabIndex=0;resize.setAttribute('role','separator');
  resize.setAttribute('aria-label','Largeur du volet Conversations');
  resize.setAttribute('aria-orientation','vertical');body.append(resize);
  const limits=()=>({min:220,max:Math.max(220,Math.min(480,innerWidth-680))});
  function setWidth(value) {
    const {min,max}=limits();const width=Math.max(min,Math.min(max,value));
    body.style.setProperty('--assistant-left-width',width+'px');
    resize.setAttribute('aria-valuemin',min);resize.setAttribute('aria-valuemax',max);resize.setAttribute('aria-valuenow',width);
  }
  setWidth(252);
  resize.addEventListener('pointerdown',event=>{
    if(event.button!==0)return;event.preventDefault();resize.setPointerCapture(event.pointerId);
    body.classList.add('assistant-resizing');
  });
  resize.addEventListener('pointermove',event=>{
    if(resize.hasPointerCapture(event.pointerId))setWidth(event.clientX-left.getBoundingClientRect().left);
  });
  const stopResize=()=>body.classList.remove('assistant-resizing');
  resize.addEventListener('lostpointercapture',stopResize);
  resize.addEventListener('pointerup',event=>{if(resize.hasPointerCapture(event.pointerId))resize.releasePointerCapture(event.pointerId);});
  resize.addEventListener('keydown',event=>{
    const current=Number(resize.getAttribute('aria-valuenow'));
    if(!['ArrowLeft','ArrowRight','Home','End'].includes(event.key))return;
    event.preventDefault();setWidth(event.key==='Home'?limits().min:event.key==='End'?limits().max:current+(event.key==='ArrowRight'?20:-20));
  });
  window.addEventListener('resize',()=>setWidth(Number(resize.getAttribute('aria-valuenow'))));
  const editor = element("dialog");
  editor.id = "assistant-editor";
  editor.setAttribute("aria-labelledby", "assistant-editor-title");
  const form = element("form"),
    heading = element("h2");
  heading.id = "assistant-editor-title";
  const input = element("input");
  input.maxLength = 80;
  input.required = true;
  const label = element("label");
  label.append(element("span"), input);
  const error = element("p");
  error.setAttribute("role", "alert");
  const save = element("button", "Enregistrer");
  save.type = "submit";
  const cancel = button("Annuler", () => editor.close(), "secondary");
  form.append(heading, label, error, save, cancel);
  editor.append(form);
  document.body.append(editor);
  document.dispatchEvent(new CustomEvent("survie:dialog", { detail: editor }));
  let commit = null,
    editOwner = null;
  function edit(title, caption, value, action) {
    heading.textContent = title;
    label.firstChild.textContent = caption;
    input.value = value;
    error.textContent = "";
    commit = action;
    editOwner = S.user?.id;
    editor.showModal();
    input.focus();
  }
  form.onsubmit = async (event) => {
    event.preventDefault();
    if (!commit || editOwner !== S.user?.id) return;
    save.disabled = true;
    try {
      await commit(input.value.trim());
      editor.close();
      await histories();
    } catch (e) {
      error.textContent = e.message;
    } finally {
      save.disabled = false;
    }
  };
  function menu(label) {
    const d = element("details", undefined, "assistant-row-menu");
    const summary = element("summary", "⋯");
    summary.setAttribute("aria-label", label);
    d.append(summary);
    return d;
  }
  const dragType = "application/x-setupsurvie-conversation";
  let dragging = null;
  const moving = new Set();
  function clearDrag() {
    dragging = null;
    left.classList.remove("assistant-dragging");
    left.querySelectorAll(".is-dragging,.is-drop-target").forEach((node) =>
      node.classList.remove("is-dragging", "is-drop-target"),
    );
    dragStatus.textContent = "";
  }
  async function moveConversation(conversation, target) {
    const owner = S.user?.id;
    if (!owner || moving.has(conversation.id)) return;
    if ((conversation.folder_id || "") === target) {
      toast("Cette conversation est déjà dans ce dossier.");
      return;
    }
    moving.add(conversation.id);
    try {
      await api("/conversations/" + encodeURIComponent(conversation.id) + "/folder",
        { folder_id: target || null }, { method: "PUT" });
      if (S.user?.id !== owner) return;
      if(target) { expandedProjects.add(target);saveProjects(); }
      await histories();
      const destination = folderItems.find((item) => item.id === target)?.name || "Sans dossier";
      toast("Conversation déplacée dans « " + destination + " ».");
    } finally {
      moving.delete(conversation.id);
    }
  }
  function makeDraggable(row, conversation) {
    row.draggable = true;
    let canDrag = true;
    row.addEventListener("pointerdown", (event) => {
      canDrag = !event.target.closest("details");
    });
    const grip = element("span", undefined, "assistant-drag-handle");
    grip.setAttribute("aria-hidden", "true");
    grip.title = "Glisser vers un dossier";
    grip.append(SurvieUI.icon("M8 6h.01 M16 6h.01 M8 12h.01 M16 12h.01 M8 18h.01 M16 18h.01"));
    row.prepend(grip);
    row.addEventListener("dragstart", (event) => {
      if (!S.user || !canDrag || !event.dataTransfer || moving.has(conversation.id)) {
        event.preventDefault();
        return;
      }
      clearDrag();
      dragging = { conversation, owner: S.user?.id };
      event.dataTransfer.setData(dragType, conversation.id);
      event.dataTransfer.effectAllowed = "move";
      row.classList.add("is-dragging");
      left.classList.add("assistant-dragging");
      dragStatus.textContent = "Déposez la conversation sur un dossier pour l’y déplacer.";
    });
    row.addEventListener("dragend", clearDrag);
  }
  document.addEventListener("survie:auth", clearDrag);
  document.addEventListener("survie:route", ({ detail }) => {
    if (detail.section !== "assistant") clearDrag();
  });
  function folderButton(value, label, action) {
    const b = button(
      label,
      action || (() => {
        folder = value;
        offset = 0;
        histories();
      }),
      "secondary",
    );
    b.setAttribute("aria-pressed", String(folder === value));
    if (value !== "all") {
      const target = value === "unfiled" ? "" : value;
      b.dataset.folderId = target;
      const validDrag = () => dragging && dragging.owner === S.user?.id;
      b.addEventListener("dragover", (event) => {
        if (!validDrag()) return;
        event.preventDefault();
        event.dataTransfer.dropEffect = "move";
        left.querySelectorAll(".is-drop-target").forEach((node) => node.classList.remove("is-drop-target"));
        b.classList.add("is-drop-target");
      });
      b.addEventListener("dragleave", (event) => {
        if (!b.contains(event.relatedTarget)) b.classList.remove("is-drop-target");
      });
      b.addEventListener("drop", async (event) => {
        if (!validDrag() || event.dataTransfer?.getData(dragType) !== dragging.conversation.id) return;
        event.preventDefault();
        const conversation = dragging.conversation;
        clearDrag();
        try { await moveConversation(conversation, target); }
        catch (error) { toast(error.message); }
      });
    }
    return b;
  }
  const expandedProjects = new Set();
  const projectKey=()=> 'survie-expanded-projects:'+S.user?.id;
  function saveProjects(){try{sessionStorage.setItem(projectKey(),JSON.stringify([...expandedProjects]));}catch(_){}}

  function conversationRow(c) {
        const row = element("div", undefined, "conversation-row"),
          open = button(
            c.title,
            async () => {
              await openConversation(c.id);
              body.dataset.zone = "discussion";
              refreshZones();
            },
            "conversation-link",
          ),
          m = menu("Actions de " + c.title);
        open.setAttribute("aria-current", String(c.id === S.conversation));
        open.title = c.title;
        open.dataset.conversationId = c.id;
        const move = element("select");
        move.setAttribute("aria-label", "Dossier de " + c.title);
        move.append(new Option("Sans dossier", ""));
        for (const f of folderItems) move.append(new Option(f.name, f.id));
        move.value = c.folder_id || "";
        move.onchange = async () => {
          move.disabled = true;
          try {
            await moveConversation(c, move.value);
          } catch (e) {
            toast(e.message);
            move.value = c.folder_id || "";
          } finally {
            move.disabled = false;
          }
        };
        m.append(
          button(
            "Renommer",
            () =>
              edit(
                "Renommer la conversation",
                "Titre",
                c.title,
                async (value) => {
                  await api(
                    "/conversations/" + encodeURIComponent(c.id) + "/title",
                    { title: value },
                    { method: "PATCH" },
                  );
                  if (S.conversation === c.id) {
                    $("chat-title").textContent = value;
                    $("chat-title").title = value;
                  }
                },
              ),
            "text-button",
          ),
          move,
          button("Supprimer", () => deleteConversation(c), "text-button"),
        );
        row.append(open, m);
        makeDraggable(row, c);
    return row;
  }
  async function loadProject(f, host, own, owner, offset = 0) {
    try {
      const data = await api('/conversations?' + new URLSearchParams({folder:f.id,q:search.value,offset:String(offset)}));
      if (own !== generation || owner !== S.user?.id || !host.isConnected) return;
      host.querySelector('.project-more')?.remove();
      if (!offset) host.replaceChildren();
      for (const c of data.conversations) host.append(conversationRow(c));
      if (!data.conversations.length && !offset) host.append(element('p','Aucune conversation dans ce projet.','small muted'));
      if (data.has_more) {
        const more = button('Voir la suite', () => { more.disabled=true;void loadProject(f,host,own,owner,offset+100); }, 'project-more');
        host.append(more);
      }
    } catch (error) {
      if (own !== generation || owner !== S.user?.id) return;
      const retry = button('Réessayer', () => { retry.remove();void loadProject(f,host,own,owner,offset); });
      host.append(element('p',error.message,'small muted'),retry);
    }
  }
  histories = async () => {
    if (!S.user) return;
    const own = ++generation,
      owner = S.user.id;
    try {
      let data,
        organization,
        degraded = false;
      try {
        [data, organization] = await Promise.all([
          api(
            "/conversations?" +
              new URLSearchParams({
                folder: folder === 'all' && !search.value ? 'unfiled' : folder,
                q: search.value,
                offset: String(offset),
              }),
          ),
          api("/conversation-folders"),
        ]);
      } catch (e) {
        if (
          e.name === "AbortError" ||
          own !== generation ||
          S.user?.id !== owner
        )
          return;
        data = await api("/conversations");
        organization = { folders: [] };
        degraded = true;
        folder = "all";
        offset = 0;
      }
      if (own !== generation || S.user?.id !== owner) return;
      folderItems = organization.folders;
      if (
        folder !== "all" &&
        folder !== "unfiled" &&
        !folderItems.some((f) => f.id === folder)
      ) {
        folder = "all";
        offset = 0;
        return histories();
      }
      folders.replaceChildren(
        folderButton("all", "Toutes les conversations"),
        folderButton("unfiled", "Sans dossier"),
      );
      for (const f of folderItems) {
        const row = element("div", undefined, "assistant-folder-row"),
          m = menu("Actions du dossier " + f.name);
        m.append(
          button(
            "Renommer",
            () =>
              edit("Renommer le projet", "Nom du dossier", f.name, (value) =>
                api(
                  "/conversation-folders/" + encodeURIComponent(f.id),
                  { name: value },
                  { method: "PATCH" },
                ),
              ),
            "text-button",
          ),
          button(
            "Supprimer le dossier",
            async () => {
              if (
                !confirm(
                  "Supprimer le dossier « " +
                    f.name +
                    " » ? Ses conversations seront conservées dans Sans dossier.",
                )
              )
                return;
              try {
                await api(
                  "/conversation-folders/" + encodeURIComponent(f.id),
                  undefined,
                  { method: "DELETE" },
                );
                await histories();
              } catch (e) {
                toast(e.message);
              }
            },
            "text-button",
          ),
        );
        const project = element('section',undefined,'assistant-project');
        const contents = element('div',undefined,'assistant-project-conversations');
        contents.id='project-'+f.id;
        const toggle=folderButton(f.id,f.name+' ('+f.count+')',()=>{
          const open=!expandedProjects.has(f.id);
          if(open) expandedProjects.add(f.id);else expandedProjects.delete(f.id);
          saveProjects();
          contents.hidden=!open;toggle.setAttribute('aria-expanded',String(open));
          if(open) void loadProject(f,contents,own,owner);
        });
        toggle.setAttribute('aria-controls',contents.id);
        toggle.setAttribute('aria-expanded',String(expandedProjects.has(f.id)));
        contents.hidden=!expandedProjects.has(f.id);
        row.append(toggle,m);project.append(row,contents);folders.append(project);
        if(!contents.hidden) void loadProject(f,contents,own,owner);
      }
      list.replaceChildren();
      for (const c of data.conversations) list.append(conversationRow(c));
      if (!data.conversations.length)
        list.append(
          element(
            "p",
            search.value
              ? "Aucune conversation ne correspond à ces mots."
              : "Aucune conversation ici.",
            "small muted",
          ),
        );
      previous.hidden = !offset;
      more.hidden = !data.has_more;
      folderState.textContent = degraded
        ? "Classement indisponible. Vos conversations restent accessibles."
        : offset
          ? "Conversations " +
            (offset + 1) +
            " à " +
            (offset + data.conversations.length)
          : "";
    } catch (e) {
      if (own === generation)
        folderState.textContent =
          e.message +
          " Les conversations restent accessibles depuis leur adresse.";
    }
  };
  search.oninput = () => {
    clearTimeout(timer);
    timer = setTimeout(() => {
      offset = 0;
      histories();
    }, 250);
  };
  const leave = () => {
    generation++;
    clearTimeout(timer);
  };
  window.addEventListener("beforeunload", leave);
  window.addEventListener("pagehide", leave);
  window.addEventListener("pageshow", (event) => {
    if (event.persisted) histories();
  });
  function drawEvidence() {
    used.replaceChildren();
    for (const source of evidence.values())
      used.append(
        button(source.title, () => readSource(source.id), "text-button"),
      );
    if (!evidence.size)
      used.append(
        element(
          "p",
          "Les sources réellement consultées apparaîtront ici après une réponse.",
          "small muted",
        ),
      );
  }
  function record(data) {
    for (const s of data?.consulted_sources || [])
      if (typeof s.id === "string" && typeof s.title === "string")
        evidence.set(s.id, s);
    drawEvidence();
  }
  document.addEventListener("survie:conversation", (event) => {
    $("chat-title").title = event.detail.title || "";
    for (const node of left.querySelectorAll(".conversation-link"))
      node.setAttribute(
        "aria-current",
        String(node.dataset.conversationId === event.detail.id),
      );
    evidence.clear();
    for (const m of event.detail.messages || []) record(m.documentary);
    drawEvidence();
    body.dataset.zone = "discussion";
    refreshZones();
  });
  document.addEventListener("survie:message", (event) =>
    record(event.detail.observed),
  );
  document.addEventListener("survie:summary-command", () => {
    if (S.view !== "chat") return;
    body.dataset.right = "open";
    body.dataset.zone = "documents";
    refreshZones();
  });
  document.addEventListener("survie:job", () => {
    for (const node of $("chat-messages").querySelectorAll(
      ".documentary-sources button[data-source]",
    ))
      evidence.set(node.dataset.source, {
        id: node.dataset.source,
        title: node.textContent,
      });
    drawEvidence();
  });
  document.addEventListener("survie:source-choices", () => {
    empty.hidden = !!selectedSourceChoices().length;
  });
  document.addEventListener("survie:new-conversation", () => {
    evidence.clear();
    drawEvidence();
    $("chat-title").textContent = "Nouvelle discussion";
    $("chat-title").removeAttribute("title");
    for (const node of left.querySelectorAll(".conversation-link")) {
      node.setAttribute("aria-current", "false");
    }
    body.dataset.zone = "discussion";
    refreshZones();
  });
  document.addEventListener("survie:auth", () => {
    generation++;
    expandedProjects.clear();
    try { const saved=JSON.parse(sessionStorage.getItem(projectKey())||'[]');if(Array.isArray(saved))for(const id of saved)if(typeof id==='string')expandedProjects.add(id); } catch(_) {}
    folder = "all";
    offset = 0;
    search.value = "";
    if (editor.open) editor.close();
    evidence.clear();
    drawEvidence();
    histories();
  });
  drawEvidence();
  document.addEventListener("DOMContentLoaded", () => {
    if (!S.conversation) $("chat-title").textContent = "Nouvelle discussion";
  });
  const tasks = element("div", undefined, "assistant-tasks");
  for (const [label, action] of [
    ["Poser une question", () => $("chat-input").focus()],
    [
      "Traduire un document",
      () => {
        view("library");
        toast("Ouvrez le document à traduire dans la bibliothèque.");
      },
    ],
    [
      "Faire une synthèse",
      () => {
        if (!selectedSourceChoices().length) {
          view("library");
          toast(
            "Choisissez les documents à comparer, puis revenez à la discussion.",
          );
        } else {
          body.dataset.right = "open";
          body.dataset.zone = "documents";
          refreshZones();
          $("summary-panel").open = true;
        }
      },
    ],
    [
      "Comprendre ou apprendre",
      () => {
        $("chat-input").value =
          "Aide-moi à comprendre ce sujet avec une explication adaptée à mon niveau et des exercices : ";
        $("chat-input").focus();
      },
    ],
  ])
    tasks.append(button(label, action, "secondary"));
  const emptyTemplate = () => {
    const target = $("chat-messages").querySelector(".chat-empty");
    if (target && !target.querySelector(".assistant-tasks")) {
      target.querySelector(".question-examples")?.remove();
      target
        .querySelector(".assistant-symbol")
        ?.replaceChildren(SurvieUI.icon("M4 4h16v12H9l-5 4z M8 8h8 M8 12h5"));
      target.querySelector("h2").textContent = "Comment puis-je vous aider ?";
      target.append(tasks);
    }
  };
  emptyTemplate();
  document.addEventListener("survie:new-conversation", emptyTemplate);
})();
