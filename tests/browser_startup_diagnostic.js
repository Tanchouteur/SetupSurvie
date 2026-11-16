// Intercepted read-only observations; no engine command or model in this recipe.
async page=>{
 const base='http://10.0.3.2:8769',checks=[],errors=[],commands=[];
 const check=(ok,label)=>{if(!ok)throw Error(label);checks.push(label);};
 page.on('pageerror',error=>errors.push(error.message));
 page.on('request',request=>{if(request.method()!=='GET'&&request.url().includes('/api/'))commands.push(new URL(request.url()).pathname);});
 await page.request.post(base+'/api/profiles/select',{data:{id:'browser'},headers:{Origin:base}});
 const version=(await(await page.request.get(base+'/api/health')).json()).version;
 let exported=0;
 await page.route('**/api/admin/assistant/startup-report?*',route=>{exported++;return route.fulfill({json:{schema:1,kind:'SetupSurvie startup diagnostic',version,created:new Date().getTime()/1000,mode:'rapide',model:'fixture',context:32768,refused_attempts:[{action:'calibration',phase:'refused_before_start',http_status:409,observed:{controller:{online:false,operation:'start',last_engine_action:{status:'failed',stage:'waiting_for_api',elapsed_ms:45000}}}}],current:{controller:{online:true,memory:{available:6*1024**3}},ollama:{version:{state:'responding'}},model_loaded_by_this_check:false}}});});
 await page.goto(base+'/#/appareil/tests?test=memory');await page.waitForFunction(()=>S.user&&S.authReady&&document.getElementById('next-calibration-mode').options.length);
 check(exported===0,'Ouvrir les tests ne lance pas le diagnostic ni un modèle');
 const downloadEvent=page.waitForEvent('download');await page.locator('#next-startup-report-export').click();const download=await downloadEvent,chunks=[];for await(const chunk of await download.createReadStream())chunks.push(chunk);const report=JSON.parse(Buffer.concat(chunks).toString());
 check(exported===1&&report.refused_attempts[0].phase==='refused_before_start','Le rapport garde le refus qui précédait la création du test');
 check(report.current.controller.online&&!report.refused_attempts[0].observed.controller.online,'L’état actuel ne remplace pas l’état enregistré après le refus');
 check(!report.current.model_loaded_by_this_check&&commands.length===0,'Le contrôle n’envoie aucune commande de démarrage ou inférence');
 check(/^setupsurvie-demarrage-ia-v.+-\d{4}-\d{2}-\d{2}_\d{2}h\d{2}m\d{2}s\.json$/.test(download.suggestedFilename()),'Nom de diagnostic lisible avec version et heure');
 for(const width of [1366,390,320]){await page.setViewportSize({width,height:900});check(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'Commande de diagnostic adaptée à '+width);}
 check(errors.length===0,'Aucune erreur JavaScript : '+errors.join(','));
 return {checks:checks.length,results:checks,real_inference:false};
}
