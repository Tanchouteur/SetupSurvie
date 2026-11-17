(() => {
  if (location.hostname !== '127.0.0.1' || location.port !== '18780') return;
  const element = id => document.getElementById(id);
  const go = number => new Intl.NumberFormat('fr-FR', {maximumFractionDigits: 1}).format(number / 1e9);
  element('guide').hidden = true;
  element('live').hidden = false;
  document.querySelector('.back').href = 'http://127.0.0.1:8080/#appareil/stockage';

  async function refresh() {
    try {
      const response = await fetch('/api/suivi-copie', {cache: 'no-store'});
      if (!response.ok) throw new Error();
      const data = await response.json();
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
