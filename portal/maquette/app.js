/* Prototype isolé : aucune requête API, aucun modèle, aucune opération serveur. */
'use strict';
const $ = id => document.getElementById(id);
const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const TTL = 7 * 86400000;
const prefix = 'survie-maquette-v1:';
function read(key, fallback) {
  try { const item = JSON.parse(localStorage.getItem(prefix + key)); return item && Date.now() - item.at < TTL ? item.value : fallback; } catch (_) { return fallback; }
}
function write(key, value) { try { localStorage.setItem(prefix + key, JSON.stringify({at:Date.now(), value})); } catch (_) { /* Mémoire facultative. */ } }
let profile = read('profile', 'famille');
if (!['famille','visiteur'].includes(profile)) profile = 'famille';
const key = name => profile + ':' + name;
let memory = read(key('navigation'), {tabs:{}, details:{}});
function validMemory(value) { return value && typeof value === 'object' && value.tabs && value.details ? value : {tabs:{}, details:{}}; }
memory = validMemory(memory);
let current = null;
let scenario = 'transfert';
let demoPaused = false;
let switchingProfile = false;
let draft = read(key('draft'), '');
if (typeof draft !== 'string') draft = '';
const collections = [
  {id:'encyclopedie', title:'Encyclopédie illustrée', type:'ENCYCLOPÉDIE', icon:'▤', description:'Explorer les sciences, la nature et les savoirs du quotidien.', language:'Français'},
  {id:'jardin', title:'Le jardin au fil des saisons', type:'GUIDES PRATIQUES', icon:'❧', description:'Des repères pour observer, apprendre et organiser son jardin.', language:'Français'},
  {id:'apprendre', title:'Apprendre en famille', type:'ENSEIGNEMENT', icon:'✎', description:'Comprendre une notion et avancer ensemble, à son rythme.', language:'Français'}
];
const articles = [
  {id:'observation', title:'Tenir un carnet d’observation', collection:'jardin', description:'Une méthode simple pour garder une trace de ce que l’on observe.', text:['Un carnet rassemble vos observations au même endroit. Une date, un dessin et quelques mots peuvent suffire pour commencer.','Choisissez un lieu que vous pouvez observer régulièrement. Notez ce qui change : la lumière, la présence de feuilles ou les couleurs.','Pour comparer deux observations, essayez de décrire la même chose à chaque fois. Gardez séparées votre observation et votre explication possible.']},
  {id:'saisons', title:'Comprendre le rythme des saisons', collection:'encyclopedie', description:'Observer les changements de la nature au cours de l’année.', text:['Les saisons permettent de décrire des changements qui se répètent au cours de l’année. La lumière et les paysages évoluent progressivement.','Pour commencer, vous pouvez observer un même arbre chaque semaine et dessiner ce qui change.','Ce texte est un exemple de mise en page, sans source documentaire associée. Il ne fait pas partie de la bibliothèque installée.']},
  {id:'mesurer', title:'Apprendre à mesurer une longueur', collection:'apprendre', description:'Comparer, choisir une unité et noter un résultat.', text:['Mesurer consiste à comparer une grandeur à une unité choisie. Pour une longueur, on peut utiliser une règle graduée.','Avant de lire le résultat, vérifiez où se trouve le zéro de la règle. Notez le nombre et l’unité ensemble.','Exercice : choisissez trois objets, estimez leur longueur, puis comparez vos estimations avec une mesure.']}
];
const names = {accueil:'Accueil', bibliotheque:'Bibliothèque', assistant:'Assistant', cartes:'Cartes', appareil:'Mon appareil'};
function link(path, text, cls='') { return `<a href="#/${path}"${cls ? ` class="${cls}"` : ''}>${text}</a>`; }
function head(kicker, title, description) { return `<div class="page-head"><div class="eyebrow">${kicker}</div><h1>${title}</h1><p>${description}</p></div>`; }
function note(text, warning=false) { return `<div class="note${warning?' warning':''}">${text}</div>`; }
function tabs(section, items, active) { return `<nav class="tabs" aria-label="${names[section]} : rubriques">${items.map(([id,label])=>`<a href="#/${section}/${id}"${id===active?' aria-current="page"':''}>${label}</a>`).join('')}</nav>`; }
function state(text, extra='') { return `<span class="status ${extra}"><span class="dot" aria-hidden="true"></span>${text}</span>`; }
function collectionCard(c) { return `<a class="card card-link" href="#/bibliotheque/collection?id=${c.id}"><span class="icon" aria-hidden="true">${c.icon}</span><div class="eyebrow">${c.type}</div><h3>${c.title}</h3><p>${c.description}</p><span class="chip">${c.language} · Exemple</span><span class="arrow">Ouvrir la collection →</span></a>`; }
function articleList(items) { return items.map(a=>link(`bibliotheque/document?id=${a.id}`,`<strong>${a.title}</strong><span>${a.description}</span>`,'reading-link')).join(''); }
function activity() { return `<div class="activity-strip"><div><strong>Votre bibliothèque s’enrichit</strong><p>Exemple : deux transferts en cours, sans utiliser l’assistant.</p></div>${link('appareil/telechargements','Voir le suivi →')}</div>`; }
function searchForm(query='', filter='fr') { return `<form class="search" id="search-form"><label><span class="sr-only">Rechercher dans les documents de démonstration</span><input type="search" name="query" maxlength="150" value="${esc(query)}" placeholder="Un sujet, un livre, un savoir-faire…"></label><select name="language" aria-label="Langue des documents"><option value="fr"${filter==='fr'?' selected':''}>Français</option><option value="all"${filter==='all'?' selected':''}>Toutes les langues</option></select><button type="submit">Rechercher</button></form>`; }
function home() { return `<div class="hero"><div><div class="eyebrow">VOTRE BIBLIOTHÈQUE FAMILIALE</div><h1>De quoi avez-vous<br>envie d’apprendre ?</h1><p>Ouvrez un livre, explorez un sujet ou posez une question. Retrouvez vos repères, même sans Internet.</p></div><img src="/branding/logo.png" alt="Feu de camp et livre ouvert"></div>${searchForm()}<div class="suggestions">${link('bibliotheque/recherche?q=jardin','Le jardin')}${link('bibliotheque/recherche?q=apprendre','Apprendre ensemble')}${link('bibliotheque/recherche?q=observation','Observer la nature')}</div><div class="grid two">${link('assistant',`<span class="icon" aria-hidden="true">◌</span><h2>Comprendre avec l’assistant</h2><p>Une question, une explication, un document à éclaircir.</p><span class="arrow">${draft?'Retrouver mon brouillon':'Préparer une question'} →</span>`,'card card-link')}${link('cartes',`<span class="icon" aria-hidden="true">⌖</span><h2>Retrouver vos repères</h2><p>Consulter une carte et les trajets préparés.</p><span class="arrow">Explorer les cartes →</span>`,'card card-link')}</div><div class="section-heading"><h2>À portée de lecture</h2>${link('bibliotheque/collections','Toutes les collections →')}</div><div class="grid">${collections.map(collectionCard).join('')}</div>${activity()}`; }
function library(route) {
  const tab = route.tab;
  if (tab==='collection') {
    const c = collections.find(c=>c.id===route.params.get('id'));
    if (!c) return missing();
    return `${link('bibliotheque/collections','← Les collections','back')}${head(c.type,c.title,'Collection de démonstration · Français · Lecture sans assistant')}<div class="card reader"><h2>Explorer cette collection</h2><p>${c.description}</p>${articleList(articles.filter(a=>a.collection===c.id))}${note('Ces quelques pages fictives servent à essayer l’ouverture directe d’une collection. Les vraies encyclopédies restent accessibles dans le portail actuel.')}<a href="/#data">Ouvrir mes vraies collections dans le portail actuel ↗</a></div>`;
  }
  if (tab==='document') {
    const a = articles.find(a=>a.id===route.params.get('id'));
    if (!a) return missing();
    return `${link(`bibliotheque/collection?id=${a.collection}`,'← La collection','back')}${head('LECTURE · EXEMPLE FICTIF',a.title,'Un exemple de lecture pour tester les liens, le retour et les favoris.')}<article class="card reader"><span class="chip">Texte de démonstration · Sans source documentaire</span>${a.text.map(t=>`<p>${t}</p>`).join('')}<div class="actions"><button class="secondary" id="favorite" data-article="${a.id}">${favorites().includes(a.id)?'Retirer des favoris de démo':'Ajouter aux favoris de démo'}</button>${link('assistant', 'Préparer une question','button')}</div>${note('Ce document ne représente pas une source consultée par l’assistant. Aucun contenu n’est ajouté à votre bibliothèque réelle.')}</article>`;
  }
  const nav = tabs('bibliotheque',[['collections','Collections'],['recherche','Rechercher'],['parcours','Parcours'],['favoris','Mes favoris'],['traductions','Traductions']],tab);
  let body = '';
  if (tab==='collections') body=`<p class="muted">Vous pouvez ouvrir une collection directement, sans lancer de recherche.</p><div class="grid">${collections.map(collectionCard).join('')}</div>${note('Collections fictives pour essayer la navigation.')}<a href="/#data">Consulter les encyclopédies et guides réellement installés ↗</a>`;
  if (tab==='recherche') {
    const q = route.params.get('q') || ''; const normalized=q.toLocaleLowerCase('fr');
    const results = articles.filter(a=>(a.title+' '+a.description+' '+collections.find(c=>c.id===a.collection).title).toLocaleLowerCase('fr').includes(normalized));
    body=`${searchForm(q,route.params.get('lang')||'fr')}<p class="result-count">${results.length} résultat(s) dans les exemples de la maquette</p><div class="card">${results.length?articleList(results):'<h2>Aucun exemple ne correspond</h2><p>Essayez « jardin », « observation » ou « mesurer ». La vraie recherche reste dans le portail actuel.</p>'}</div>`;
  }
  if (tab==='favoris') body=`<div class="card"><h2>Vos lectures à retrouver</h2>${favorites().length?articleList(articles.filter(a=>favorites().includes(a.id))):'<p>Aucun favori de démonstration. Ouvrez un document, puis ajoutez-le ici.</p>'}</div>${note('Ces favoris sont propres à cette maquette et à ce profil fictif. Vos favoris réels sont conservés dans le portail actuel.')}`;
  if (tab==='parcours') body=`<div class="grid two"><article class="card"><span class="icon" aria-hidden="true">❧</span><h2>Observer son jardin</h2><p>Un exemple de parcours pour apprendre progressivement.</p><details data-memory="parcours"><summary>Voir les étapes</summary><ol><li>Choisir un lieu d’observation.</li><li>Prendre des notes régulières.</li><li>Comparer ses observations.</li></ol></details>${link('bibliotheque/document?id=observation','Lire le premier document →')}</article><article class="card"><h2>Apprendre à mesurer</h2><p>Comprendre une notion, puis essayer un exercice.</p>${link('bibliotheque/document?id=mesurer','Commencer →')}</article></div>`;
  if (tab==='traductions') body=`<div class="card"><h2>Les traductions partagées</h2><p>Leur place dans la future bibliothèque : avec le document original, la mention « traduction IA » et les avertissements de qualité.</p><p>Aucune traduction réelle n’est chargée dans la maquette.</p><a href="/#library">Retrouver les traductions du portail actuel ↗</a></div>`;
  return `${head('BIBLIOTHÈQUE','Un livre, un sujet, une découverte.','Explorez les collections ou cherchez une information dans leurs documents.')}${nav}${body}`;
}
function favorites() { const list=read(key('favorites'),[]); return Array.isArray(list)?list.filter(id=>articles.some(a=>a.id===id)):[]; }
function assistant() { return `${head('ASSISTANT','Prenons le temps de comprendre.','Préparez une question et choisissez le temps à y consacrer.')}<div class="chat-layout"><aside class="card chat-history"><h2>Vos échanges</h2><p class="small muted">Historique de démonstration</p>${link('assistant','Nouvelle question')}${link('bibliotheque/document?id=observation','Un document pour commencer →')}<a href="/#chat">Mes vraies conversations ↗</a></aside><div><div class="card chat-space"><div class="icon" aria-hidden="true">◌</div><h2>Qu’aimeriez-vous comprendre ?</h2><p>Votre brouillon vous attend si vous changez de page. Aucune question n’est envoyée depuis la maquette.</p></div><form id="draft-form" class="compose"><label for="draft">Votre question</label><textarea id="draft" maxlength="20000" rows="4" placeholder="Écrivez votre question avec vos mots…">${esc(draft)}</textarea><div class="actions"><label>Temps de réponse<select id="response-mode"><option value="rapide">Réponse rapide</option><option value="moyenne">Réponse moyenne</option><option value="approfondie">Réponse approfondie</option></select></label><button type="submit">Essayer l’envoi</button></div><p class="small muted" id="draft-status" role="status">Brouillon de démo conservé sur ce navigateur pendant 7 jours au maximum.</p></form>${note('L’assistant réel, la dictée et la traduction restent disponibles dans l’interface actuelle. Aucun modèle ne sera démarré par cette maquette.')}<a href="/#chat">Ouvrir l’assistant actuel ↗</a></div></div>`; }
function mapPage(route) { return `${head('CARTES','Vos repères, autour de vous.','Consultez une zone et retrouvez les trajets déjà préparés.')}${tabs('cartes',[['explorer','Explorer'],['reperes','Mes repères'],['trajets','Itinéraires']],route.tab)}${route.tab==='explorer'?`<div class="map-demo" aria-label="Illustration cartographique fictive, sans données géographiques"><svg viewBox="0 0 800 330" aria-hidden="true"><path d="M0 160 Q150 200 230 110 T490 145 T800 80" fill="none" stroke="#c2d8db" stroke-width="28"/><path d="M100 0 Q180 110 260 330 M0 250 Q280 190 800 260 M500 0 L390 330" fill="none" stroke="#fcfbef" stroke-width="12"/><path d="M100 0 Q180 110 260 330 M0 250 Q280 190 800 260 M500 0 L390 330" fill="none" stroke="#c9c5ac" stroke-width="2"/><g fill="#b5c5a1"><circle cx="610" cy="110" r="56"/><circle cx="680" cy="145" r="40"/><circle cx="64" cy="75" r="37"/></g><g fill="#d1c6af"><rect x="260" y="145" width="24" height="18"/><rect x="300" y="170" width="30" height="22"/><rect x="345" y="150" width="19" height="20"/></g><circle cx="330" cy="210" r="9" fill="#285a43" stroke="white" stroke-width="4"/></svg><div class="map-caption"><strong>Exemple de zone préparée</strong>Illustration uniquement · Aucun lieu ni trajet réel</div></div>`:`<div class="card"><h2>${route.tab==='reperes'?'Un endroit à retrouver':'Un trajet déjà préparé'}</h2><p>${route.tab==='reperes'?'Exemple : le point de départ de la famille.':'Exemple : le parcours de promenade, avec ses étapes et sa fiche.'}</p>${link('cartes/explorer','Afficher l’illustration →')}</div>`}<div class="note mobile-only">Sur téléphone, priorité à la carte, aux repères et aux trajets préparés. La création et la préparation complexes se font depuis un ordinateur.</div><div class="actions"><a class="button secondary" href="/cartes.html">Ouvrir les vraies cartes ↗</a>${link('appareil/telechargements','Préparer une zone sur ordinateur →','desktop-only')}</div><details data-memory="map-coverage"><summary>Qu’est-ce qui est disponible hors ligne ?</summary><p>Le fond de carte, les adresses, le relief et les itinéraires se préparent séparément. Leur présence réelle n’est pas vérifiée dans cette maquette.</p></details>`; }
function scenarios() { return `<label class="small">État à essayer dans la maquette<select id="scenario"><option value="transfert"${scenario==='transfert'?' selected':''}>Téléchargement en cours</option><option value="verification"${scenario==='verification'?' selected':''}>Vérification du fichier</option><option value="jeu"${scenario==='jeu'?' selected':''}>Assistant en mode jeu</option><option value="inconnu"${scenario==='inconnu'?' selected':''}>Suivi indisponible</option></select></label>`; }
function machine(route) {
  const nav=tabs('appareil',[['ensemble','Vue d’ensemble'],['activite','Activité'],['telechargements','Téléchargements'],['stockage','Stockage'],['reglages','Réglages']],route.tab);
  const unknown=scenario==='inconnu';
  let body='';
  if (route.tab==='ensemble') body=`${note('Vous regardez le PC qui héberge SetupSurvie, même depuis votre téléphone. Toutes les valeurs ci-dessous sont fictives.')}<div class="grid"><article class="card"><h3>Bibliothèque</h3>${state(unknown?'État inconnu':'Lecture disponible',unknown?'unknown':'')}<p class="small muted">${unknown?'Impossible de vérifier le service.':'Encyclopédies et guides accessibles sans démarrer l’IA.'}</p></article><article class="card"><h3>Assistant</h3>${state(unknown?'État inconnu':scenario==='jeu'?'En pause · mode jeu':'Arrêté volontairement',unknown?'unknown':'warning')}<p class="small muted">Les documents restent consultables lorsque l’IA est arrêtée.</p></article><article class="card"><h3>Cartes</h3>${state(unknown?'État inconnu':'Zone de démonstration',unknown?'unknown':'')}<p class="small muted">Fond, adresses, relief et itinéraires sont distincts.</p></article></div>${unknown?note('Le suivi ne répond plus. Cela ne prouve pas que le serveur ou le téléchargement est arrêté.',true):activity()}<div class="section-heading"><h2>Les ressources du PC</h2>${link('appareil/stockage','Voir le stockage →')}</div><div class="grid compact"><article class="card stat"><h3>Espace libre</h3><strong>${unknown?'—':'640 Go'}</strong><p>${unknown?'Mesure indisponible':'Sur le volume documentaire · Exemple'}</p></article><article class="card stat"><h3>Mémoire du PC</h3><strong>${unknown?'—':'12 / 32 Go'}</strong><p>Tous les programmes du PC · Exemple</p></article><article class="card stat"><h3>Carte graphique</h3><strong>${unknown?'—':scenario==='jeu'?'78 %':'3 %'}</strong><p>Activité globale, jeux compris · Exemple</p></article></div><details data-memory="machine-details"><summary>Voir les mesures détaillées</summary><div class="card"><div class="row"><div><h3>Mémoire vidéo</h3><p>Exemple fictif</p></div><span>${unknown?'Indisponible':'1,2 / 8 Go'}</span></div><div class="row"><div><h3>Température GPU</h3><p>Si la mesure existe sur ce PC</p></div><span>${unknown?'Indisponible':'42 °C · exemple'}</span></div><div class="row"><div><h3>Questions en cours</h3></div><span>${unknown?'Inconnu':'0 · exemple'}</span></div></div></details>`;
  if (route.tab==='activite') body=`<div class="card"><h2>Ce que fait le PC</h2><div class="row"><div><h3>Enrichissement de la bibliothèque</h3><p>Deux collections dans le plan fictif.</p></div>${link('appareil/telechargements','Voir le détail →')}</div><div class="row"><div><h3>Assistant</h3><p>Aucune question réelle n’est envoyée par la maquette.</p></div><span>Au repos · exemple</span></div><div class="row"><div><h3>Traductions</h3><p>Les textes et brouillons restent dans leur conversation.</p></div><a href="/#chat">Portail actuel ↗</a></div></div>`;
  if (route.tab==='telechargements') body=`<article class="card"><div class="eyebrow">PLAN DE DÉMONSTRATION</div><h2>${unknown?'Le suivi est momentanément indisponible':demoPaused?'Téléchargement en pause':scenario==='verification'?'Vérification du fichier reçu':'Votre bibliothèque s’enrichit'}</h2><p>${unknown?'Dernier exemple connu : 128 Go vérifiés sur 240 Go. Cet état peut être périmé.':'128 Go sur 240 Go reçus et vérifiés · exemple fictif'}</p>${unknown?'':'<progress value="128" max="240" aria-label="Volume reçu et vérifié dans le plan fictif"></progress>'}<p class="small muted">${scenario==='verification'?'La vérification peut prendre plusieurs minutes sans hausse du volume téléchargé.':'Les fichiers partiels ne sont pas encore comptés comme disponibles.'}</p><div class="row"><div><h3>Encyclopédie illustrée</h3><p>${scenario==='verification'?'12 Go reçus · vérification en cours':'8 Go transférés sur 12 Go'}</p></div><span>${unknown?'État inconnu':demoPaused?'En pause':scenario==='verification'?'Vérification':'Téléchargement'}</span></div><div class="row"><div><h3>Apprendre en famille</h3><p>Exemple : prochain fichier du plan</p></div><span>${unknown?'État inconnu':'En attente'}</span></div><div class="actions desktop-only">${unknown?'':`<button id="pause-demo" class="secondary">${demoPaused?'Reprendre':'Mettre en pause'} · démo</button>`}<a href="/#data">Gérer mes téléchargements réels ↗</a></div><p class="small muted">Vous pouvez fermer cette page. La maquette ne commande aucun transfert réel.</p></article><div class="note mobile-only">Le téléphone permet de suivre la progression. La préparation et les commandes avancées restent sur ordinateur.</div><details data-memory="download-completed"><summary>Déjà terminé dans cet exemple</summary><div class="card"><h3>Le jardin au fil des saisons</h3><p>Exemple : fichier vérifié et disponible à la lecture.</p>${link('bibliotheque/collection?id=jardin','Ouvrir la collection de démonstration →')}</div></details>`;
  if (route.tab==='stockage') body=`<div class="grid compact"><article class="card stat"><h3>Volume documentaire</h3><strong>${unknown?'—':'640 Go'}</strong><p>Espace libre · exemple fictif</p></article><article class="card stat"><h3>Capacité du volume</h3><strong>${unknown?'—':'2 000 Go'}</strong><p>Ce disque n’est pas mesuré par la maquette</p></article></div><article class="card" style="margin-top:20px"><h2>Ce qui occupe le disque</h2>${[['Bibliothèque et guides','Documents conservés'],['Cartes et itinéraires','Ressources géographiques'],['Modèles de l’assistant','Présents sur disque, pas forcément chargés'],['Fichiers en cours','Partiels conservés pour la reprise']].map(([t,d])=>`<div class="row"><div><h3>${t}</h3><p>${d}</p></div><span>Taille non mesurée</span></div>`).join('')}</article>${note('Les tailles par catégorie seront raccordées aux mesures réelles dans un lot ultérieur. Aucun nettoyage ni suppression depuis la maquette.')}`;
  if (route.tab==='reglages') body=`<div class="card settings-list"><h2>Préparer et entretenir l’appareil</h2>${[['Profils de la famille','Sans mot de passe, accessibles sur le réseau','users'],['Ouvrir sur un téléphone','Adresse locale, QR code et fiche à imprimer','connect'],['Lieux de référence','Domicile et point de départ','settings'],['Moteur de l’assistant','Arrêt et reprise explicite, mode jeu respecté','settings'],['Ajouter des contenus','Guides, collections et zones cartographiques','data'],['Contexte et retours','Instructions de l’assistant et retours enregistrés','settings']].map(([t,d,h])=>`<a href="/#${h}"><span><strong>${t}</strong><small>${d}</small></span><span aria-hidden="true">↗</span></a>`).join('')}</div>${note('Ces liens ouvrent les réglages réels dans l’interface actuelle. La maquette n’effectue aucune modification.')}<div class="note mobile-only">Les opérations de préparation complexes se réalisent plus confortablement depuis un ordinateur.</div><div class="actions"><button id="clear-memory" class="secondary">Effacer la mémoire de cette maquette</button></div><p class="small muted">Efface seulement les préférences, brouillons et favoris de démonstration de ce navigateur. Aucun effet sur vos données réelles.</p>`;
  return `${head('MON APPAREIL','Comprendre ce qui se passe.','Les documents, l’assistant et les opérations du PC, réunis au même endroit.')}${nav}${body}<div class="card" style="margin-top:28px">${scenarios()}<p class="small muted">Sélecteur de démonstration : ne change aucun service réel.</p></div>`;
}
function missing() { return `${head('PAGE INDISPONIBLE','Cet exemple n’existe plus.','Vos documents réels ne sont pas concernés.')}${link('bibliotheque/collections','Revenir aux collections','button')}`; }
const allowedTabs={bibliotheque:['collections','recherche','parcours','favoris','traductions','collection','document'],cartes:['explorer','reperes','trajets'],appareil:['ensemble','activite','telechargements','stockage','reglages']};
function routeFor(hash) {
  const [path, query=''] = hash.replace(/^#\/?/,'').split('?');
  const [section='accueil', requested] = path.split('/');
  if (!Object.hasOwn(names, section)) return null;
  const allowed=allowedTabs[section];
  const preferred=memory.tabs[section];
  const tab=allowed ? (requested || (allowed.includes(preferred)?preferred:allowed[0])) : '';
  if (allowed && !allowed.includes(tab)) return null;
  return {section,tab,params:new URLSearchParams(query)};
}
function storeMemory() { write(key('navigation'),memory); }
function saveEntry() {
  if (!current) return;
  const focused=document.activeElement;
  history.replaceState({...history.state,scroll:window.scrollY,focus:focused?.id || null},'',location.href);
}
let scrollFrame=0;
window.addEventListener('scroll',()=>{if(!scrollFrame)scrollFrame=requestAnimationFrame(()=>{scrollFrame=0;saveEntry();});},{passive:true});
function saveDraft() { const input=$('draft'); if(input){draft=input.value.slice(0,20000);write(key('draft'),draft);} }
function render(restore=false) {
  const route=routeFor(location.hash);
  current=route;
  const previousScroll=history.state?.scroll || 0;
  const previousFocus=history.state?.focus;
  if (route?.tab && !['document','collection'].includes(route.tab)) { memory.tabs[route.section]=route.tab;storeMemory(); }
  if (route) {memory.last=location.hash;storeMemory();}
  $('content').innerHTML=!route?missing():({accueil:home,bibliotheque:()=>library(route),assistant,cartes:()=>mapPage(route),appareil:()=>machine(route)})[route.section]();
  document.querySelectorAll('#navigation a').forEach(a=>{if(a.dataset.section===route?.section)a.setAttribute('aria-current','page');else a.removeAttribute('aria-current');});
  $('breadcrumb').textContent=route ? names[route.section] : 'Page indisponible';
  document.title=(route ? names[route.section] : 'Page indisponible')+' · Maquette SetupSurvie';
  $('profile-name').textContent=(profile==='famille'?'Famille':'Visiteur')+' · démo';
  document.querySelector('.avatar').textContent=profile==='famille'?'F':'V';
  document.querySelectorAll('details[data-memory]').forEach(d=>{
    d.open=!!memory.details[d.dataset.memory];
    d.addEventListener('toggle',()=>{memory.details[d.dataset.memory]=d.open;storeMemory();});
  });
  if($('draft')) {
    $('draft').addEventListener('input',saveDraft);
    $('response-mode').value=read(key('mode'),'rapide');
    $('response-mode').onchange=e=>write(key('mode'),e.target.value);
    $('draft-form').onsubmit=e=>{e.preventDefault();saveDraft();$('draft-status').textContent='Essai terminé : brouillon conservé. Aucun message envoyé, aucun modèle démarré.';};
  }
  if($('search-form')) $('search-form').onsubmit=e=>{e.preventDefault();const form=new FormData(e.target);navigate('#/bibliotheque/recherche?q='+encodeURIComponent(form.get('query'))+'&lang='+encodeURIComponent(form.get('language')));};
  if($('favorite')) $('favorite').onclick=e=>{
    const id=e.target.dataset.article;const items=favorites();const next=items.includes(id)?items.filter(x=>x!==id):[...items,id];write(key('favorites'),next);e.target.textContent=next.includes(id)?'Retirer des favoris de démo':'Ajouter aux favoris de démo';$('announcement').textContent=next.includes(id)?'Favori de démonstration ajouté.':'Favori de démonstration retiré.';
  };
  if($('scenario')) $('scenario').onchange=e=>{scenario=e.target.value;saveEntry();render(true);};
  if($('pause-demo')) $('pause-demo').onclick=()=>{demoPaused=!demoPaused;saveEntry();render(true);};
  if($('clear-memory')) $('clear-memory').onclick=()=>{
    try {for(const k of Object.keys(localStorage))if(k.startsWith(prefix))localStorage.removeItem(k);}catch(_){}
    memory={tabs:{},details:{}};draft='';profile='famille';navigate('#/accueil');$('announcement').textContent='Mémoire de la maquette effacée. Vos données réelles sont conservées.';
  };
  requestAnimationFrame(()=>{
    if(restore){const focus=previousFocus&&document.getElementById(previousFocus);(focus||$('content')).focus({preventScroll:true});window.scrollTo(0,previousScroll);}
    else {$('content').focus({preventScroll:true});window.scrollTo(0,0);}
  });
}
function navigate(hash) {
  saveDraft();saveEntry();
  if (hash===location.hash)return;
  history.pushState({scroll:0},'',hash);render();
}
document.addEventListener('click',e=>{
  const skip=e.target.closest('a[href="#content"]');
  if(skip){e.preventDefault();$('content').focus();return;}
  const a=e.target.closest('a[href^="#/"]');
  if(!a||e.defaultPrevented||e.button!==0||e.metaKey||e.ctrlKey||e.shiftKey||e.altKey||a.target==='_blank')return;
  e.preventDefault();navigate(a.getAttribute('href'));
});
history.scrollRestoration='manual';
window.addEventListener('popstate',()=>{
  if(!switchingProfile)saveDraft();
  switchingProfile=false;
  const dialog=$('profile-dialog');
  if(history.state?.profileDialog){if(!dialog.open)dialog.showModal();return;}
  if(dialog.open)dialog.close();
  render(true);
});
window.addEventListener('pagehide',()=>{saveDraft();saveEntry();});
document.addEventListener('visibilitychange',()=>{if(document.hidden){saveDraft();saveEntry();}});
$('profile-open').onclick=()=>{saveEntry();history.pushState({...history.state,profileDialog:true},'',location.href);$('profile-dialog').showModal();};
$('profile-dialog').addEventListener('close',()=>{if(history.state?.profileDialog)history.back();});
document.querySelectorAll('[data-profile]').forEach(b=>b.onclick=()=>{
  saveDraft();switchingProfile=true;profile=b.dataset.profile;write('profile',profile);memory=validMemory(read(key('navigation'),{tabs:{},details:{}}));draft=read(key('draft'),'');
  if(typeof draft!=='string')draft='';$('profile-dialog').close();
});
// Contrairement au portail réel, ces profils sont des exemples locaux uniquement.
window.addEventListener('storage',e=>{if(e.key===prefix+'profile'){$('announcement').textContent='Le profil de démo a changé dans un autre onglet. Cet onglet conserve son contexte.';}});
const webui=new URL(location.href);webui.port=location.protocol==='https:'?'8444':'3000';webui.pathname='/';webui.hash='';webui.search='';document.querySelectorAll('.native-webui').forEach(a=>a.href=webui.href);
const initial=location.hash.startsWith('#/')?location.hash:(memory.last&&routeFor(memory.last)?memory.last:'#/accueil');
history.replaceState({...history.state, profileDialog:false, scroll:history.state?.scroll || 0},'',initial);
render(true);
if(window.ResizeObserver)new ResizeObserver(()=>{document.documentElement.style.setProperty('--preview',document.querySelector('.preview').offsetHeight+'px');}).observe(document.querySelector('.preview'));
