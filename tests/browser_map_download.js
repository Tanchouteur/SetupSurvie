// A real service worker and IndexedDB; tiny synthetic PMTiles padded to span blocks.
async (page, reopenWithoutServer) => {
  const base = 'http://10.0.3.2:8766';
  const original = Buffer.from('__PMTILES_FIXTURE__', 'base64');
  const archive = Buffer.concat([original, Buffer.alloc(2 * 1024 * 1024 + 64, 71)]);
  let revision = 'a', truncate = false;
  const item = () => ({
    id: 'sollies', title: 'Carte fictive', url: '/api/maps/test/archive',
    center: [6.1, 43.1], bbox: [6.095, 43.09, 6.12, 43.11], maxzoom: 12,
    edition: '2026-11-10', attribution: 'Données fictives', bytes: archive.length, sha256: revision.repeat(64)
  });
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  await page.route('**/api/**', async route => {
    const request = route.request();
    const path = new URL(request.url()).pathname;
    if (path.endsWith('/archive')) {
      const range = request.headers().range?.match(/bytes=(\d+)-(\d+)/);
      if (!range) {
        return route.fulfill({status: 200, body: truncate ? archive.subarray(0, -31) : archive});
      }
      const start = Number(range[1]), end = Math.min(Number(range[2]), archive.length - 1);
      return route.fulfill({status: 206, headers: {
        'Content-Range': `bytes ${start}-${end}/${archive.length}`, 'Accept-Ranges': 'bytes'
      }, body: archive.subarray(start, end + 1)});
    }
    if (path === '/api/maps') return route.fulfill({json: {maps: [item()]}});
    return route.fulfill({status: 401, json: {detail: 'Profil non choisi'}});
  });
  await page.setViewportSize({width: 320, height: 568});
  await page.goto(base + '/cartes.html');
  await page.waitForFunction(() => window.SurvieMap);
  await page.locator('#offline-map').focus();
  await page.keyboard.press('Enter');
  await page.locator('#offline-map-dialog').waitFor({state: 'visible'});
  await page.locator('#download-offline-map').click();
  await page.locator('#offline-map-progress').waitFor({state: 'hidden', timeout: 45000});
  const firstResult = await page.locator('#offline-map-status').innerText();
  if (!firstResult.includes('Carte prête')) throw Error(firstResult);
  const saved = await page.evaluate(async () => (await SurvieMapStorage.areas())[0]);
  const offlinePath = await page.locator('#open-offline-maps').getAttribute('href');
  if (!offlinePath || saved.sha256 !== item().sha256) throw Error('Zone non publiée');

  revision = 'b';
  truncate = true;
  await page.reload();
  await page.waitForFunction(() => window.SurvieMap);
  await page.locator('#offline-map').focus();
  await page.keyboard.press('Enter');
  await page.locator('#offline-map-dialog').waitFor({state: 'visible'});
  await page.getByRole('button', {name: 'Mettre à jour', exact: true}).click();
  await page.locator('#offline-map-progress').waitFor({state: 'hidden'});
  const replacementResult = await page.locator('#offline-map-status').innerText();
  if (!replacementResult.includes('incomplet')) throw Error(replacementResult);
  if (await page.evaluate(async () => (await SurvieMapStorage.areas())[0].key) !== saved.key) {
    throw Error('Un transfert incomplet a remplacé la carte saine');
  }

  const viewer = await reopenWithoutServer();
  await viewer.addInitScript(() => {
    Object.defineProperty(window, 'survieMapStyle', {set(style) {
      Object.defineProperty(window, 'survieMapStyle', {value: style});
      const Map = maplibregl.Map;
      maplibregl.Map = class extends Map {
        constructor(options) {
          super(options);
          window.testOfflineMap = this;
        }
      };
    }, configurable: true});
  });
  viewer.on('pageerror', error => errors.push(error.message));
  await viewer.setViewportSize({width: 320, height: 568});
  await viewer.goto(base + offlinePath);
  await viewer.waitForFunction(() => document.querySelector('#map').dataset.ready === 'true');
  if (!await viewer.evaluate(() => testOfflineMap.queryRenderedFeatures({layers: ['roads']}).length > 0)) {
    throw Error('Routes vectorielles absentes après redémarrage hors ligne');
  }
  if (!(await viewer.locator('#status').innerText()).includes('Disponible sans le serveur')) {
    throw Error('Carte non rendue après fermeture de l’onglet et coupure réseau');
  }
  const localBytes = await viewer.evaluate(async () => {
    const [area] = await SurvieMapStorage.areas();
    const db = await SurvieMapStorage.openDatabase();
    try {
      const source = SurvieMapStorage.source(db, area);
      const {data} = await source.getBytes(2 * 1024 * 1024 - 16, 32);
      return Array.from(new Uint8Array(data));
    } finally { db.close(); }
  });
  if (!localBytes.every(byte => byte === 71) || localBytes.length !== 32) throw Error('Lecture entre deux blocs incorrecte');
  await viewer.screenshot({path:'/artifacts/setupsurvie-carte-telechargee.png',fullPage:true});

  viewer.once('dialog', dialog => dialog.accept());
  await viewer.locator('#remove-area').click();
  await viewer.waitForFunction(() => document.querySelector('#status').textContent.includes('Aucune carte'));
  await viewer.reload();
  if (!(await viewer.locator('#status').innerText()).includes('Aucune carte')) {
    await viewer.waitForFunction(() => document.querySelector('#status').textContent.includes('Aucune carte'));
  }
  if (errors.length) throw Error(JSON.stringify(errors));
  return {passed:true,service_worker:true,persists_after_browser_restart:true,server_stopped:true,vector_tiles_rendered:true,incomplete_replacement_preserved:true,purge:true};
}
