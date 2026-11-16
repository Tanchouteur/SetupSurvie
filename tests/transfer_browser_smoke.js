// Tests the exported human guide as a local file, with no network dependency.
const {chromium, webkit}=require('/opt/transfer-test/node_modules/playwright');
const {execFileSync}=require('node:child_process');
execFileSync('python3',['-c',"import sys;from pathlib import Path;sys.path.insert(0,'scripts');import transfer;root=Path('/tmp/transfer-guide');root.mkdir();transfer.export_report(root,{'phase':'copied','inventory':{'files':[]}})"]);
(async()=>{
  for (const [name,engine] of [['chromium',chromium],['webkit',webkit]]) {
    const browser=await engine.launch({headless:true});
    for(const width of [390,1280]) {
      const page=await browser.newPage({viewport:{width,height:800}});
      const network=[];page.on('request',r=>{if(/^https?:/.test(r.url()))network.push(r.url())});
      await page.goto('file:///tmp/transfer-guide/LISEZ-MOI.html');
      const text=await page.locator('body').innerText();
      if(!text.includes('Marc : du HDD au SSD de 2 To')||!text.includes('Revenir au HDD'))throw Error('Missing guide');
      if(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth))throw Error(name+' overflow at '+width);
      if(network.length)throw Error('External requests');
      console.log(name+' '+width+': local guide readable, no overflow, zero HTTP requests');
      await page.close();
    }
    await browser.close();
  }
})().catch(e=>{console.error(e);process.exit(1)});
