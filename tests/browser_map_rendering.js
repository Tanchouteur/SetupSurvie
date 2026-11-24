// Real PMTiles range reads + vector/raster rendering, entirely fictional data.
async page=>{
  const base='http://10.0.3.2:8766',archive=Buffer.from('__PMTILES_FIXTURE__','base64'),errors=[],outside=[],ranges=[];
  await page.unroute('**/*');page.on('pageerror',e=>errors.push(e.message));
  await page.route('**/*',async route=>{
    const req=route.request(),u=new URL(req.url());
    if(u.origin!==base){outside.push(req.url());return route.abort();}
    if(u.pathname==='/vendor/maps/maplibre-gl.js'){
      const response=await route.fetch();return route.fulfill({response,body:(await response.text())+`;(()=>{const Real=maplibregl.Map;maplibregl.Map=class extends Real{constructor(options){super(options);window.fixtureMap=this;window.styleLoads=0;this.on('style.load',()=>window.styleLoads++);}};})();`});
    }
    if(!u.pathname.startsWith('/api/'))return route.continue();
    if(u.pathname.endsWith('/archive')){
      const range=req.headers().range?.match(/bytes=(\d+)-(\d+)/);if(!range)throw Error('Range header absent');
      const start=Number(range[1]),end=Math.min(Number(range[2]),archive.length-1);ranges.push([start,end]);
      return route.fulfill({status:206,headers:{'Content-Range':`bytes ${start}-${end}/${archive.length}`,'Accept-Ranges':'bytes','Content-Type':'application/octet-stream'},body:archive.subarray(start,end+1)});
    }
    // Uniform translucent shade with a missing-data quadrant; no opaque DEM.
    if(u.pathname.startsWith('/api/geography/shade/'))return route.fulfill({contentType:'image/png',body:Buffer.from('__SHADE_FIXTURE__','base64')});
    const values={
      '/api/profiles/current':{id:'fixture',name:'Famille',role:'admin'},
      '/api/maps':{maps:[{id:'sollies',title:'Carte fictive de test',url:'/api/maps/test/archive',center:[6.1,43.1],bbox:[6,43,6.2,43.2],maxzoom:12,edition:'Fixture',attribution:'Fictional test · OpenStreetMap contributors · Protomaps · ODbL 1.0'}]},
      '/api/settings':{home:{lat:43.1,lon:6.1},departure:null},
      '/api/geography/status':{datasets:[{terrain:true}]},
      '/api/geography/elevation':{elevation_m:123},
      '/api/map-notebook':{lists:[],points:[],routes:[]},
      '/api/routing':{prepared:false,note:'Réseau fictif'}
    };return route.fulfill({json:values[u.pathname]||{}});
  });
  await page.setViewportSize({width:1440,height:900});await page.goto(base+'/cartes.html');
  await page.waitForFunction(()=>window.fixtureMap?.loaded()&&document.querySelector('#map').dataset.ready==='true');
  if(!await page.evaluate(()=>fixtureMap.queryRenderedFeatures({layers:['roads']}).length>0))throw Error('Routes vectorielles absentes');
  const initial=await page.evaluate(()=>styleLoads);
  await page.locator('[data-panel=map-layers]').click();await page.locator('#relief').click();await page.locator('#relief').click();
  await page.locator('#home').click();await page.waitForFunction(()=>!fixtureMap.isMoving());
  if(await page.evaluate(()=>styleLoads)!==initial)throw Error('Reconstruction inutile du style');
  await page.evaluate(()=>{SurvieMap.route({type:'LineString',coordinates:[[6.09,43.1],[6.11,43.11]]},[{geometry:{type:'LineString',coordinates:[[6.085,43.1],[6.09,43.1]]}}]);});
  await page.waitForFunction(()=>!fixtureMap.isMoving()&&fixtureMap.loaded());
  await page.locator('#relief').click();await page.locator('#relief').click();
  if(!await page.evaluate(()=>fixtureMap.getSource('route-connectors')._data.features.length===1&&fixtureMap.getSource('planned-route')._data.features.length===1))throw Error('Trajet perdu pendant le changement d’affichage');
  const printCheck=await page.evaluate(()=>{window.dispatchEvent(new Event('beforeprint'));const img=document.querySelector('.map-print-image');return {bytes:img.src.length,preserved:fixtureMap.getCanvas().getContext('webgl2')?.getContextAttributes().preserveDrawingBuffer};});
  if(printCheck.bytes<2000||printCheck.preserved===true)throw Error('Capture d’impression vide ou buffer préservé en permanence');
  await page.screenshot({path:'/artifacts/setupsurvie-cartes-rendu.png',fullPage:true});
  for(const [width,height] of [[1024,768],[390,844]]){
    await page.setViewportSize({width,height});
    if(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth))throw Error('Débordement '+width);
  }
  await page.setViewportSize({width:320,height:568});
  const attribution=page.locator('.maplibregl-ctrl-attrib-button');
  const tools=page.locator('#open-map-panel');
  const credits=page.locator('.maplibregl-ctrl-attrib.maplibregl-compact');
  await credits.waitFor();
  if(await credits.evaluate(el=>el.classList.contains('maplibregl-compact-show')))await attribution.click();
  await attribution.click();
  await credits.locator('.maplibregl-ctrl-attrib-inner').getByText('Fictional test',{exact:false}).waitFor();
  const creditsBox=await credits.boundingBox(), toolsBox=await tools.boundingBox();
  if(creditsBox.y+creditsBox.height>toolsBox.y)throw Error('Les outils chevauchent les crédits ouverts');
  const selectedBox=await page.locator('#selected-point-card').boundingBox();
  if(selectedBox.y+selectedBox.height>creditsBox.y)throw Error('Les crédits ouverts chevauchent la fiche du repère');
  await page.screenshot({path:'/artifacts/setupsurvie-cartes-mobile-credits.png',fullPage:true});
  await tools.click();
  await page.locator('#close-map-panel').waitFor({state:'visible'});
  if(!ranges.length||errors.length||outside.length)throw Error(JSON.stringify({ranges,errors,outside}));
  return {passed:true,real_pmtiles:true,range_requests:ranges.length,real_renderer:true,style_preserved:true,synthetic_data:true};
}
