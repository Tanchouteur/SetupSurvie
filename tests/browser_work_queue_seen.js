// « Marquer comme vu » for a finished item of the work queue, fixture API only.
async page=>{
 const base='http://10.0.3.2:8769',checks=[],errors=[],marks=[];
 const check=(ok,name)=>{if(!ok)throw Error(name);checks.push(name);};
 page.on('pageerror',e=>errors.push(e.message));
 let seen=false;
 const job=()=>({id:'archive-video-index',kind:'archive-video-index',type:'Examen des collections',title:'Inventaire des vidéos dans les collections',
   status:'partial',lane:'local',done:135,total:135,stage:'Toutes les collections ont été parcourues.',dismissible:true,signature:'0123456789abcdef',seen});
 await page.route('**/api/work-queue',route=>route.fulfill({json:{paused:false,running:false,lanes:{ai:{running:false,waiting:false},download:{running:false,waiting:false},local:{running:false,waiting:false}},jobs:[job()]}}));
 await page.route('**/api/work-queue/*/seen',route=>{marks.push(route.request().postDataJSON());seen=true;return route.fulfill({json:{accepted:true}});});
 await page.setViewportSize({width:1366,height:900});await page.goto(base+'/#/file');
 await page.waitForFunction(()=>typeof S!=='undefined'&&S.authReady);
 const card=page.locator('#work-queue-groups [data-work-id="archive-video-index"]');
 await card.waitFor();
 check(await page.locator('#work-queue-groups').textContent().then(t=>t.includes('Inventaires terminés')),'Élément terminé affiché dans À suivre');
 const action=card.getByRole('button',{name:/Marquer comme vu/});
 check(await action.count()===1,'Commande « Marquer comme vu » proposée');
 await action.click();
 await page.waitForFunction(()=>!document.querySelector('#work-queue-groups [data-work-id="archive-video-index"]'));
 check(marks.length===1&&marks[0].signature==='0123456789abcdef','Empreinte de l’état transmise au serveur');
 check(await page.locator('.work-queue-idle').isVisible(),'File vide affichée une fois l’élément vu');
 await page.getByRole('button',{name:'Historique récent'}).click();
 await page.locator('#work-queue-groups [data-work-id="archive-video-index"]').waitFor();
 check(await page.locator('#work-queue-groups [data-work-id="archive-video-index"] .work-queue-seen-label').isVisible(),'Élément vu conservé dans l’historique');
 check(errors.length===0,'Aucune erreur JavaScript : '+errors.join(','));
 return {checks:checks.length,results:checks};
}
