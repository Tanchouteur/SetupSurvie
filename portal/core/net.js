/* Couche réseau commune du portail.
 *
 * Chargée avant tous les autres scripts. Elle enveloppe `fetch` une seule fois
 * pour que chaque module, ancien ou nouveau, reçoive des erreurs en français
 * et que l'interface sache quand l'appareil SetupSurvie ne répond plus.
 * Aucune donnée n'est conservée ; seules les requêtes vers `/api/` du même
 * site sont concernées.
 */
(() => {
  if (window.SurvieNet) return;
  const nativeFetch = window.fetch.bind(window);
  const OFFLINE =
    "L’appareil SetupSurvie ne répond pas. Vérifiez qu’il est allumé et que cet appareil est connecté au même réseau Wi-Fi.";
  const RETRY_DELAYS = [3, 5, 10, 15];
  const listeners = new Set();
  const state = { online: true, checking: false, retryAt: 0, attempt: 0, lostAt: 0 };
  let timer = null;
  let leaving = false;

  addEventListener("pagehide", () => { leaving = true; });
  addEventListener("pageshow", () => { leaving = false; });

  function isLocalApi(input) {
    try {
      const raw = typeof input === "string" ? input : input?.url || String(input);
      const url = new URL(raw, location.href);
      return url.origin === location.origin && url.pathname.startsWith("/api/");
    } catch (_) {
      return false;
    }
  }

  function emit() {
    const snapshot = { ...state };
    for (const listener of listeners) {
      try { listener(snapshot); } catch (_) { /* un écouteur ne bloque pas les autres */ }
    }
    document.dispatchEvent(new CustomEvent("survie:connection", { detail: snapshot }));
  }

  function setOnline() {
    clearTimeout(timer);
    timer = null;
    const changed = !state.online;
    Object.assign(state, { online: true, checking: false, retryAt: 0, attempt: 0, lostAt: 0 });
    if (changed) emit();
  }

  function schedule() {
    clearTimeout(timer);
    const delay = RETRY_DELAYS[Math.min(state.attempt, RETRY_DELAYS.length - 1)] * 1000;
    state.attempt += 1;
    state.retryAt = Date.now() + delay;
    state.checking = false;
    timer = setTimeout(probe, delay);
    emit();
  }

  /* Confirme la perte avant de l'annoncer : un seul échec (onglet en fond,
   * navigation en cours) ne suffit pas à afficher le bandeau. */
  async function probe() {
    if (state.checking) return state.online;
    state.checking = true;
    if (!state.online) emit();
    try {
      const response = await nativeFetch("/api/health", { cache: "no-store", credentials: "same-origin" });
      if (response.status < 500 || response.headers.get("content-type")?.includes("json")) {
        setOnline();
        return true;
      }
    } catch (_) { /* toujours injoignable */ }
    if (leaving) { state.checking = false; return false; }
    if (state.online) {
      state.online = false;
      state.lostAt = Date.now();
    }
    schedule();
    return false;
  }

  function suspect() {
    if (leaving || state.checking || !state.online) return;
    probe();
  }

  function networkError(cause) {
    const error = new Error(OFFLINE);
    error.name = "NetworkError";
    error.offline = true;
    error.cause = cause;
    return error;
  }

  window.fetch = async function survieFetch(input, init) {
    const local = isLocalApi(input);
    let response;
    try {
      response = await nativeFetch(input, init);
    } catch (error) {
      if (!local || error?.name === "AbortError") throw error;
      suspect();
      throw networkError(error);
    }
    if (local) {
      const proxyFailure = [502, 503, 504].includes(response.status) &&
        !response.headers.get("content-type")?.includes("json");
      if (proxyFailure) suspect();
      else if (!state.online) setOnline();
    }
    return response;
  };

  /* Traduit un message technique éventuel. Les messages déjà rédigés en
   * français par le serveur ou l'interface sont rendus tels quels. */
  function humanize(value) {
    const text = String(value?.message ?? value ?? "").trim();
    if (!text) return "Une erreur inattendue s’est produite. Réessayez dans quelques instants.";
    if (/failed to fetch|networkerror|network error|load failed|network request failed|err_connection|err_internet/i.test(text)) return OFFLINE;
    if (/unexpected token|unexpected end of json|json\.parse|is not valid json|syntaxerror/i.test(text))
      return "Le service a renvoyé une réponse illisible. Réessayez dans quelques instants.";
    if (/timed? ?out|timeout/i.test(text)) return "Le service met trop de temps à répondre. Réessayez dans quelques instants.";
    if (/aborted|aborterror|the user aborted|signal is aborted/i.test(text)) return "L’opération a été annulée.";
    const http = text.match(/^HTTP\s*(\d{3})/i);
    if (http) return `Le service a répondu par une erreur (code ${http[1]}). Réessayez dans quelques instants.`;
    if (/^(type|reference|range)error\b|is not a function|cannot read propert|undefined is not/i.test(text))
      return "Une erreur inattendue s’est produite dans la page. Rechargez la page ; vos données sont conservées sur l’appareil.";
    return text;
  }

  window.SurvieNet = {
    OFFLINE,
    humanize,
    state: () => ({ ...state }),
    onChange(listener) { listeners.add(listener); return () => listeners.delete(listener); },
    retryNow() { clearTimeout(timer); state.checking = false; return probe(); },
    nativeFetch,
  };
})();
