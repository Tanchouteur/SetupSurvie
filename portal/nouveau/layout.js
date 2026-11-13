/* Reorganise les contrôles existants sans les recopier ni changer leurs actions. */
(() => {
  const get=id=>document.getElementById(id);
  const make=(tag,cls,html='')=>{const n=document.createElement(tag);n.className=cls;n.innerHTML=html;return n;};
  const route=(path,label)=>`<a href="#/${path}" data-route="${path}">${label}</a>`;
  const header=(title,text)=>make('div','page-heading',`<div class="eyebrow">VOTRE SERVEUR LOCAL</div><h1>${title}</h1><p>${text}</p>`);
  const notice=make('div','next-banner','<strong>Nouvelle interface</strong><span>Vos documents et profils habituels, une organisation plus simple.</span><a href="/classique/" id="next-classic">Interface classique ↗</a>');
  document.body.prepend(notice);
  const nav=make('nav','next-main-nav');nav.id='navigation';nav.setAttribute('aria-label','Navigation principale');
  for(const [path,icon,label] of [['accueil','⌂','Accueil'],['bibliotheque','▤','Bibliothèque'],['assistant','◌','Assistant'],['cartes','⌖','Cartes'],['appareil','◴','Mon appareil']]){
    const a=make('a','nav-item',`<span aria-hidden="true">${icon}</span><span>${label}</span>`);a.href='#/'+path;a.dataset.route=path;nav.append(a);
  }
  get('main-navigation').querySelector('nav').replaceWith(nav);
  const history=make('details','next-history');history.append(make('summary','','Vos conversations'));history.append(document.querySelector('.sidebar-section'));
  get('view-chat').querySelector('.chat-top').after(history);
  get('admin-nav')?.remove(); // Its ID is recreated as a visible-in-Famille settings shortcut.
  const admin=make('button','quiet','Réglages de l’appareil');admin.id='admin-nav';admin.dataset.view='settings';admin.hidden=true;
  document.querySelector('.sidebar-bottom').prepend(admin);
  document.querySelector('.brand').href='#/accueil';document.querySelector('.brand').dataset.route='accueil';
  document.querySelectorAll('a[href="/maquette/"],a[href="/nouveau/"]').forEach(a=>{a.href='/classique/';a.innerHTML='<strong>Interface classique ↗</strong><small>Retrouver la présentation habituelle.</small>';});
  get('view-home').querySelector('h1').innerHTML='De quoi avez-vous<br>envie d’apprendre ?';
  get('view-home').querySelector('.welcome').classList.add('next-welcome');
  const lib=get('view-library'),oldHeading=lib.querySelector('.page-heading');
  oldHeading.replaceWith(header('Un livre, un sujet, une découverte.','Ouvrez une collection directement ou recherchez une information dans les documents.'));
  const libTabs=make('nav','next-tabs');libTabs.setAttribute('aria-label','Rubriques de la bibliothèque');
  libTabs.innerHTML=[['collections','Collections'],['recherche','Rechercher'],['parcours','Parcours'],['favoris','Mes favoris'],['traductions','Traductions']].map(([p,l])=>route('bibliotheque/'+p,l)).join('');
  lib.querySelector('.page-heading').after(libTabs);
  const learningBrowser=get('learning-browser');
  const search=make('div','next-library-pane');search.id='next-search';
  for(const child of [...lib.children])if(child!==lib.querySelector('.page-heading')&&child!==libTabs)search.append(child);
  const learning=make('div','next-library-pane');learning.id='next-learning';learningBrowser.open=true;learning.append(learningBrowser);
  const collections=make('div','next-library-pane');collections.id='next-collections';
  collections.append(make('p','muted','Ces collections sont réellement présentes sur le serveur. Leur disponibilité de lecture est vérifiée séparément de leur téléchargement.'));
  collections.append(make('h2','','Encyclopédies et livres'),get('data-books'),make('h2','','Guides et fiches pratiques'),get('data-guides'));
  const invNotice=make('p','small muted');invNotice.id='next-inventory-notice';invNotice.setAttribute('role','status');collections.prepend(invNotice);
  lib.append(collections,search,learning);
  const storage=make('section','view');storage.id='view-storage';storage.hidden=true;
  storage.append(header('L’espace de votre bibliothèque.','Les fichiers sur disque sont distincts des modèles chargés en mémoire.'),get('data-summary'),make('h2','','Modèles enregistrés sur le disque'),get('data-models'),get('data-preparation'));
  get('main').append(storage);
  const maps=make('section','view');maps.id='view-maps';maps.hidden=true;
  maps.append(header('Vos repères, autour de vous.','Retrouvez les cartes locales, vos points et les itinéraires préparés.'));
  maps.append(make('article','panel next-map-intro','<h2>Cartes hors ligne</h2><p>Le fond de carte, les adresses, le relief et le réseau d’itinéraires sont préparés séparément. La présence d’un fond ne signifie pas que toutes ces données sont disponibles.</p><a class="button" href="/cartes.html?interface=nouveau">Ouvrir les cartes et mes repères →</a><p class="next-mobile-note">Sur téléphone, privilégiez la consultation des lieux et trajets préparés. Les outils complexes de création restent sur ordinateur.</p>'));
  get('main').append(maps);
  const activity=make('section','view');activity.id='view-activity';activity.hidden=true;activity.append(header('Ce que fait l’appareil.','Le suivi des préparations est indépendant de l’assistant et du navigateur.'));get('main').append(activity);
  get('view-monitor').querySelector('.page-heading').replaceWith(header('Comprendre ce qui se passe.','Ce sont les mesures du PC qui héberge SetupSurvie, même lorsque vous consultez cette page depuis un téléphone.'));
  get('view-data').querySelector('.page-heading').replaceWith(header('Les téléchargements et préparations.','Suivez les transferts en cours avant d’ajouter de nouveaux contenus.'));
  // Inventory grids moved to Library/Storage; remove only the now-empty headings.
  for(const node of [...get('view-data').children])if(node.tagName==='H2')node.remove();
  const machineTabs=make('nav','next-tabs');machineTabs.id='next-machine-tabs';machineTabs.setAttribute('aria-label','Rubriques de l’appareil');
  machineTabs.innerHTML=[['ensemble','Vue d’ensemble'],['activite','Activité'],['telechargements','Téléchargements'],['stockage','Stockage'],['reglages','Réglages']].map(([p,l])=>route('appareil/'+p,l)).join('');
  get('view-monitor').querySelector('.page-heading').after(machineTabs);
  for(const target of ['view-monitor','view-data','view-activity']){
    const block=make('article','panel next-activity');block.innerHTML='<h2 class="next-transfer-title">Lecture de l’activité…</h2><p class="next-transfer-message" role="status"></p><progress class="next-transfer-progress" max="1" aria-label="Volume du plan déjà vérifié" hidden></progress><div class="next-transfer-files"></div><p class="next-transfer-time small muted"></p><p class="small muted">Les fichiers partiels ne sont pas encore vérifiés. Un reçu de vérification ne prouve pas la disponibilité dans le lecteur ou la recherche.</p>';
    get(target).querySelector('.page-heading').after(block);
  }
  const services=make('article','panel');services.id='next-services';services.innerHTML='<h2>Les fonctions disponibles</h2><p id="next-service-health" role="status">Vérification des services…</p>';get('view-monitor').querySelector('.engine-panel').before(services);
  const settings=get('view-settings');settings.querySelector('.page-heading h1').textContent='Préparer et entretenir l’appareil.';
  settings.querySelector('.page-heading p').textContent='Ces commandes sont proposées dans le profil Famille, librement accessible sur le réseau local.';
  for(const h of settings.querySelectorAll('h2'))if(h.textContent==='Comptes et accès'){h.textContent='Profils de la famille';h.nextElementSibling.textContent='Créez un profil pour ranger les conversations et les favoris de chaque personne.';h.parentElement.querySelector('button').textContent='Gérer les profils';}
  const tools=make('div','next-settings-links');tools.innerHTML=route('appareil/profils','Profils')+route('appareil/connexion','Ouvrir sur un téléphone')+route('appareil/telechargements','Téléchargements');settings.querySelector('.page-heading').after(tools);
  tools.after(make('p','next-mobile-note','Les opérations complexes de préparation et les réglages du moteur se font depuis un ordinateur. Les profils et le suivi restent consultables ici.'));
  const memory=make('article','panel');memory.innerHTML='<h2>Mémoire de navigation</h2><p>Effacez seulement les onglets, filtres et brouillons mémorisés sur ce navigateur. Vos conversations et favoris sur le serveur sont conservés.</p><button id="next-clear-memory" class="secondary">Effacer la mémoire de navigation</button>';settings.append(memory);
  get('view-chat').querySelector('h1').textContent='Prenons le temps de comprendre.';
  const bottom=make('div','next-mobile-tools','<a href="/classique/">Interface classique ↗</a><a class="native-webui" href="/">Open WebUI ↗</a><a href="/secours.html">Documents de secours ↗</a>');document.querySelector('footer').before(bottom);
})();
