"""Read-only document checks run inside the restored pilot, never print content."""
import json
import os
from pathlib import Path
import sqlite3
import urllib.parse
import urllib.request


def probe():
    path=Path(os.environ.get('PILOT_STATE_DIR','/pilot-data'))/'pilot.db'
    from contextlib import closing
    with closing(sqlite3.connect(path.as_uri()+'?mode=ro',uri=True)) as db:
        row=db.execute("SELECT title FROM documents WHERE title!='' LIMIT 1").fetchone()
        if row is None:row=db.execute("SELECT title FROM passages WHERE title!='' LIMIT 1").fetchone()
    if row is None:return {'search':'not_tested_no_indexed_guide','open_document':'not_tested'}
    opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
    def get(route):
        with opener.open('http://127.0.0.1:8000'+route,timeout=90) as response:return json.load(response)
    results=get('/api/search?'+urllib.parse.urlencode({'q':row[0][:160],'limit':3}))['results']
    if not results:raise ValueError('Recherche sans résultat après transfert.')
    document=get('/api/source?'+urllib.parse.urlencode({'id':results[0]['id']}))
    if not document:raise ValueError('Ouverture documentaire vide après transfert.')
    return {'search':'passed','open_document':'passed'}


if __name__=='__main__':
    try:print(json.dumps(probe()))
    except Exception:
        print(json.dumps({'search':'failed','open_document':'failed'}))
        raise SystemExit(1)
