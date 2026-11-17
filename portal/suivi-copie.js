(() => {
  if (location.hostname !== '127.0.0.1' || location.port !== '18780') return;
  const element = id => document.getElementById(id);
  const go = number => new Intl.NumberFormat('fr-FR', {maximumFractionDigits: 1}).format(number / 1e9);
  const received = new URLSearchParams(location.hash.slice(1)).get('autorisation');
  if (received) {
    sessionStorage.setItem('autorisation-transfert', received);
    history.replaceState(null, '', location.pathname);
  }
  const token = sessionStorage.getItem('autorisation-transfert');
  const headers = token ? {'X-SetupSurvie-Transfer': token} : {};
  const confirmations = {
    copy: 'SetupSurvie sera arrêté pendant la copie. Continuer ?',
    activate: 'Démarrer SetupSurvie depuis le disque de destination ?',
    rollback: 'Arrêter la destination et rendre la source disponible ? Les nouvelles données du SSD resteront sur le SSD.',
  };
  let lastDestination = '';
  let sending = false;
  const path = element('path');
  const buttons = [...element('commands').querySelectorAll('button')];
  for (const button of buttons) {
    button.addEventListener('click', async () => {
      const action = button.dataset.action;
      if (sending || (confirmations[action] && !confirm(confirmations[action]))) return;
      sending = true;
      buttons.forEach(control => { control.disabled = true; });
      try {
        const response = await fetch('/api/suivi-copie/action', {
          method: 'POST', headers: {...headers, 'Content-Type': 'application/json'},
          body: JSON.stringify({action, destination: path.value, confirmed: true}),
        });
        if (!response.ok) throw new Error();
        element('message').textContent = 'Commande transmise à l’assistant.';
      } catch {
        element('message').textContent = 'Commande indisponible. Vérifiez l’assistant sur le PC serveur.';
      } finally {
        sending = false;
      }
    });
  }
  element('guide').hidden = true;
  element('live').hidden = false;
  document.querySelector('.back').href = 'http://127.0.0.1:8080/#appareil/stockage';

  async function refresh() {
    try {
      const response = await fetch('/api/suivi-copie', {cache: 'no-store', headers});
      if (!response.ok) throw new Error();
      const data = await response.json();
      element('commands').hidden = !data.commands;
      if (data.commands) {
        if (document.activeElement !== path && (path.value === lastDestination || !path.value)) {
          path.value = data.destination;
        }
        lastDestination = data.destination;
        element('message').textContent = data.message;
        buttons.forEach(button => { button.disabled = Boolean(data.busy || sending); });
      }
      element('destination').textContent = data.destination;
      element('phase').textContent = data.state === 'interrupted' ? 'Copie interrompue' : data.phase;
      element('progress').hidden = !data.bytes_total;
      if (data.bytes_total) {
        const percent = 100 * data.bytes_verified / data.bytes_total;
        element('progress').value = percent;
        element('volume').textContent = `${go(data.bytes_verified)} / ${go(data.bytes_total)} Go vérifiés (${Math.floor(percent)} %)`;
      } else {
        element('volume').textContent = '';
      }
      if (data.state === 'interrupted') {
        element('file').textContent = data.reason || 'Reprenez la copie dans Transférer SetupSurvie.';
      } else if (data.state === 'running' && data.file_total > 100e6) {
        element('file').textContent = `Fichier en cours · ${go(data.file_bytes)} / ${go(data.file_total)} Go`;
      } else {
        element('file').textContent = data.files_total ? `${data.files_done.toLocaleString('fr-FR')} / ${data.files_total.toLocaleString('fr-FR')} fichiers vérifiés` : '';
      }
      element('updated').textContent = data.updated_at ? 'Dernier point de copie à ' + new Date(data.updated_at * 1000).toLocaleTimeString('fr-FR') : '';
    } catch {
      element('phase').textContent = 'Suivi indisponible';
      element('updated').textContent = 'Rouvrez le suivi depuis Transférer SetupSurvie.';
    }
    setTimeout(refresh, 2500);
  }
  refresh();
})();
