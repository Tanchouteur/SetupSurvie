async page=>{
 const base='http://10.0.3.2:8769',checks=[],errors=[];const check=(v,label)=>{if(!v)throw Error(label);checks.push(label);};page.on('pageerror',e=>errors.push(e.message));
 await page.setViewportSize({width:1366,height:950});await page.goto(base+'/#/bibliotheque/recherche?q=Shelter');await page.waitForSelector('#search-results .result button');await page.evaluate(()=>readSource('guide:shelter.en.pdf'));
 const before=page.url();await page.locator('#reader').getByRole('button',{name:/^(Traduire en français|Traduction : ouvrir ou reprendre)$/}).click();
 check(page.url()===before,'Traduction prépare sur place');check(await page.locator('#reader-work h3').evaluate(n=>n.getBoundingClientRect().top>=76),'Titre de traduction visible sous la navigation PC');await page.locator('#reader-work-choice').selectOption('');await page.locator('#reader-work').getByRole('button',{name:'Démarrer la traduction',exact:true}).click();
 await page.waitForFunction(()=>!!document.getElementById('reader-work-choice').value);const job=await page.locator('#reader-work-choice').inputValue();
 check(await page.evaluate(()=>!S.conversation),'Conversation courante préservée');
 await page.waitForFunction(()=>document.querySelector('#reader-work-parts .translation-part p')?.textContent.startsWith('Construction'));
 await page.locator('#reader-work').getByRole('button',{name:'Mettre en pause',exact:true}).click();await page.waitForFunction(()=>document.getElementById('reader-work-status').textContent.startsWith('En pause'));
 const compare=page.locator('#reader-work-parts details').first();await compare.locator('summary').click();check(await compare.evaluate(n=>n.open),'Comparer l’original pendant la lecture');
 const readingURL=page.url();await page.locator('#navigation [data-view=chat]').click();await page.goto(readingURL);await page.locator('#reader [data-document-action=translate]').click();await page.waitForFunction(()=>document.getElementById('reader-work-status').textContent.startsWith('En pause'));check(true,'Retrouver la traduction après une autre rubrique');
 await page.reload();await page.waitForFunction(()=>S.authReady&&S.user);await page.locator('#reader').getByRole('button',{name:'Traduction : ouvrir ou reprendre',exact:true}).click();
 await page.waitForFunction(()=>document.getElementById('reader-work-status').textContent.startsWith('En pause'));
 check(await page.locator('#reader-work-choice').inputValue()===job,'Travail retrouvé par original sans reprise automatique');
 for(const width of [320,390,1024,1440]){await page.setViewportSize({width,height:900});check(!await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),'Lecteur sans débordement '+width);}
 const pdf=await page.context().newPage();pdf.on('pageerror',e=>errors.push(e.message));await pdf.goto(base+'/pdf.html?id=guide%3Ashelter.en.pdf&interface=nouveau',{waitUntil:'domcontentloaded'});
 await pdf.getByRole('button',{name:'Traduire ce PDF',exact:true}).click();await pdf.waitForSelector('#reader-work:visible');
 check(await pdf.locator('#pdf-translation-work').isVisible(),'Traduction accessible dans le lecteur PDF dédié');
 await pdf.getByRole('button',{name:'Revenir au PDF',exact:true}).click();check(await pdf.locator('#pdf-container').isVisible(),'Retour au PDF sans changer de page');await pdf.close();
 check(!errors.length,'Aucune erreur JS : '+errors.join(','));return {checks:checks.length};
}
