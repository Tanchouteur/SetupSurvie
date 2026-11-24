// CI-only browser regression. All downloaded map data is synthetic.
const fs=require('node:fs');
const os=require('node:os');
const path=require('node:path');
const {createRequire}=require('node:module');
const {spawn}=require('node:child_process');
const {once}=require('node:events');
const {chromium,webkit}=createRequire('/tmp/setupsurvie-browser/package.json')('playwright');
const root=path.resolve(__dirname,'..');

async function startServer(port){
  const server=spawn('python',['-m','http.server',String(port),'--bind','127.0.0.1','--directory',path.join(root,'portal')],{stdio:'ignore'});
  for(let attempt=0;attempt<50;attempt++){
    try{if((await fetch(`http://127.0.0.1:${port}/cartes.html`)).ok)return server;}catch(_){}
    await new Promise(resolve=>setTimeout(resolve,100));
  }
  server.kill();
  throw Error(`Fixture server unavailable on port ${port}`);
}
async function stopServer(server){
  if(server.exitCode!==null||server.signalCode!==null)return;
  const exited=once(server,'exit');
  server.kill();
  await exited;
}
function loadRecipe(file,port){
  const source=fs.readFileSync(path.join(__dirname,file),'utf8')
    .replaceAll('http://10.0.3.2:8766',`http://127.0.0.1:${port}`)
    .replaceAll('/artifacts/','/tmp/maps-ui-')
    .replaceAll('__PMTILES_FIXTURE__',fs.readFileSync(path.join(root,'fixtures/maps/display-small.pmtiles')).toString('base64'))
    .replaceAll('__SHADE_FIXTURE__',fs.readFileSync(path.join(root,'fixtures/maps/shade-small.png')).toString('base64'));
  return eval('('+source+')');
}
async function runDownload(engine,name){
  const file='browser_map_download.js';
  const server=await startServer(8767);
  const profile=fs.mkdtempSync(path.join(os.tmpdir(),'ss-offline-map-'));
  let context;
  try{
    context=await engine.launchPersistentContext(profile,{headless:true});
    const result=await loadRecipe(file,8767)(context.pages()[0]||await context.newPage(),async()=>{
      await stopServer(server);
      await context.close();
      context=await engine.launchPersistentContext(profile,{headless:true});
      return context.pages()[0]||context.newPage();
    });
    console.log(JSON.stringify({engine:name,recipe:file,...result}));
  }finally{
    if(context)await context.close();
    await stopServer(server);
    fs.rmSync(profile,{recursive:true,force:true});
  }
}
(async()=>{
  const targetEngine=process.env.BROWSER_ENGINE;
  if(targetEngine&&!['chromium','webkit','firefox'].includes(targetEngine))throw Error(`Invalid BROWSER_ENGINE: ${targetEngine}`);
  if(targetEngine==='firefox')return;
  const server=await startServer(8766);
  try{
    for(const [name,engine] of [['chromium',chromium],['webkit',webkit]]){
      if(targetEngine&&name!==targetEngine)continue;
      const browser=await engine.launch({headless:true});
      try{
        for(const file of ['browser_map_redesign.js','browser_map_notebook.js','browser_map_defaults.js','browser_map_accesses.js','browser_map_rendering.js']){
          const context=await browser.newContext();
          const page=await context.newPage();
          const result=await loadRecipe(file,8766)(page);
          console.log(JSON.stringify({engine:name,recipe:file,...result}));
          await context.close();
        }
      }finally{await browser.close();}
      await runDownload(engine,name);
    }
  }finally{await stopServer(server);}
})().catch(error=>{console.error(error);process.exitCode=1;});
