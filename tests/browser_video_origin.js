// An inventory stays active while the filtered catalogue is slow.
async page=>{
  const base='http://10.0.3.2:8769',checks=[];
  const check=(ok,label)=>{if(!ok)throw Error(label);checks.push(label);};
  let youtubeRequests=0,releaseYoutube;
  const slowYoutube=new Promise(resolve=>{releaseYoutube=resolve;});
  let holdOther=true,releaseOther,otherStarted;
  const slowOther=new Promise(resolve=>{releaseOther=resolve;});
  const otherRequest=new Promise(resolve=>{otherStarted=resolve;});
  await page.request.post(base+'/api/profiles/select',{data:{id:'browser'},headers:{Origin:base}});
  await page.route(/\/api\/videos\?/,async route=>{
    const origin=new URL(route.request().url()).searchParams.get('origin');
    if(origin==='youtube'){youtubeRequests++;await slowYoutube;}
    if(origin==='non_youtube'&&holdOther){otherStarted();await slowOther;return;}
    const groups=origin==='youtube'?[{id:'local:chaîne fictive',name:'Chaîne fictive',count:2}]:[];
    const data={status:{phase:origin==='all'?'running':'completed'},total:groups.length*2,group_total:groups.length,groups};
    await route.fulfill({json:data});
  });
  await page.clock.install();
  try{
    await page.goto(base+'/#/bibliotheque/collections');
    const feedback=page.locator('#next-videos-feedback'),origin=page.getByLabel('Origine des vidéos');
    await page.getByRole('link',{name:'Vidéos',exact:true}).click();
    await page.waitForFunction(()=>document.querySelector('#next-videos-feedback').textContent==='Inventaire en cours…');
    const requested=page.waitForRequest(/\/api\/videos\?.*origin=youtube/);
    await origin.selectOption('youtube');
    await requested;
    await page.clock.runFor(3200);
    releaseYoutube();
    check(youtubeRequests===1,'Le suivi de l’inventaire laisse aboutir la requête YouTube');
    await page.locator('#next-videos-list').getByText('Chaîne fictive').waitFor({timeout:5000});
    check(await page.locator('#next-videos-count').textContent()==='2 vidéos','Le filtre affiche le résultat lent');

    await origin.selectOption('non_youtube');
    await otherRequest;
    await page.clock.fastForward(21000);
    const retry=page.getByRole('button',{name:'Réessayer',exact:true});
    await retry.waitFor({timeout:5000});
    check((await feedback.textContent()).includes('met trop de temps'),'Le délai dépassé est expliqué');
    holdOther=false;
    await retry.click();
    await page.waitForFunction(()=>document.querySelector('#next-videos-count').textContent.includes('Aucune vidéo'));
    check(!await retry.isVisible(),'Le filtre peut être relancé après expiration');
  }finally{releaseYoutube();releaseOther();}
  return {checks:checks.length,results:checks};
}
