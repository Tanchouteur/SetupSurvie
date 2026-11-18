"""Read-only document checks run inside the restored pilot, never print content."""
import json
import os
from pathlib import Path
import sqlite3
import urllib.parse
import urllib.request
from xml.etree import ElementTree


def probe_routing(opener):
    if not (Path(os.environ.get('MAPS_DIR','/maps'))/'routing/current/manifest.json').is_file():return 'not_prepared'
    for mode in ('foot','motorcycle','car'):
        # Only the fixed local service names; never an Internet routing fallback.
        with opener.open('http://router-'+mode+':5000/nearest/v1/driving/0,0?number=1',timeout=15) as response:
            value=json.load(response)
        if value.get('code')!='Ok' or not value.get('waypoints'):raise ValueError('Moteur local d’itinéraire indisponible après transfert.')
    return 'passed'


def probe_kiwix(opener):
    if not any(Path('/zim').glob('*.zim')):return 'not_prepared'
    with opener.open('http://kiwix:8080/catalog/v2/entries?count=1',timeout=15) as response:
        catalogue=ElementTree.parse(response)
    if catalogue.find('{http://www.w3.org/2005/Atom}entry') is None:
        raise ValueError('Archives présentes sur le disque mais absentes du catalogue Kiwix.')
    return 'passed'


def probe():
    opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
    routing=probe_routing(opener)
    kiwix=probe_kiwix(opener)
    path=Path(os.environ.get('PILOT_STATE_DIR','/pilot-data'))/'pilot.db'
    from contextlib import closing
    with closing(sqlite3.connect(path.as_uri()+'?mode=ro',uri=True)) as db:
        row=db.execute("SELECT title FROM documents WHERE title!='' LIMIT 1").fetchone()
        if row is None:row=db.execute("SELECT title FROM passages WHERE title!='' LIMIT 1").fetchone()
    if row is None:return {'search':'not_tested_no_indexed_guide','open_document':'not_tested','routing':routing,'kiwix':kiwix}
    def get(route):
        with opener.open('http://127.0.0.1:8000'+route,timeout=90) as response:return json.load(response)
    results=get('/api/search?'+urllib.parse.urlencode({'q':row[0][:160],'limit':3}))['results']
    if not results:raise ValueError('Recherche sans résultat après transfert.')
    document=get('/api/source?'+urllib.parse.urlencode({'id':results[0]['id']}))
    if not document:raise ValueError('Ouverture documentaire vide après transfert.')
    return {'search':'passed','open_document':'passed','routing':routing,'kiwix':kiwix}


if __name__=='__main__':
    try:print(json.dumps(probe()))
    except Exception:
        print(json.dumps({'search':'failed','open_document':'failed'}))
        raise SystemExit(1)
