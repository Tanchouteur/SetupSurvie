// Real tiny API fixture, no password or real model.
async page => {
  const base='http://10.0.3.2:8769';
  await page.setViewportSize({width:1366,height:900});
  await page.unrouteAll({behavior:'wait'});await page.goto('about:blank');await page.context().clearCookies();
  // Simulate the TLS proxy response before loading the portal, then use HTTP.
  await page.request.post(base+'/api/profiles/select',{data:{id:'browser'},headers:{Origin:base,'X-Forwarded-Proto':'https'}});
  await page.goto(base+'/#/bibliotheque/recherche');await page.waitForFunction(()=>typeof S!=='undefined'&&S.user?.id==='browser');
  await page.locator('#account-button').click();await page.getByRole('button',{name:'Famille',exact:true}).click();await page.waitForFunction(()=>typeof S!=='undefined'&&S.user?.id==='local-family');
  if(await page.locator('input[type=password]').count())throw Error('Password field remains in portal');
  const layouts=[];
  // The retired classic sidebar is gone; check the single portal at each size instead.
  for(const [width,height] of [[1440,900],[1024,768],[900,500],[390,844],[320,568]]){
    await page.setViewportSize({width,height});
    if(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth))throw Error('Page overflow at '+width);
    layouts.push({width,height,noHorizontalOverflow:true});
  }
  await page.setViewportSize({width:1366,height:900});
  await page.locator('#account-button').click();await page.locator('#profile-create-form [name=name]').fill('Profil essai '+Date.now());
  const chosen=await page.locator('#profile-create-form [name=name]').inputValue();await page.locator('#profile-create-form button').click();
  await page.waitForFunction(name=>typeof S!=='undefined'&&S.user?.name===name,chosen);const id=await page.evaluate(()=>typeof S!=='undefined'&&S.user.id);
  const favorite=await page.request.put(base+'/api/favorites',{data:{source_id:'guide:craft.en.txt'},headers:{Origin:base}});if(!favorite.ok())throw Error(await favorite.text());
  await page.request.post(base+'/api/questions',{data:{message:'Mémo du profil'},headers:{Origin:base}});
  await page.locator('#account-button').click();await page.getByRole('button',{name:'Famille',exact:true}).click();await page.waitForFunction(()=>typeof S!=='undefined'&&S.user?.id==='local-family');
  if((await(await page.request.get(base+'/api/favorites')).json()).results.some(r=>r.id==='guide:craft.en.txt'))throw Error('Favorite leaked into family');
  await page.locator('#account-button').click();await page.getByRole('button',{name:chosen,exact:true}).click();await page.waitForFunction(id=>typeof S!=='undefined'&&S.user?.id===id,id);
  if(!(await(await page.request.get(base+'/api/favorites')).json()).results.some(r=>r.id==='guide:craft.en.txt'))throw Error('Favorite lost');
  if(!(await(await page.request.get(base+'/api/conversations')).json()).conversations.some(c=>c.title==='Mémo du profil'))throw Error('History lost');
  const other=await page.context().newPage();await other.goto(base+'/#/bibliotheque/recherche');await other.waitForFunction(id=>typeof S!=='undefined'&&S.user?.id===id,id);
  await page.locator('#account-button').click();await page.getByRole('button',{name:'Famille',exact:true}).click();await page.waitForFunction(()=>typeof S!=='undefined'&&S.user?.id==='local-family');
  await other.bringToFront();
  try{await other.waitForFunction(()=>typeof S!=='undefined'&&S.user?.id==='local-family');}
  catch(error){
    const state=await other.evaluate(async()=>({user:S.user,reloading:S.profileReloading,hidden:document.hidden,focus:document.hasFocus(),visibility:document.visibilityState,current:await(await fetch('/api/profiles/current')).json(),storage:localStorage.getItem('survie.profile.changed')}));
    throw Error('Secondary profile tab: '+JSON.stringify(state)+' cookies='+JSON.stringify((await page.context().cookies()).filter(c=>c.name==='survie_profile')));
  }
  const stale=await page.request.put(base+'/api/favorites',{data:{source_id:'guide:craft.en.txt'},headers:{Origin:base,'X-Survie-Profile':id}});
  if(stale.status()!==409)throw Error('Stale tab can change another profile');
  await other.close();
  if(await page.locator('#feedback-button').isVisible())throw Error('Feedback button reintroduced');
  if(await page.locator('input[type=password]').count())throw Error('Password field remains');
  return {httpAndHttpsChoice:true,noPassword:true,profileCreatedAndRestored:true,favoritesAndHistoryPreserved:true,tabsSynchronized:true,staleWriteBlocked:true,feedbackHidden:true,layouts};
}
