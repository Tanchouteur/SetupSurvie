async page => {
  const base='http://10.0.3.2:8769',checks=[],errors=[];let searches=0;
  const check=(v,label)=>{if(!v)throw Error(label);checks.push(label);};
  page.on('pageerror',e=>errors.push(e.message));
  page.on('request',r=>{if(new URL(r.url()).pathname==='/api/search')searches++;});
  await page.route('**/api/inventory',r=>r.fulfill({json:{
    books:[{id:'wikipedia_fr_all',title:'Encyclopédie de référence',language:'Français',description:'Sciences et histoire illustrées',ready:true,url:'/content/wikipedia_fr_all/',bytes:100},
           {id:'atlas_en.zim.part',title:'Atlas en cours',language:'Anglais',description:'Téléchargement incomplet',ready:false,bytes:4}],
    guides:[{id:'guide:energie-fr.pdf',title:'Guide d’électricité',language:'Français',description:'Organisme de test · Édition 2026',ready:true,bytes:3},
            {id:'guide:dentist-01.pdf',title:'Where There Is No Dentist — Chapitre 01',language:'Anglais',ready:true,bytes:8},
            {id:'guide:dentist-02.pdf',title:'Where There Is No Dentist — Chapitre 02',language:'Anglais',ready:true,bytes:9},
            {id:'guide:atelier-01.pdf',title:'Atelier pratique — Outils',language:'Français',ready:true,bytes:8},
            {id:'guide:atelier-02.pdf',title:'Atelier pratique — Rangement',language:'Français',ready:true,bytes:9}],models:[],note:'Inventaire fictif de recette'}
  }));
  await page.setViewportSize({width:1440,height:950});
  await page.goto(base+'/#/bibliotheque/collections');await page.waitForFunction(()=>typeof S!=='undefined'&&S.authReady&&S.user);
  // This recipe owns the mocked books/guides. Local media have their own
  // live catalogue and filtering recipe, not the mocked /api/inventory response.
  await page.waitForFunction(()=>document.querySelectorAll('#data-books .data-card,#data-guides .data-card').length===7);
  const field=page.locator('#collection-filter'),visible=()=>page.locator('#data-books .data-card:visible,#data-guides .data-card:visible').count();
  const opening=await page.locator('#data-books a').getAttribute('href');
  check(new URL(opening).pathname==='/content/wikipedia_fr_all/','Lien direct Kiwix conservé');
  await field.fill('ELECTRICITE');check(await visible()===1,'Recherche insensible aux accents et à la casse');
  await field.fill('fr energie');check(await visible()===1,'Mots multiples dans le nom de fichier');
  await field.fill('reference encyclopedie');check(await visible()===1,'Mots dans un ordre différent');
  check((await page.locator('#collection-filter-count').textContent()).includes('1 / 7'),'Compteur de résultats');
  check(searches===0,'Filtre local sans recherche de contenu ni IA');
  await field.fill('atlas');check((await page.locator('#collection-filter-count').textContent()).includes('0 disponible'),'Un partiel ne devient pas une ressource ouvrable');
  await field.fill('introuvable');check(await visible()===0,'Résultat vide sans cartes parasites');
  check(await page.locator('#collection-filter-empty').isVisible(),'Absence de correspondance expliquée');
  check((await page.locator('#collection-search-inside').getAttribute('href')).includes('q=introuvable'),'Repli vers la recherche dans les documents');
  await field.fill('electricite');
  await page.locator('#navigation [data-route="assistant"]').click();
  await page.locator('#navigation [data-route="bibliotheque"]').click();
  check(await field.inputValue()==='electricite','Filtre conservé entre rubriques');
  await page.reload();await page.waitForFunction(()=>typeof S!=='undefined'&&S.authReady&&S.user);
  check(await field.inputValue()==='electricite','Filtre restauré au rechargement : '+page.url()+' / '+await field.inputValue()+' / '+errors.join(','));
  await page.waitForFunction(()=>document.querySelectorAll('#data-guides details.next-collection-group').length===2);
  await page.locator('#collection-filter-clear').click();
  check(await visible()===3,'Effacer le filtre restaure les cartes et replie la série');
  check(await page.locator('#data-books a').getAttribute('href')===opening,'Ouverture inchangée après filtrage');
  const series=page.locator('#data-guides details.next-collection-group').filter({hasText:'Where There Is No Dentist'});
  check(await page.locator('#data-guides details.next-collection-group').filter({hasText:'Atelier pratique'}).count()===1,'Une autre série reçoit le même regroupement');
  check((await series.locator('summary').innerText()).includes('Where There Is No Dentist · 2 documents'),'Un seul groupe pour deux chapitres');
  await series.locator('summary').click();
  check(await series.getByRole('heading',{name:'Chapitre 01'}).isVisible(),'Le groupe ouvre les chapitres');
  check(await series.getByText('Lire le guide',{exact:false}).count()===2,'Chaque chapitre garde sa commande de lecture');
  await series.locator('summary').click();
  await page.waitForFunction(id=>localStorage.getItem('survie-next-v1:'+S.user.id+':detail:'+id)?.includes('"value":false'),await series.getAttribute('id'));
  await field.fill('dentist 02');
  check(await series.getByRole('heading',{name:'Chapitre 02'}).isVisible()&&await visible()===1,'Le filtre ouvre la série et isole son chapitre');
  await page.getByRole('link',{name:'Guides',exact:true}).click();
  check(await series.getByRole('heading',{name:'Chapitre 02'}).isVisible(),'La rubrique garde le chapitre filtré même si le groupe était replié');
  await page.getByRole('link',{name:'Tout',exact:true}).click();
  await page.locator('#collection-filter-clear').click();
  for(const [category,content] of [['livres','#data-books'],['guides','#data-guides'],['videos','#next-videos']]){
    const summary=page.locator(`[data-collection-section="${category}"] > summary`);
    await summary.click();
    check(!await summary.evaluate(element=>element.parentElement.open)&&!await page.locator(content).isVisible(),'La rubrique '+category+' peut être repliée');
    if(category!=='videos'){
      await summary.click();
      check(await page.locator(content).isVisible(),'La rubrique '+category+' peut être rouverte');
    }
  }
  await page.setViewportSize({width:320,height:568});
  const videoLink=page.getByRole('link',{name:'Vidéos',exact:true});
  check(await videoLink.isVisible(),'Vidéos accessible dans la navigation mobile des Collections');
  await videoLink.click();
  await page.waitForURL(/rubrique=videos/);
  check(await page.locator('#next-videos').isVisible()&&await visible()===0,'La rubrique Vidéos présente directement la liste');
  check((await page.locator('#collection-search-inside').getAttribute('href')).includes('kind=videos'),'La recherche depuis Vidéos reste sur les sous-titres');
  await page.reload();
  await page.waitForSelector('#next-videos:visible');
  check(await videoLink.getAttribute('aria-current')==='page','La rubrique Vidéos survit au rechargement');
  await page.getByRole('link',{name:'Guides',exact:true}).click();
  check(await series.isVisible()&&!await page.locator('#next-videos').isVisible(),'Les guides sont accessibles séparément');
  await page.goBack();
  await page.waitForURL(/rubrique=videos/);
  check(await page.locator('#next-videos').isVisible(),'Le retour navigateur retrouve Vidéos');
  const videoSummary=page.locator('#collection-section-videos > summary');
  await videoSummary.click();
  await page.reload();
  await page.waitForFunction(()=>S.authReady&&S.user);
  check(!await page.locator('#next-videos').isVisible(),'La rubrique Vidéos reste repliée au rechargement de son adresse directe');
  await videoLink.click();
  check(await page.locator('#next-videos').isVisible(),'Le bouton Vidéos rouvre explicitement la rubrique');
  await page.getByRole('link',{name:'Tout',exact:true}).click();
  await page.setViewportSize({width:1440,height:950});
  await series.locator('summary').click();
  await page.locator('#collection-section-guides > summary').click();
  await page.locator('#collection-section-livres > summary').click();
  await field.fill('dentist 02');
  await page.reload();
  await page.waitForSelector('#data-guides h3:text-is("Chapitre 02"):visible');
  await page.locator('#collection-filter-clear').click();
  check(!await page.locator('#data-books').isVisible()&&!await page.locator('#data-guides').isVisible(),'Effacer le filtre après rechargement retrouve les rubriques repliées');
  await page.locator('#collection-section-guides > summary').click();
  check(await series.getByRole('heading',{name:'Chapitre 02'}).isVisible(),'La série ouverte est mémorisée même quand sa rubrique était repliée');
  await page.locator('#collection-section-livres > summary').click();
  await page.addStyleTag({content:'.next-collection-section[open] > :not(summary) { min-height: calc(100vh + 300px); }'});
  await page.evaluate(()=>document.fonts.ready);
  for(const width of [1440,320]){
    await page.setViewportSize({width,height:700});
    for(const id of ['livres','guides','videos']){
      const stuck=await page.waitForFunction(({id,width})=>{
        const section=document.getElementById('collection-section-'+id);
        const sectionTop=section.getBoundingClientRect().top;
        if(Math.abs(sectionTop+150)>2){
          window.scrollTo({top:scrollY+sectionTop+150,behavior:'instant'});
          return false;
        }
        const nav=document.querySelector(width>760?'#main-navigation':'.topbar');
        const summary=section.querySelector('summary');
        const gap=summary.getBoundingClientRect().top-nav.getBoundingClientRect().bottom;
        const heading=summary.querySelector('h2').getBoundingClientRect();
        const mask=getComputedStyle(summary,'::before');
        return gap>=6&&gap<=12&&section.classList.contains('is-pinned')&&
          heading.left-summary.getBoundingClientRect().left>=14&&Math.abs(parseFloat(mask.height)-gap)<2;
      },{id,width},{timeout:5000}).then(()=>true,()=>false);
      const label='Titre '+id+' accroché sous la navigation à '+width+' px';
      if(!stuck){
        const layout=await page.evaluate(({id,width})=>{
          const section=document.getElementById('collection-section-'+id);
          const summary=section.querySelector('summary');
          const nav=document.querySelector(width>760?'#main-navigation':'.topbar');
          return {open:section.open,hidden:section.hidden,scrollY,position:getComputedStyle(summary).position,
            section:section.getBoundingClientRect().toJSON(),pinned:section.classList.contains('is-pinned'),
            titleInset:summary.querySelector('h2').getBoundingClientRect().left-summary.getBoundingClientRect().left,
            summary:summary.getBoundingClientRect().top,nav:nav.getBoundingClientRect().bottom};
        },{id,width});
        throw Error(label+' : '+JSON.stringify(layout));
      }
      check(true,label+' avec marge intérieure et espace sous la navigation');
    }
  }
  await page.locator('#collection-section-videos > summary').click();
  await page.waitForFunction(()=>!document.querySelector('#collection-section-videos').classList.contains('is-pinned'));
  check(!await page.locator('#next-videos').isVisible(),'Un titre accroché permet toujours de replier la rubrique');
  await page.setViewportSize({width:1440,height:950});
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
