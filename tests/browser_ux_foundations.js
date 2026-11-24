// Small fixture API only. Proves navigation and help, never translation fidelity.
async page => {
  const base='http://10.0.3.2:8769',checks=[],errors=[],commands=[];
  const check=(value,label)=>{if(!value)throw Error(label);checks.push(label);};
  page.on('pageerror',e=>errors.push(e.message));
  page.on('request',r=>{if(r.method()==='POST')commands.push(new URL(r.url()).pathname);});
  for(const width of [320,390,1024,1366,1440,1920]){
    await page.setViewportSize({width,height:900});await page.goto(base+'/#/bibliotheque/collections');
    await page.evaluate(()=>window.scrollTo(0,0));
    await page.waitForFunction(()=>typeof S!=='undefined'&&S.authReady&&S.user);
    check(await page.locator('#view-library h1').innerText()==='Bibliothèque','Titre concret à '+width);
    check(!await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),'Pas de débordement à '+width);
    const books = page.locator('#collection-section-livres');
    const heading = books.locator(':scope > summary');
    await heading.waitFor();
    check(await heading.evaluate(node => {
      const bounds = node.getBoundingClientRect();
      return bounds.top >= 0 && bounds.bottom <= innerHeight;
    }), 'Livres et encyclopédies accessibles au premier écran à '+width);
    if (!await books.evaluate(node => node.open)) await heading.click();
    await page.locator('#data-books').waitFor({state:'visible'});
    check(await books.evaluate(node => node.open), 'Livres et encyclopédies consultables à '+width);
    const help=page.getByRole('button',{name:'Comprendre le filtre des collections',exact:true});
    await help.click();check(await help.getAttribute('aria-expanded')==='true','Aide ouverte au clic à '+width);
    await page.keyboard.press('Escape');check(await help.getAttribute('aria-expanded')==='false','Aide fermée par Échap à '+width);
    await page.locator('#collection-filter').focus();await page.keyboard.press('Shift+Tab');
    check(await help.evaluate(n=>n===document.activeElement),'Aide dans l’ordre du clavier à '+width);
    await page.keyboard.press('Escape');
  }
  await page.goto(base+'/#/bibliotheque/recherche?q=Shelter');
  await page.waitForSelector('#search-results .result button');
  await page.locator('#search-results .result button').first().click();
  await page.waitForFunction(()=>document.activeElement?.matches('#reader h2'));
  check(await page.locator('#library-search').isHidden(),'Recherche laisse la place à la lecture');
  check(await page.locator('#reader h2').evaluate(n=>n.getBoundingClientRect().top)<500,'Lecture visible sur ordinateur');
  await page.locator('#reader .reader-actions button').first().click();
  await page.waitForSelector('#library-search',{state:'visible'});
  check(await page.locator('#library-query').inputValue()==='Shelter','Retour conserve la recherche');
  check(!commands.length,'Aucune commande serveur par consultation');
  check(!errors.length,'Aucune erreur JavaScript : '+errors.join(','));
  return {checks:checks.length,results:checks};
}
