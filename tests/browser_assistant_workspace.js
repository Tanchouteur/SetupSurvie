async page=>{
 const base='http://10.0.3.2:8769',checks=[],errors=[];
 const check=(ok,label)=>{if(!ok)throw Error(label);checks.push(label);};page.on('pageerror',e=>errors.push(e.message));
 await page.setViewportSize({width:1440,height:950});await page.goto(base+'/#/assistant');await page.waitForFunction(()=>S.authReady&&S.user);
 check(await page.locator('#assistant-history').isVisible()&&await page.locator('#assistant-documents').isVisible(),'Deux volets PC visibles');
 check(await page.locator('#chat-input').isVisible(),'Discussion et saisie au centre');
 await page.locator('#assistant-folder-create').click();await page.locator('#assistant-editor input').fill('Potager '+Date.now());await page.locator('#assistant-editor button[type=submit]').click();
 await page.waitForFunction(()=>document.querySelectorAll('.assistant-folder-row').length>0);
 check(true,'Dossier personnel créé depuis le volet');
 await page.locator('#chat-input').fill('Question fictive de classement');await page.locator('#chat-form').evaluate(n=>n.requestSubmit());await page.waitForFunction(()=>!!S.conversation&&!S.job);
 const id=await page.evaluate(()=>S.conversation);
 const row=page.locator('#conversation-list .conversation-row').filter({has:page.getByRole('button',{name:'Question fictive de classement',exact:true})});
 await row.locator('summary').click();await row.getByRole('button',{name:'Renommer',exact:true}).click();await page.locator('#assistant-editor input').fill('Mes semis');await page.locator('#assistant-editor button[type=submit]').click();
 await page.waitForFunction(()=>document.getElementById('conversation-list').textContent.includes('Mes semis'));
 check(await page.locator('#chat-title').innerText()==='Mes semis','Conversation renommée sans nouvel envoi');
 const renamed=page.locator('#conversation-list .conversation-row').filter({has:page.getByRole('button',{name:'Mes semis',exact:true})});await renamed.locator('summary').click();
 const folder=await renamed.locator('select option').last().getAttribute('value');await renamed.locator('select').selectOption(folder);
 await page.waitForTimeout(150);await page.reload();await page.waitForFunction(()=>S.authReady&&S.user&&!S.loadingConversation);
 const stored=await page.request.get(base+'/api/conversations?folder='+folder);check((await stored.json()).conversations.some(c=>c.id===id),'Classement conservé au rechargement');
 await page.locator('#assistant-history input[type=search]').fill('Mes semis');await page.waitForFunction(()=>document.querySelectorAll('#conversation-list .conversation-row').length===1);check(true,'Recherche dans les conversations');
 for(const width of [1024,1366,1920,390,320]){await page.setViewportSize({width,height:844});if(width<=1000){await page.locator('[data-assistant-zone="discussion"]').click();check(await page.locator('#assistant-discussion').isVisible()&&!await page.locator('#assistant-history').isVisible(),'Une zone à la fois sur téléphone '+width);await page.locator('[data-assistant-zone="documents"]').click();check(await page.locator('#assistant-documents').isVisible(),'Volet documentaire mobile '+width);}check(!await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),'Pas de débordement '+width);}
 check(!errors.length,'Aucune erreur JS : '+errors.join(','));return {checks:checks.length};
}
