// CI-only browser regression. No map, document, account or model is downloaded.
const fs=require('node:fs');
const path=require('node:path');
const {createRequire}=require('node:module');
const {spawn}=require('node:child_process');
const {chromium,webkit}=createRequire('/tmp/setupsurvie-browser/package.json')('playwright');
(async()=>{
  const root=path.resolve(__dirname,'..');
  const server=spawn('python',['-m','http.server','8766','--bind','127.0.0.1','--directory',path.join(root,'portal')],{stdio:'ignore'});
  let browser;
  try{
    for(let attempt=0;attempt<50;attempt++){try{if((await fetch('http://127.0.0.1:8766/cartes.html')).ok)break;}catch(_){}await new Promise(r=>setTimeout(r,100));}
    for(const [name,engine] of [['chromium',chromium],['webkit',webkit]]){
      browser=await engine.launch({headless:true});
      for(const file of ['browser_map_redesign.js','browser_map_notebook.js','browser_ux_preview.js','browser_map_defaults.js','browser_map_accesses.js','browser_map_rendering.js']){
        const context=await browser.newContext();const page=await context.newPage();
        const source=fs.readFileSync(path.join(__dirname,file),'utf8').replaceAll('http://10.0.3.2:8766','http://127.0.0.1:8766').replaceAll('/artifacts/','/tmp/maps-ui-').replaceAll('__PMTILES_FIXTURE__',fs.readFileSync(path.join(root,'fixtures/maps/display-small.pmtiles')).toString('base64')).replaceAll('__SHADE_FIXTURE__',fs.readFileSync(path.join(root,'fixtures/maps/shade-small.png')).toString('base64'));
        const recipe=eval('('+source+')');
        const result=await recipe(page);console.log(JSON.stringify({engine:name,recipe:file,...result}));
        await context.close();
      }
      await browser.close();browser=null;
    }
  }finally{if(browser)await browser.close();server.kill();}
})().catch(error=>{console.error(error);process.exitCode=1;});
