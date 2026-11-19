// Real profile settings, immutable translation task and portal; fake inference.
async page=>{
 const base='http://10.0.3.2:8769',headers={Origin:base},checks=[],errors=[],writes=[];
 const check=(ok,label)=>{if(!ok)throw Error(label);checks.push(label);};page.on('pageerror',e=>errors.push(e.message));
 page.on('request',r=>{if(r.method()==='POST'&&new URL(r.url()).pathname==='/api/translations')writes.push(r.url());});
 await page.request.post(base+'/api/profiles/select',{data:{id:'browser'},headers});
 await page.request.put(base+'/api/translation-terms',{data:{terms:[]},headers});
 await page.goto(base+'/#/assistant');await page.waitForFunction(()=>S.user&&S.authReady&&!S.loadingConversation);
 await page.locator('#chat-reset').click();await page.evaluate(()=>attachToConversation({id:'guide:shelter.en.txt',title:'Guide fictif'}));
 await page.locator('#translation-panel').evaluate(n=>n.open=true);await page.locator('#translation-terms > summary').click();
 await page.waitForFunction(()=>document.querySelector('#translation-terms-message').textContent.includes('Aucun mot imposé'));
 check(writes.length===0,'Ouvrir le vocabulaire ne lance pas de traduction');
 await page.getByRole('button',{name:'Ajouter un mot',exact:true}).click();
 const row=page.locator('.translation-term-row').first();await row.getByLabel('Dans le texte original').fill('Shelter');await row.getByLabel('En français').fill('Abri');
 await page.locator('#translation-start').click();check(writes.length===0,'Une préférence non enregistrée ne démarre pas silencieusement sans elle');
 check((await page.locator('#translation-terms-message').textContent()).includes('Enregistrez vos mots'),'La demande d’enregistrement est expliquée');
 await page.getByRole('button',{name:'Enregistrer ces mots',exact:true}).click();
 await page.waitForFunction(()=>document.querySelector('#translation-terms-message').textContent.includes('1 mot(s) enregistré'));
 await page.locator('#translation-start').click();await page.waitForFunction(()=>S.translation&&document.getElementById('translation-progress').value>=1);
 const id=await page.evaluate(()=>S.translation);await page.locator('#translation-pause').click();
 await page.waitForFunction(()=>document.querySelector('#translation-summary').textContent.includes('En pause'));
 let status=await(await page.request.get(base+'/api/translations/'+id)).json();const count=status.done;
 check(status.guidance.terms[0].french==='Abri'&&status.guidance.previous_context,'Le travail conserve ses choix et le repère de contexte');
 await row.getByLabel('En français').fill('Refuge');await page.getByRole('button',{name:'Enregistrer ces mots',exact:true}).click();
 await page.waitForFunction(()=>document.querySelector('#translation-terms-message').textContent.includes('1 mot(s) enregistré'));
 status=await(await page.request.get(base+'/api/translations/'+id)).json();check(status.guidance.terms[0].french==='Abri','Modifier les prochaines traductions ne modifie pas le travail en pause');
 await page.reload();await page.waitForFunction(()=>S.translation&&document.querySelector('#translation-summary').textContent.includes('En pause'));
 await page.locator('#translation-panel').evaluate(n=>n.open=true);await page.locator('#translation-terms').evaluate(n=>n.open=true);
 await page.waitForFunction(()=>document.querySelector('.translation-term-row input[data-term=french]')?.value==='Refuge');
 check(writes.length===1,'Rechargement conserve le vocabulaire sans reprendre le travail');
 check((await page.locator('#translation-terms-current').textContent()).includes('1 terme(s)'),'Le vocabulaire du travail est distingué des préférences futures');
 check((await page.locator('#translation-terms').innerText()).includes('Shelter → Abri'),'Les choix figés du travail restent visibles');
 await page.locator('#translation-resume').click();await page.waitForFunction(n=>document.querySelector('#translation-progress').value>n,count);
 await page.locator('#translation-stop').click();await page.waitForFunction(()=>document.querySelector('#translation-summary').textContent.includes('Arrêtée'));
 status=await(await page.request.get(base+'/api/translations/'+id)).json();
 check(status.parts.some(p=>p.quality?.guidance?.previous_position_proposed===0),'Les contrôles retracent le passage précédent proposé au modèle');
 for(const width of [1366,390,320]){await page.setViewportSize({width,height:844});check(await page.locator('#assistant-discussion #translation-terms').isVisible()&&!await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),'Éditeur lisible dans la discussion à '+width);}
 await page.locator('.translation-term-row').first().getByRole('button',{name:'Retirer ce mot',exact:true}).click();await page.getByRole('button',{name:'Enregistrer ces mots',exact:true}).click();
 await page.waitForFunction(()=>document.querySelector('#translation-terms-message').textContent.includes('0 mot(s) enregistré'));
 check((await(await page.request.get(base+'/api/translation-terms')).json()).terms.length===0,'Une liste vide rétablit le vocabulaire libre pour la suite');
 await page.request.delete(base+'/api/translations/'+id,{headers});
 check((await page.request.get(base+'/api/source?id=guide%3Ashelter.en.txt')).ok(),'Supprimer le travail conserve le document original');
 check(errors.length===0,'Aucune erreur JavaScript : '+errors.join(','));return {checks:checks.length,results:checks,real_inference:false};
}
