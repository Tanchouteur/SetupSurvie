async page => {
  const base='http://10.0.3.2:8769',checks=[],errors=[];let searches=0;
  const check=(v,label)=>{if(!v)throw Error(label);checks.push(label);};
  page.on('pageerror',e=>errors.push(e.message));
  page.on('request',r=>{if(new URL(r.url()).pathname==='/api/search')searches++;});
  await page.route('**/api/inventory',r=>r.fulfill({json:{
    books:[{id:'wikipedia_fr_all',title:'Encyclopédie de référence',language:'Français',description:'Sciences et histoire illustrées',ready:true,url:'/content/wikipedia_fr_all/',bytes:100},
           {id:'atlas_en.zim.part',title:'Atlas en cours',language:'Anglais',description:'Téléchargement incomplet',ready:false,bytes:4}],
    guides:[{id:'guide:energie-fr.pdf',title:'Guide d’électricité',language:'Français',description:'Organisme de test · Édition 2026',ready:true,bytes:3}],models:[],note:'Inventaire fictif de recette'}
  }));
  await page.setViewportSize({width:1440,height:950});
  await page.goto(base+'/#/bibliotheque/collections');await page.waitForFunction(()=>S.authReady&&S.user);
  await page.waitForFunction(()=>document.querySelectorAll('#next-collections .data-card').length===3);
  const field=page.locator('#collection-filter'),visible=()=>page.locator('#next-collections .data-card:visible').count();
  const opening=await page.locator('#data-books a').getAttribute('href');
  check(new URL(opening).pathname==='/content/wikipedia_fr_all/','Lien direct Kiwix conservé');
  await field.fill('ELECTRICITE');check(await visible()===1,'Recherche insensible aux accents et à la casse');
  await field.fill('fr energie');check(await visible()===1,'Mots multiples dans le nom de fichier');
  await field.fill('reference encyclopedie');check(await visible()===1,'Mots dans un ordre différent');
  check((await page.locator('#collection-filter-count').textContent()).includes('1 / 3'),'Compteur de résultats');
  check(searches===0,'Filtre local sans recherche de contenu ni IA');
  await field.fill('atlas');check((await page.locator('#collection-filter-count').textContent()).includes('0 disponible'),'Un partiel ne devient pas une ressource ouvrable');
  await field.fill('introuvable');check(await visible()===0,'Résultat vide sans cartes parasites');
  check(await page.locator('#collection-filter-empty').isVisible(),'Absence de correspondance expliquée');
  check((await page.locator('#collection-search-inside').getAttribute('href')).includes('q=introuvable'),'Repli vers la recherche dans les documents');
  await field.fill('electricite');
  await page.locator('#navigation [data-route="assistant"]').click();
  await page.locator('#navigation [data-route="bibliotheque"]').click();
  check(await field.inputValue()==='electricite','Filtre conservé entre rubriques');
  await page.reload();await page.waitForFunction(()=>S.authReady&&S.user);
  check(await field.inputValue()==='electricite','Filtre restauré au rechargement');
  await page.locator('#collection-filter-clear').click();
  check(await visible()===3,'Tout afficher restaure les cartes');
  check(await page.locator('#data-books a').getAttribute('href')===opening,'Ouverture inchangée après filtrage');
  await field.fill('electricite');
  await page.locator('#collection-search-inside').click();
  await page.waitForURL(/bibliotheque\/recherche\?q=electricite/);
  check(await page.locator('#library-query').inputValue()==='electricite','Recherche dans le contenu reprend les mots saisis');
  await page.goBack();await page.waitForSelector('#collection-filter:visible');
  check(await field.inputValue()==='electricite','Retour navigateur restaure le filtre');
  await page.setViewportSize({width:320,height:568});
  check(!await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),'Champ utilisable sur petit écran sans débordement');
  check(errors.length===0,'Aucune erreur JavaScript : '+errors.join(','));
  return {checks:checks.length,results:checks};
}
