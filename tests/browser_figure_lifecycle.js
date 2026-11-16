// Delay only our PDF module import; no inference or external resource.
async page=>{
 const base='http://10.0.3.2:8769',checks=[],errors=[];
 const check=(ok,label)=>{if(!ok)throw Error(label);checks.push(label);};
 page.on('pageerror',error=>errors.push(error.message));
 let release;const gate=new Promise(resolve=>release=resolve);
 await page.route('**/vendor/pdfjs/pdf.mjs',async route=>{await gate;await route.fulfill({contentType:'text/javascript',body:'window.figureModuleLoaded=true;export const GlobalWorkerOptions={};export class PDFWorker{constructor(){window.postDepartureWorker=(window.postDepartureWorker||0)+1;}destroy(){}}export function getDocument(){throw Error("Unexpected PDF after departure");}'});});
 await page.request.post(base+'/fixture/figures?enabled=true',{headers:{Origin:base}});
 try{
  await page.request.post(base+'/api/profiles/select',{data:{id:'browser'},headers:{Origin:base}});
  await page.goto(base+'/#/assistant');await page.waitForFunction(()=>S.user&&!S.loadingConversation);await page.locator('#chat-reset').click();
  const pending=page.waitForRequest(request=>request.url().endsWith('/vendor/pdfjs/pdf.mjs'));
  await page.locator('#chat-input').fill('Montre les schémas fixture du montage.');await page.locator('#send-question').click();
  await page.waitForFunction(()=>document.querySelectorAll('.source-figure').length===2);await page.locator('.source-figure').first().scrollIntoViewIfNeeded();await pending;
  check(true,'Un chargement de module PDF est réellement retardé');
  await page.evaluate(()=>window.dispatchEvent(new PageTransitionEvent('pagehide',{persisted:false})));release();
  await page.waitForFunction(()=>window.figureModuleLoaded===true);
  check(await page.evaluate(()=>!window.postDepartureWorker),'Le module arrivé après le départ ne démarre aucun worker PDF');
  check(await page.locator('.message-assistant').count()>0,'La réponse textuelle reste présente');
  check(errors.length===0,'Aucune erreur JavaScript : '+errors.join(','));
  return {checks:checks.length,results:checks,real_model:false};
 }finally{release();await page.request.post(base+'/fixture/figures?enabled=false',{headers:{Origin:base}});}
}
