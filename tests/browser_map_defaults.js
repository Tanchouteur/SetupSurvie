// Local synthetic terrain tile only. No basemap/corpus/model or Internet request.
async page => {
  const base='http://10.0.3.2:8766',checks=[],errors=[],outside=[];let terrain=true,tileRequests=0,mutations=0;
  const png='iVBORw0KGgoAAAANSUhEUgAAAQAAAAEACAYAAABccqhmAAADHElEQVR4nO3UoQEAIADDsJ3O53AGohHxVd3ZLtC03wHAPwYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQYAYQ9QmxZywEi7rgAAAABJRU5ErkJggg==';
  const check=(value,label)=>{if(!value)throw Error(label);checks.push(label);};
  page.on('pageerror',e=>errors.push(e.message));
  await page.route('**/*',async route=>{
    const r=route.request(),u=new URL(r.url());
    if(u.origin!==base){outside.push(r.url());return route.abort();}
    if(!u.pathname.startsWith('/api/'))return route.continue();
    if(r.method()!=='GET')mutations++;
    if(u.pathname.startsWith('/api/geography/terrain/')){tileRequests++;return route.fulfill({contentType:'image/png',body:Buffer.from(png,'base64')});}
    const values={
      '/api/profiles/current':{id:'fixture',name:'Famille',role:'admin'},
      '/api/maps':{maps:[]},
      '/api/settings':{home:null,departure:null},
      '/api/geography/status':{datasets:terrain?[{terrain:true}]:[]},
      '/api/map-notebook':{lists:[],points:[],routes:[]},
      '/api/routing':{prepared:false,note:'Réseau non préparé'}
    };
    return route.fulfill({json:values[u.pathname]||{}});
  });
  await page.setViewportSize({width:1440,height:900});
  await page.goto(base+'/cartes.html?interface=nouveau');await page.waitForFunction(()=>window.SurvieMap);
  check(await page.locator('#relief').getAttribute('aria-pressed')==='true','Relief activé dès l’ouverture si disponible');
  await page.waitForFunction(()=>document.querySelector('#map').dataset.ready==='true');
  check(tileRequests>0,'La couche relief demande seulement les tuiles locales');
  const back=new URL(await page.locator('.back-link').getAttribute('href'),base);
  check(back.hash==='#/accueil','Retour à l’accueil sans boucle vers la carte');
  await page.locator('[data-panel="map-layers"]').click();
  await page.locator('#relief').click();
  check(await page.locator('#relief').getAttribute('aria-pressed')==='false','Relief masquable manuellement');
  await page.locator('#relief').click();
  check(await page.locator('#relief').getAttribute('aria-pressed')==='true','Relief réactivable manuellement');
  // Finish the previous document before counting requests for the no-terrain case.
  // Re-enabling hillshade may still have queued tile requests when reload starts.
  await page.goto('about:blank');terrain=false;tileRequests=0;
  await page.goto(base+'/cartes.html?interface=nouveau');await page.waitForFunction(()=>window.SurvieMap);
  await page.waitForFunction(()=>document.querySelector('#map').dataset.ready==='true');
  check(await page.locator('#relief').getAttribute('aria-pressed')==='false','Sans altitudes la carte reste sans faux relief');
  check((await page.locator('#relief-help').textContent()).includes('Aucune altitude'),'Altitudes absentes expliquées');
  check(tileRequests===0,'Aucune tuile relief demandée quand les altitudes manquent');
  await page.setViewportSize({width:390,height:844});
  check(await page.locator('#map').isVisible(),'Carte conservée sur téléphone sans relief disponible');
  check(!await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),'Pas de débordement mobile');
  check(mutations===0&&outside.length===0,'Aucun téléchargement/préparation automatique ni requête Internet');
  check(errors.length===0,'Aucune erreur JavaScript : '+errors.join(','));
  return {checks:checks.length,results:checks};
}
