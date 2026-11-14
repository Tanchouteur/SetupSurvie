// Synthetic data, real MapLibre renderer. Every external request is blocked.
async page => {
  const base='http://10.0.3.2:8766',errors=[],external=[],checks=[];
  let failure='no_access',delay=false,requests=0;
  const list='a'.repeat(32),points=[{id:'b'.repeat(32),list_id:list,title:'Maison test',lat:43.1,lon:6.1},{id:'c'.repeat(32),list_id:list,title:'Source test',lat:43.11,lon:6.11}];
  const check=(ok,label)=>{if(!ok)throw Error(label);checks.push(label);};
  await page.unroute('**/*');
  page.on('pageerror',e=>errors.push(e.message));
  await page.route('**/*',async route=>{
    const req=route.request(),u=new URL(req.url()),path=u.pathname;
    if(u.origin!==base){external.push(req.url());return route.abort();}
    if(path==='/vendor/maps/maplibre-gl.js'){
      const response=await route.fetch();
      return route.fulfill({response,body:(await response.text())+`;(()=>{const Real=maplibregl.Map;maplibregl.Map=class extends Real{constructor(options){super(options);window.fixtureMap=this;window.fixtureStyleLoads=0;this.on('style.load',()=>window.fixtureStyleLoads++);}};})();`});
    }
    if(!path.startsWith('/api/'))return route.continue();
    let data={};
    if(path==='/api/profiles/current')data={id:'fixture',name:'Famille',role:'admin'};
    else if(path==='/api/maps')data={maps:[]};
    else if(path==='/api/geography/status')data={datasets:[]};
    else if(path==='/api/settings')data={home:null,departure:null};
    else if(path==='/api/geography/elevation')data={elevation_m:123};
    else if(path==='/api/map-notebook')data={lists:[{id:list,title:'Mes repères'}],points,routes:[]};
    else if(path==='/api/routing')data={prepared:true,note:'Réseau synthétique prêt'};
    else if(path==='/api/admin/map-notebook/accesses'){
      requests++;const p=req.postDataJSON();
      data={build_id:'fixture',candidates:[{lat:p.lat,lon:p.lon+.003,label:'Chemin du test',distance_m:244,token:'chosen-1'},{lat:p.lat+.002,lon:p.lon,label:'Autre accès',distance_m:222,token:'chosen-2'}]};
    }else if(path==='/api/admin/map-notebook/calculate'){
      const body=req.postDataJSON();if(delay)await new Promise(r=>setTimeout(r,500));
      if(failure==='engine_unavailable'||(failure&&!body.points[0].access_token))return route.fulfill({status:failure==='engine_unavailable'?503:422,json:{detail:{code:failure,message:failure==='engine_unavailable'?'Moteur local indisponible. Réessayez.':'Choisissez un accès proche.'}}});
      data={...body,draft_id:'d'.repeat(32),distance_m:2400,duration_s:2160,points:body.points.map((p,i)=>({...p,snapped_lat:p.lat,snapped_lon:p.lon+(i?0:.003),offset_m:i?0:244})),geometry:{type:'LineString',coordinates:[[6.103,43.1],[6.11,43.11]]},connectors:[{distance_m:244,geometry:{type:'LineString',coordinates:[[6.1,43.1],[6.103,43.1]]}}],segments:[],note:'Kilomètres sur les voies uniquement.'};
    }
    return route.fulfill({json:data});
  });
  await page.setViewportSize({width:1440,height:900});await page.goto(base+'/cartes.html');
  await page.waitForFunction(()=>window.SurvieMap&&document.body.dataset.mapRole==='admin');
  await page.locator('[data-panel=planning-panel]').click();
  await page.locator('#route-stops select').nth(0).selectOption(points[0].id);await page.locator('#route-stops select').nth(1).selectOption(points[1].id);
  check(!await page.locator('#route-speed').isVisible(),'Options secondaires repliées');
  await page.locator('#route-calculate').click();await page.locator('#access-candidates button').nth(1).waitFor();
  check(!await page.locator('#route-form').isVisible(),'Choix d’accès dans le panneau existant');
  check(!await page.locator('#route-save-form').isVisible(),'Aucun trajet enregistrable avant confirmation');
  check(await page.locator('#access-confirm').isDisabled(),'Confirmation explicite nécessaire');
  await page.locator('#access-candidates button').first().focus();await page.keyboard.press('Enter');
  check(await page.locator('#access-candidates button').first().getAttribute('aria-pressed')==='true','Choix au clavier');
  await page.waitForFunction(()=>!fixtureMap.isMoving());await page.screenshot({path:'/artifacts/setupsurvie-cartes-acces.png',fullPage:true});
  await page.locator('#access-confirm').click();await page.locator('#route-save-form').waitFor({state:'visible'});
  check((await page.locator('#selected-route-stops').textContent()).includes('liaison à vérifier'),'Distance de liaison distincte');
  await page.waitForFunction(()=>fixtureMap.getSource('route-connectors')?._data.features.length===1);check(true,'Raccordement représenté séparément');
  check(points[0].lon===6.1,'Point d’origine conservé');
  await page.locator('#route-review-access').click();await page.locator('#access-candidates button').nth(1).click();await page.locator('#access-candidates button').first().waitFor();
  await page.locator('#access-manual').click();
  await page.locator('#map').click({position:{x:300,y:300}});await page.locator('#access-candidates button').first().waitFor();
  check(await page.locator('#access-title').textContent()==='Choisir un accès pour Source test','Choix manuel pour la bonne étape');
  await page.locator('#access-cancel').click();
  check(await page.locator('#route-stops select').nth(0).inputValue()===points[0].id,'Annulation conserve les étapes');
  failure='engine_unavailable';const before=requests;
  await page.locator('#route-calculate').click();await page.waitForFunction(()=>document.querySelector('#planning-message').textContent.includes('Moteur local indisponible'));
  check(requests===before,'Une panne moteur ne cherche pas de faux accès');
  check(!await page.locator('#route-save-form').isVisible(),'Échec sans brouillon enregistrable');
  failure='no_route';await page.locator('#route-mode').selectOption('car');await page.locator('#route-calculate').click();
  await page.locator('#route-review-access').waitFor({state:'visible'});check(await page.locator('#route-form').isVisible(),'Absence de liaison conserve le formulaire');
  await page.locator('#route-mode').selectOption('foot');failure=null;delay=true;
  await page.locator('#route-calculate').click();await page.locator('#route-mode').selectOption('car');await page.waitForFunction(()=>!document.querySelector('#route-calculate').disabled);
  check(!await page.locator('#route-save-form').isVisible(),'Réponse périmée ignorée');
  await page.setViewportSize({width:1024,height:768});
  check(!await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),'Panneau sans débordement à 1024 px');
  check(errors.length===0,'Aucune erreur JavaScript : '+errors.join(','));check(external.length===0,'Aucune requête extérieure');
  return {passed:true,checks,real_renderer:true,routing_simulated:true};
}
