'use strict';

globalThis.SurvieMapStorage = (() => {
  const BLOCK_SIZE = 2 * 1024 * 1024;
  const VIEWER = '/cartes-hors-ligne/';
  const supported = () => window.isSecureContext && !!(
    navigator.serviceWorker && navigator.locks && window.indexedDB
  );
  function formatBytes(bytes) {
    const [unit, scale] = bytes >= 1e9 ? ['gigabyte', 1e9] : bytes >= 1e6 ? ['megabyte', 1e6] : ['kilobyte', 1e3];
    return new Intl.NumberFormat('fr-FR', {style: 'unit', unit, maximumFractionDigits: 1}).format(bytes / scale);
  }

  function openDatabase() {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open('survie-offline-maps', 2);
      request.onupgradeneeded = event => {
        if (event.oldVersion < 1) {
          request.result.createObjectStore('areas', {keyPath: 'id'});
          request.result.createObjectStore('blocks');
        }
        request.result.createObjectStore('viewer');
      };
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error);
    });
  }

  function read(request) {
    return new Promise((resolve, reject) => {
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error);
    });
  }

  function completed(transaction) {
    return new Promise((resolve, reject) => {
      transaction.oncomplete = resolve;
      transaction.onabort = () => reject(transaction.error || new Error('Écriture interrompue.'));
    });
  }

  function blockRange(key, first = 0, last = Number.MAX_SAFE_INTEGER) {
    return IDBKeyRange.bound([key, first], [key, last]);
  }

  async function areas() {
    const db = await openDatabase();
    try {
      return await read(db.transaction('areas').objectStore('areas').getAll());
    } finally {
      db.close();
    }
  }

  async function viewerAsset(version, path) {
    const db = await openDatabase();
    try {
      return await read(db.transaction('viewer').objectStore('viewer').get([version, path]));
    } finally {
      db.close();
    }
  }

  async function saveViewer(version, paths) {
    const db = await openDatabase();
    try {
      const keys = await read(db.transaction('viewer').objectStore('viewer').getAllKeys());
      if (paths.every(path => keys.some(key => key[0] === version && key[1] === path))) return;
      const files = await Promise.all(paths.map(async path => {
        const response = await fetch(path, {cache: 'reload', redirect: 'error'});
        if (!response.ok) throw new Error('Fichier du lecteur indisponible.');
        return response.blob();
      }));
      const transaction = db.transaction('viewer', 'readwrite');
      const assets = transaction.objectStore('viewer');
      for (let index = 0; index < paths.length; index++) assets.put(files[index], [version, paths[index]]);
      await completed(transaction);
    } finally {
      db.close();
    }
  }

  function source(db, area) {
    return {
      getKey: () => location.origin + VIEWER + 'archive/' + area.key,
      async getBytes(offset, length) {
        const count = Math.min(length, area.bytes - offset);
        if (count <= 0) throw new Error('Données de carte manquantes.');
        const first = Math.floor(offset / BLOCK_SIZE);
        const last = Math.floor((offset + count - 1) / BLOCK_SIZE);
        const blocks = await read(db.transaction('blocks').objectStore('blocks').getAll(blockRange(area.key, first, last)));
        if (blocks.length !== last - first + 1) throw new Error('Données de carte manquantes.');
        const data = new Uint8Array(count);
        let written = 0;
        let start = offset % BLOCK_SIZE;
        for (const buffer of blocks) {
          const bytes = new Uint8Array(buffer, start, Math.min(buffer.byteLength - start, count - written));
          data.set(bytes, written);
          written += bytes.length;
          start = 0;
        }
        if (written !== count) throw new Error('Données de carte incomplètes.');
        return {data: data.buffer};
      }
    };
  }

  function writeBlock(db, key, index, bytes) {
    const transaction = db.transaction('blocks', 'readwrite');
    transaction.objectStore('blocks').put(bytes, [key, index]);
    return completed(transaction);
  }

  async function pruneUnpublishedBlocks(db, saved) {
    // Keep the last published copy until its replacement has fully arrived.
    const published = new Set(saved.map(area => area.key));
    const transaction = db.transaction('blocks', 'readwrite');
    const blocks = transaction.objectStore('blocks');
    blocks.openKeyCursor().onsuccess = event => {
      const cursor = event.target.result;
      if (!cursor) return;
      if (!published.has(cursor.key[0])) blocks.delete(blockRange(cursor.key[0]));
      cursor.continue();
    };
    await completed(transaction);
  }

  async function streamParts(response, db, area, signal, onProgress) {
    const reader = response.body.getReader();
    let block = new Uint8Array(BLOCK_SIZE);
    let index = 0, used = 0, received = 0;
    try {
      for (;;) {
        const {done, value} = await reader.read();
        if (done) break;
        signal.throwIfAborted();
        received += value.length;
        if (received > area.bytes) throw new Error('La taille de la carte a changé sur le serveur.');
        let offset = 0;
        while (offset < value.length) {
          const count = Math.min(value.length - offset, BLOCK_SIZE - used);
          block.set(value.subarray(offset, offset + count), used);
          offset += count;
          used += count;
          if (used === BLOCK_SIZE) {
            await writeBlock(db, area.key, index++, block.buffer);
            block = new Uint8Array(BLOCK_SIZE);
            used = 0;
          }
        }
        onProgress(received);
      }
      if (received !== area.bytes) throw new Error('Téléchargement incomplet. Réessayez depuis le réseau de la maison.');
      if (used) await writeBlock(db, area.key, index, block.buffer.slice(0, used));
    } finally {
      await reader.cancel().catch(() => {});
    }
  }

  function withWriteLock(action) {
    return navigator.locks.request('survie-offline-maps', {ifAvailable: true}, lock => {
      if (!lock) throw new Error('Une autre fenêtre utilise déjà le stockage des cartes.');
      return action();
    });
  }

  function download(item, signal, onProgress) {
    return withWriteLock(async () => {
      const db = await openDatabase();
      const area = {
        id: item.id, title: item.title, bytes: item.bytes, sha256: item.sha256, edition: item.edition,
        center: item.center, bbox: item.bbox, attribution: item.attribution, key: crypto.randomUUID()
      };
      try {
        const saved = await read(db.transaction('areas').objectStore('areas').getAll());
        const previous = saved.find(item => item.id === area.id);
        await pruneUnpublishedBlocks(db, saved);
        if (previous?.sha256 === area.sha256) return;
        const estimate = navigator.storage?.estimate?.();
        const {quota, usage} = await estimate?.catch(() => ({})) || {};
        if (Number.isFinite(quota) && quota - usage < area.bytes) {
          throw new Error('Espace insuffisant dans ce navigateur. Libérez de la place ou choisissez une zone plus petite.');
        }
        const response = await fetch(item.url, {signal, cache: 'no-store', redirect: 'error'});
        if (response.status !== 200 || !response.body) throw new Error('Le serveur ne peut pas fournir cette carte.');
        await streamParts(response, db, area, signal, onProgress);
        const archive = new pmtiles.PMTiles(source(db, area));
        const header = await archive.getHeader();
        if (header.tileType !== 1) throw new Error('Ce fond de carte est illisible.');
        signal.throwIfAborted();
        const transaction = db.transaction(['areas', 'blocks'], 'readwrite');
        transaction.objectStore('areas').put(area);
        if (previous) transaction.objectStore('blocks').delete(blockRange(previous.key));
        await completed(transaction);
      } catch (error) {
        const transaction = db.transaction('blocks', 'readwrite');
        transaction.objectStore('blocks').delete(blockRange(area.key));
        await completed(transaction).catch(() => {});
        throw error;
      } finally {
        db.close();
      }
    });
  }

  function remove(area) {
    return withWriteLock(async () => {
      const db = await openDatabase();
      try {
        const saved = await read(db.transaction('areas').objectStore('areas').getAll());
        const current = saved.find(item => item.id === area.id);
        if (!current || current.key !== area.key) return;
        await pruneUnpublishedBlocks(db, saved);
        const transaction = db.transaction(['areas', 'blocks'], 'readwrite');
        transaction.objectStore('areas').delete(area.id);
        transaction.objectStore('blocks').delete(blockRange(area.key));
        await completed(transaction);
      } finally {
        db.close();
      }
    });
  }

  return {VIEWER, supported, formatBytes, areas, openDatabase, viewerAsset, saveViewer, source, download, remove};
})();
