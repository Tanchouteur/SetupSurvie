async page=>{
 const base='http://10.0.3.2:8769',checks=[],errors=[];const check=(v,label)=>{if(!v)throw Error(label);checks.push(label);};page.on('pageerror',e=>errors.push(e.message));
 // Other recipes deliberately leave resumable jobs. This scenario needs its
 // own profile; a legitimate one-active-translation refusal is not a UI timeout.
 const profileResponse=await page.request.post(base+'/api/profiles',{data:{name:'Recette lecteur de traduction'},headers:{Origin:base}});
 check(profileResponse.ok(),'Profil de recette isolé des traductions des autres scénarios');
 await page.setViewportSize({width:1366,height:950});await page.goto(base+'/#/bibliotheque/recherche?q=Shelter');await page.waitForSelector('#search-results .result button');await page.evaluate(()=>readSource('guide:shelter.en.pdf'));
 const before=page.url();await page.locator('#reader').getByRole('button',{name:/^(Traduire en français|Traduction : ouvrir ou reprendre)$/}).click();
 check(page.url()===before,'Traduction prépare sur place');check(await page.locator('#reader-work h3').evaluate(n=>n.getBoundingClientRect().top>=76),'Titre de traduction visible sous la navigation PC');await page.locator('#reader-work-choice').selectOption('');await page.locator('#reader-work').getByRole('button',{name:'Démarrer la traduction',exact:true}).click();
 try{await page.waitForFunction(()=>!!document.getElementById('reader-work-choice').value);}
 catch(error){throw Error('Lancement traduction lecteur : '+JSON.stringify(await page.evaluate(()=>({profile:S.user?.id,authReady:S.authReady,reader:S.reader,status:document.getElementById('reader-work-status')?.textContent,choice:document.getElementById('reader-work-choice')?.value})))+' ; '+error.message);}
 const job=await page.locator('#reader-work-choice').inputValue();
 check(await page.evaluate(()=>!S.conversation),'Conversation courante préservée');
 await page.waitForFunction(()=>document.querySelector('#reader-work-parts .translation-part p')?.textContent.startsWith('Construction'));
 await page.locator('#reader-work').getByRole('button',{name:'Mettre en pause',exact:true}).click();await page.waitForFunction(()=>document.getElementById('reader-work-status').textContent.startsWith('En pause'));
 const compare=page.locator('#reader-work-parts details').first();await compare.locator('summary').click();check(await compare.evaluate(n=>n.open),'Comparer l’original pendant la lecture');
 const readingURL=page.url();await page.locator('#navigation [data-route=assistant]').click();await page.goto(readingURL);await page.locator('#reader [data-document-action=translate]').click();await page.waitForFunction(()=>document.getElementById('reader-work-status').textContent.startsWith('En pause'));check(true,'Retrouver la traduction après une autre rubrique');
 await page.reload();await page.waitForFunction(()=>S.authReady&&S.user);await page.locator('#reader').getByRole('button',{name:'Traduction : ouvrir ou reprendre',exact:true}).click();
 await page.waitForFunction(()=>document.getElementById('reader-work-status').textContent.startsWith('En pause'));
 check(await page.locator('#reader-work-choice').inputValue()===job,'Travail retrouvé par original sans reprise automatique');
 for(const width of [320,390,1024,1440]){await page.setViewportSize({width,height:900});check(!await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),'Lecteur sans débordement '+width);}
 const pdf=await page.context().newPage();pdf.on('pageerror',e=>errors.push(e.message));
 // Keep initialization pending and count only the reader's explicit-profile
 // checks. A focus must not compare that not-yet-loaded profile to undefined.
 await pdf.addInitScript(()=>{const fetch=window.fetch;window.readerProfileReads=0;window.fetch=(input,options)=>{if(String(input).includes('/profiles/current')&&options?.headers)window.readerProfileReads++;return fetch(input,options);};});
 let releaseStatus;const heldStatus=new Promise(resolve=>{releaseStatus=resolve;});
 await pdf.route('**/api/status',async route=>{await heldStatus;await route.continue();});
 await pdf.goto(base+'/pdf.html?id=guide%3Ashelter.en.pdf',{waitUntil:'domcontentloaded'});
 await pdf.getByRole('button',{name:'Traduire ce PDF',exact:true}).waitFor();
 const premature=await pdf.evaluate(()=>{const before=window.readerProfileReads;window.dispatchEvent(new Event('focus'));return window.readerProfileReads-before;});
 releaseStatus();check(premature===0,'Le focus pendant le chargement attend le profil avant de le comparer');
 await pdf.getByRole('button',{name:'Traduire ce PDF',exact:true}).click();await pdf.waitForSelector('#reader-work:visible');
 check(await pdf.locator('#pdf-translation-work').isVisible(),'Traduction accessible dans le lecteur PDF dédié');
 await pdf.getByRole('button',{name:'Revenir au PDF',exact:true}).click();check(await pdf.locator('#pdf-container').isVisible(),'Retour au PDF sans changer de page');
 const profile=await(await pdf.request.get(base+'/api/profiles/current',{maxRetries:1})).json();
 await pdf.request.post(base+'/api/profiles/select',{data:{id:profile.id==='browser'?'local-family':'browser'},headers:{Origin:base}});
 await pdf.evaluate(()=>window.dispatchEvent(new Event('focus')));
 await pdf.getByRole('button',{name:'Profil modifié : rechargez le lecteur',exact:true}).waitFor();
 check(await pdf.getByRole('button',{name:'Profil modifié : rechargez le lecteur',exact:true}).isDisabled(),'Un vrai changement de profil après chargement reste bloqué dans le lecteur PDF');
 await pdf.close();
 check(!errors.length,'Aucune erreur JS : '+errors.join(','));return {checks:checks.length};
}
