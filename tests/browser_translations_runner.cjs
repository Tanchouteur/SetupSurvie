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
      const nextPage=await context.newPage();
      const nextRecipe=eval('('+fs.readFileSync(path.join(root,'tests/browser_next_portal.js'),'utf8').replaceAll('http://10.0.3.2:8769','http://127.0.0.1:8769')+')');
      const nextResult=await nextRecipe(nextPage);
      const nextTranslation=eval('('+fs.readFileSync(path.join(root,'tests/browser_translation.js'),'utf8').replaceAll('http://10.0.3.2:8769','http://127.0.0.1:8769')+')');
      const nextTranslationResult=await nextTranslation(nextPage);await nextPage.close();
      if(errors.length)throw Error(errors.join('\n'));
      console.log(JSON.stringify({engine:name,...result,sources:sourceResult,learning:learningResult,documents:documentsResult,quality:qualityResult,profiles:profileResult,next:nextResult,nextTranslation:nextTranslationResult}));
      await context.close();await browser.close();browser=null;
    }
  }finally{if(browser)await browser.close();server.kill();}
})().catch(error=>{console.error(error);process.exitCode=1;});
