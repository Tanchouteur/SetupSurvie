// A tiny fixture API must already be running. No production service or model used.
const fs=require('node:fs'),path=require('node:path');
const {chromium,webkit,firefox}=require('playwright');
const base=process.env.UX_BASE||'http://127.0.0.1:8782',out=process.env.UX_ARTIFACTS||'/tmp/setupsurvie-settings-artifacts';
(async()=>{
 fs.mkdirSync(out,{recursive:true});const results={};
 for(const [name,engine] of [['chromium',chromium],['webkit',webkit],...(process.env.UX_ENGINE==='firefox'?[['firefox',firefox]]:[])]){
  if(process.env.UX_ENGINE&&name!==process.env.UX_ENGINE)continue;
  const browser=await engine.launch({headless:true});
  try{
   results[name]={};
   for(const file of ['browser_ui_finish.js','browser_assistant_workspace.js','browser_reader_work.js','browser_ux_foundations.js','browser_settings_ux.js','browser_next_portal.js','browser_search_core.js','browser_search_tools.js','browser_catalogue.js','browser_assistant_diagnostics.js','browser_search_experiment.js','browser_practical.js','browser_usage_recipe.js']){
    if(process.env.UX_RECIPE&&file!==process.env.UX_RECIPE)continue;
    const context=await browser.newContext();const page=await context.newPage();page.setDefaultTimeout(30000);
    const recipe=eval('('+fs.readFileSync(path.join(__dirname,file),'utf8').replaceAll('http://10.0.3.2:8769',base).replaceAll('/artifacts/',out+'/')+')');
    try{results[name][file]=await recipe(page);console.log(name,file,results[name][file].checks,'checks');}
    catch(error){console.error('Fixture failure',page.url(),await page.evaluate(()=>({user:typeof S==='undefined'?null:S.user?.id,view:typeof S==='undefined'?null:S.view,profileDialog:document.querySelector('#auth-dialog')?.open})).catch(()=>null));await page.screenshot({path:path.join(out,name+'-'+file+'-failure.png'),fullPage:true});throw error;}
    finally{await context.close();fs.writeFileSync(path.join(out,'results.json'),JSON.stringify(results,null,2));}
   }
   const page=await browser.newPage();
   for(const [size,width,height] of [['ordinateur',1440,950],['mobile',390,844]]){
    await page.setViewportSize({width,height});await page.goto(base+'/#/appareil/reglages');await page.waitForFunction(()=>S.authReady&&S.user);
    await page.screenshot({path:path.join(out,'parametres-apres-'+name+'-'+size+'.png'),fullPage:true});
   }
  }finally{await browser.close();}
 }
})().catch(error=>{console.error(error);process.exitCode=1;});
