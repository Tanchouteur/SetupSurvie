/* Addresses are derived from the browser host, so links also work on phones. */
function serviceUrl(port) { const url = new URL(window.location.href); url.port = String(port); url.pathname = '/'; url.search = ''; url.hash = ''; return url.href; }
document.getElementById('chat').href = serviceUrl(3000);
document.getElementById('wiki').href = serviceUrl(8081);
document.getElementById('wiki-search').addEventListener('submit', event => {
  event.preventDefault();
  const url = new URL(serviceUrl(8081)); url.pathname = '/search';
  url.searchParams.set('books.filter.lang', document.getElementById('wiki-language').value);
  url.searchParams.set('pattern', document.getElementById('wiki-query').value);
  window.location.assign(url.href);
});
let documents = [];
function render() {
  const query = document.getElementById('search').value.toLocaleLowerCase('fr');
  const language = document.getElementById('language').value;
  const list = document.getElementById('guides'); list.replaceChildren();
  const matches = documents.filter(d => (d.title + ' ' + d.path).toLocaleLowerCase('fr').includes(query) && (!language || d.language === language));
  for (const doc of matches) {
    const li = document.createElement('li'); const a = document.createElement('a'); const meta = document.createElement('small');
    a.textContent = doc.title; a.href = '/guides/' + doc.path.split('/').map(encodeURIComponent).join('/');
    meta.textContent = `${doc.language.toUpperCase()} · ${doc.format} · ${(doc.bytes / 1024).toFixed(0)} Ko`;
    li.append(a, meta); list.append(li);
  }
  document.getElementById('status').textContent = `${matches.length} document(s). Recherche par titre et chemin ; le contenu complet des guides se recherche dans l’assistant après import.`;
}
document.getElementById('search').addEventListener('input', render);
document.getElementById('language').addEventListener('change', render);
fetch('/catalog/guides.json', {cache:'no-store'}).then(r => { if (!r.ok) throw new Error(); return r.json(); }).then(data => { documents = data.documents; render(); }).catch(() => { document.getElementById('status').textContent = 'Catalogue indisponible. Relancez la commande « catalog » sur le serveur.'; });
