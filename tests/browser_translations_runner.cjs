// Browser regression against the local CPU fixture API, never a real model/account.
const fs=require('node:fs');
const path=require('node:path');
const {createRequire}=require('node:module');
const {spawn}=require('node:child_process');
const {chromium,webkit}=createRequire('/tmp/setupsurvie-browser/package.json')('playwright');
(async()=>{
  const root=path.resolve(__dirname,'..');
  const server=spawn('python',['tests/browser_translation_server.py'],{cwd:root,stdio:['ignore','ignore','inherit']});
  let browser;
  try{
    let ready=false;
    for(let n=0;n<100;n++){
      if(server.exitCode!==null)throw Error('Fixture server exited');
      try{if((await fetch('http://127.0.0.1:8769/api/health')).ok){ready=true;break;}}catch(_){}
      await new Promise(r=>setTimeout(r,100));
    }
    if(!ready)throw Error('Fixture API unavailable');
    const source=fs.readFileSync(path.join(root,'tests/browser_translation.js'),'utf8').replaceAll('http://10.0.3.2:8769','http://127.0.0.1:8769').replaceAll('.goto(base)',".goto(base+'/classique/')").replaceAll("base+'/index.html#library'","base+'/classique/index.html#library'");
    const recipe=eval('('+source+')');
    for(const [name,engine] of [['chromium',chromium],['webkit',webkit]]){
      browser=await engine.launch({headless:true});
      const context=await browser.newContext();const page=await context.newPage();
      const errors=[];page.on('pageerror',error=>errors.push(String(error)));
      const result=await recipe(page);
      const sourceRecipe=eval('('+fs.readFileSync(path.join(root,'tests/browser_sources.js'),'utf8').replaceAll('http://10.0.3.2:8769','http://127.0.0.1:8769').replaceAll('.goto(base)',".goto(base+'/classique/')").replaceAll("base+'/index.html#library'","base+'/classique/index.html#library'")+')');
      const sourceResult=await sourceRecipe(page);
      const learningRecipe=eval('('+fs.readFileSync(path.join(root,'tests/browser_learning.js'),'utf8').replaceAll('http://10.0.3.2:8769','http://127.0.0.1:8769').replaceAll('.goto(base)',".goto(base+'/classique/')").replaceAll("base+'/index.html#library'","base+'/classique/index.html#library'")+')');
      const learningResult=await learningRecipe(page);
      const documentsRecipe=eval('('+fs.readFileSync(path.join(root,'tests/browser_documents.js'),'utf8').replaceAll('http://10.0.3.2:8769','http://127.0.0.1:8769').replaceAll('.goto(base)',".goto(base+'/classique/')").replaceAll("base+'/index.html#library'","base+'/classique/index.html#library'")+')');
      const documentsResult=await documentsRecipe(page);
      const qualityRecipe=eval('('+fs.readFileSync(path.join(root,'tests/browser_translation_quality.js'),'utf8').replaceAll('http://10.0.3.2:8769','http://127.0.0.1:8769').replaceAll('.goto(base)',".goto(base+'/classique/')").replaceAll("base+'/index.html#library'","base+'/classique/index.html#library'")+')');
      const qualityResult=await qualityRecipe(page);
      const profileRecipe=eval('('+fs.readFileSync(path.join(root,'tests/browser_profiles.js'),'utf8').replaceAll('http://10.0.3.2:8769','http://127.0.0.1:8769').replaceAll('.goto(base)',".goto(base+'/classique/')").replaceAll("base+'/index.html#library'","base+'/classique/index.html#library'")+')');
      const profileResult=await profileRecipe(page);
      const filterPage=await context.newPage();
      const filterRecipe=eval('('+fs.readFileSync(path.join(root,'tests/browser_collection_filter.js'),'utf8').replaceAll('http://10.0.3.2:8769','http://127.0.0.1:8769')+')');
      const filterResult=await filterRecipe(filterPage);await filterPage.close();
      const comfortPage=await context.newPage();
      const comfortRecipe=eval('('+fs.readFileSync(path.join(root,'tests/browser_chat_comfort.js'),'utf8').replaceAll('http://10.0.3.2:8769','http://127.0.0.1:8769').replaceAll('/artifacts/','/tmp/chat-comfort-')+')');
      const comfortResult=await comfortRecipe(comfortPage);await comfortPage.close();
      const searchPage=await context.newPage();
      const searchRecipe=eval('('+fs.readFileSync(path.join(root,'tests/browser_search_core.js'),'utf8').replaceAll('http://10.0.3.2:8769','http://127.0.0.1:8769').replaceAll('/artifacts/','/tmp/search-core-')+')');
      const searchResult=await searchRecipe(searchPage);await searchPage.close();
      const toolsPage=await context.newPage();
      const toolsRecipe=eval('('+fs.readFileSync(path.join(root,'tests/browser_search_tools.js'),'utf8').replaceAll('http://10.0.3.2:8769','http://127.0.0.1:8769')+')');
      const toolsResult=await toolsRecipe(toolsPage);await toolsPage.close();
      const cataloguePage=await context.newPage();
      const catalogueRecipe=eval('('+fs.readFileSync(path.join(root,'tests/browser_catalogue.js'),'utf8').replaceAll('http://10.0.3.2:8769','http://127.0.0.1:8769')+')');
      const catalogueResult=await catalogueRecipe(cataloguePage);await cataloguePage.close();
      const diagnosticPage=await context.newPage();
      const diagnosticRecipe=eval('('+fs.readFileSync(path.join(root,'tests/browser_assistant_diagnostics.js'),'utf8').replaceAll('http://10.0.3.2:8769','http://127.0.0.1:8769')+')');
      const diagnosticResult=await diagnosticRecipe(diagnosticPage);await diagnosticPage.close();
      const experimentPage=await context.newPage();
      const experimentRecipe=eval('('+fs.readFileSync(path.join(root,'tests/browser_search_experiment.js'),'utf8').replaceAll('http://10.0.3.2:8769','http://127.0.0.1:8769')+')');
      const experimentResult=await experimentRecipe(experimentPage);await experimentPage.close();
      const practicalPage=await context.newPage();
      const practicalRecipe=eval('('+fs.readFileSync(path.join(root,'tests/browser_practical.js'),'utf8').replaceAll('http://10.0.3.2:8769','http://127.0.0.1:8769')+')');
      const practicalResult=await practicalRecipe(practicalPage);await practicalPage.close();
      const usagePage=await context.newPage();
      const usageRecipe=eval('('+fs.readFileSync(path.join(root,'tests/browser_usage_recipe.js'),'utf8').replaceAll('http://10.0.3.2:8769','http://127.0.0.1:8769').replaceAll('/artifacts/','/tmp/usage-recipe-')+')');
      const usageResult=await usageRecipe(usagePage);await usagePage.close();
      const nextPage=await context.newPage();
      const nextRecipe=eval('('+fs.readFileSync(path.join(root,'tests/browser_next_portal.js'),'utf8').replaceAll('http://10.0.3.2:8769','http://127.0.0.1:8769')+')');
      const nextResult=await nextRecipe(nextPage);
      const nextTranslation=eval('('+fs.readFileSync(path.join(root,'tests/browser_translation.js'),'utf8').replaceAll('http://10.0.3.2:8769','http://127.0.0.1:8769')+')');
      const nextTranslationResult=await nextTranslation(nextPage);await nextPage.close();
      if(errors.length)throw Error(errors.join('\n'));
      console.log(JSON.stringify({engine:name,...result,sources:sourceResult,learning:learningResult,documents:documentsResult,quality:qualityResult,profiles:profileResult,collections:filterResult,chatComfort:comfortResult,searchCore:searchResult,searchTools:toolsResult,catalogue:catalogueResult,assistantDiagnostics:diagnosticResult,searchExperiment:experimentResult,practical:practicalResult,usage:usageResult,next:nextResult,nextTranslation:nextTranslationResult}));
      await context.close();await browser.close();browser=null;
    }
  }finally{if(browser)await browser.close();server.kill();}
})().catch(error=>{console.error(error);process.exitCode=1;});
