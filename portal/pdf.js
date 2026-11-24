/* A separate page and module: PDF failures cannot stop the portal script. */
const $=id=>document.getElementById(id);
try{
  const identifier=new URLSearchParams(location.search).get('id')||'',base=identifier.split('#page=')[0];
  if(!base.startsWith('guide:')||!base.toLowerCase().endsWith('.pdf'))throw Error('Référence PDF non valide.');
  const path=base.slice(6);if(path.includes('\\')||path.split('/').some(p=>!p||p==='..'||p==='.'))throw Error('Chemin PDF non valide.');
  const file='/guides/'+path.split('/').map(encodeURIComponent).join('/');
  $('pdf-title').textContent=path.split('/').pop();
  const metadata=new AbortController(),metadataTimer=setTimeout(()=>metadata.abort(),2500);
  fetch('/api/source?id='+encodeURIComponent(base),{signal:metadata.signal}).then(async info=>{
    if(info.ok){const source=await info.json();$('pdf-title').textContent=source.title;document.title=source.title+' — SetupSurvie';}
  }).catch(()=>{}).finally(()=>clearTimeout(metadataTimer));
  const lib=await import('/vendor/pdfjs/pdf.mjs');
  lib.GlobalWorkerOptions.workerSrc='/vendor/pdfjs/pdf.worker.mjs';
  const {EventBus,PDFViewer,PDFLinkService,PDFFindController}=await import('/vendor/pdfjs/pdf_viewer.mjs');
  const eventBus=new EventBus(),linkService=new PDFLinkService({eventBus,externalLinkTarget:2,externalLinkRel:'noopener noreferrer'});
  const findController=new PDFFindController({eventBus,linkService});
  const viewer=new PDFViewer({container:$('pdf-container'),viewer:$('pdf-viewer'),eventBus,linkService,findController,maxCanvasPixels:4194304});
  linkService.setViewer(viewer);
  let wanted=Number(document.documentElement.dataset.frenchReaderPage)||Number(identifier.split('#page=')[1])||1,initialized=false;
  const pageNumber=()=>Math.max(1,Math.min(wanted,viewer.pagesCount||1200));
  window.addEventListener('survie:pdf-go',event=>{wanted=event.detail.page;$('pdf-page').value=pageNumber();if(initialized&&!$('pdf-container').hidden)viewer.currentPageNumber=pageNumber();});
  window.addEventListener('survie:pdf-view',event=>{if(event.detail.original)requestAnimationFrame(()=>{if(initialized){viewer.currentScaleValue='page-width';viewer.currentPageNumber=pageNumber();viewer.update();$('pdf-status').textContent='PDF original · texte, mise en page et illustrations. Aucun modèle IA nécessaire.';}});});
  eventBus.on('pagesinit',()=>{initialized=true;wanted=pageNumber();$('pdf-page').value=wanted;if(!$('pdf-container').hidden){viewer.currentScaleValue='page-width';viewer.currentPageNumber=wanted;}for(const button of document.querySelectorAll('.pdf-controls button,.pdf-controls input'))button.disabled=false;window.dispatchEvent(new CustomEvent('survie:pdf-page',{detail:{page:wanted}}));});
  eventBus.on('pagechanging',event=>{if(!initialized)return;wanted=event.pageNumber;$('pdf-page').value=event.pageNumber;window.dispatchEvent(new CustomEvent('survie:pdf-page',{detail:{page:event.pageNumber}}));});
  eventBus.on('updatefindmatchescount',event=>{$('pdf-status').textContent=event.matchesCount.total+' résultat(s) dans le PDF.';});
  // Bound raster resizing instead of probing the browser's maximum allocation.
  // The source PDF remains intact; large images are resized for this display.
  const documentTask=lib.getDocument({url:file,cMapUrl:'/vendor/pdfjs/cmaps/',cMapPacked:true,standardFontDataUrl:'/vendor/pdfjs/standard_fonts/',wasmUrl:'/vendor/pdfjs/wasm/',isEvalSupported:false,canvasMaxAreaInBytes:16777216,disableAutoFetch:true,disableStream:true,enableXfa:false});
  const pdf=await documentTask.promise;viewer.setDocument(pdf);linkService.setDocument(pdf);
  $('pdf-count').textContent='/ '+pdf.numPages;$('pdf-page').max=pdf.numPages;
  $('pdf-previous').onclick=()=>{viewer.currentPageNumber=Math.max(1,viewer.currentPageNumber-1);};
  $('pdf-next').onclick=()=>{viewer.currentPageNumber=Math.min(pdf.numPages,viewer.currentPageNumber+1);};
  $('pdf-page').onchange=()=>{const n=Number($('pdf-page').value);if(Number.isInteger(n)&&n>=1&&n<=pdf.numPages)viewer.currentPageNumber=n;else $('pdf-page').value=viewer.currentPageNumber;};
  $('pdf-zoom-in').onclick=()=>{viewer.currentScale=Math.min(4,viewer.currentScale*1.2);};
  $('pdf-zoom-out').onclick=()=>{viewer.currentScale=Math.max(.25,viewer.currentScale/1.2);};
  $('pdf-fit').onclick=()=>{viewer.currentScaleValue='page-width';};
  $('pdf-search').onsubmit=event=>{event.preventDefault();eventBus.dispatch('find',{source:window,type:'again',query:$('pdf-query').value,caseSensitive:false,entireWord:false,highlightAll:true,findPrevious:false,matchDiacritics:false});};
  let resizeTimer;window.addEventListener('resize',()=>{clearTimeout(resizeTimer);resizeTimer=setTimeout(()=>{if(!$('pdf-container').hidden&&viewer.currentScaleValue==='page-width')viewer.currentScaleValue='page-width';},100);});
  $('pdf-status').textContent=$('pdf-container').hidden?'Texte français enregistré · traduction IA non vérifiée.':'PDF original · texte, mise en page et illustrations. Aucun modèle IA nécessaire.';
}catch(error){$('pdf-status').textContent='Le lecteur local ne peut pas afficher ce PDF. Ouvrez l’original directement ou téléchargez-le. '+error.message;}
