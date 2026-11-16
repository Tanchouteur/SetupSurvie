// Hold the native worker handshake, while importing the real pinned PDF library.
async page=>{
 const base='http://10.0.3.2:8769',checks=[],errors=[];
 const check=(ok,label)=>{if(!ok)throw Error(label);checks.push(label);};
 page.on('pageerror',error=>errors.push(error.message));
 await page.addInitScript(()=>{window.testWorkerPorts=[];window.Worker=class extends EventTarget{constructor(url){super();this.url=String(url);this.terminated=false;testWorkerPorts.push(this);}postMessage(){}terminate(){this.terminated=true;}};});
 await page.request.post(base+'/fixture/figures?enabled=true',{headers:{Origin:base}});
 try{
  await page.request.post(base+'/api/profiles/select',{data:{id:'browser'},headers:{Origin:base}});
  await page.goto(base+'/#/assistant');await page.waitForFunction(()=>S.user&&!S.loadingConversation);await page.locator('#chat-reset').click();
  await page.locator('#chat-input').fill('Montre les schémas fixture du montage.');await page.locator('#send-question').click();
  await page.waitForFunction(()=>document.querySelectorAll('.source-figure').length===2);await page.locator('.source-figure').first().scrollIntoViewIfNeeded();
  await page.waitForFunction(()=>testWorkerPorts.length===1);
  check(await page.evaluate(()=>testWorkerPorts[0].url.endsWith('/vendor/pdfjs/pdf.worker.mjs')&&!testWorkerPorts[0].terminated),'Le worker PDF attend réellement son signal de disponibilité');
  await page.evaluate(()=>window.dispatchEvent(new Event('beforeunload')));
  check(await page.evaluate(()=>testWorkerPorts.every(port=>port.terminated)),'Le départ termine le worker même avant son signal de disponibilité');
  check(await page.evaluate(()=>{const error=new Event('error',{cancelable:true});testWorkerPorts[0].dispatchEvent(error);return error.defaultPrevented;}),'Une erreur tardive du port annulé ne devient pas une erreur de la nouvelle page');
  await page.evaluate(()=>window.dispatchEvent(new PageTransitionEvent('pagehide',{persisted:false})));
  await page.evaluate(()=>window.dispatchEvent(new PageTransitionEvent('pageshow',{persisted:true})));
  await page.waitForFunction(()=>testWorkerPorts.length===2);
  check(await page.evaluate(()=>!testWorkerPorts[1].terminated),'Le retour peut préparer un nouveau worker');
  await page.evaluate(()=>window.dispatchEvent(new PageTransitionEvent('pagehide',{persisted:false})));
  check(errors.length===0,'Aucune erreur JavaScript : '+errors.join(','));
  return {checks:checks.length,results:checks,real_model:false};
 }finally{await page.request.post(base+'/fixture/figures?enabled=false',{headers:{Origin:base}});}
}
