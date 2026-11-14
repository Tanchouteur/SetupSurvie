"""Private shared map notebooks; routing and saves never depend on a live GPS."""
import json
import time
import uuid
import xml.etree.ElementTree as ET
from fastapi import HTTPException
from . import geography, store


def init():
    with store.connect() as db:
        db.executescript('''
        CREATE TABLE IF NOT EXISTS map_lists(id TEXT PRIMARY KEY,title TEXT NOT NULL,created REAL NOT NULL);
        CREATE TABLE IF NOT EXISTS map_points(id TEXT PRIMARY KEY,list_id TEXT NOT NULL REFERENCES map_lists(id),title TEXT NOT NULL,lat REAL NOT NULL,lon REAL NOT NULL,kind TEXT NOT NULL,notes TEXT NOT NULL,updated REAL NOT NULL);
        CREATE TABLE IF NOT EXISTS map_routes(id TEXT PRIMARY KEY,list_id TEXT NOT NULL REFERENCES map_lists(id),title TEXT NOT NULL,mode TEXT NOT NULL,data TEXT NOT NULL,created REAL NOT NULL);
        CREATE TABLE IF NOT EXISTS map_drafts(id TEXT PRIMARY KEY,user_id TEXT NOT NULL,data TEXT NOT NULL,created REAL NOT NULL);
        ''')


def require_list(db, identifier):
    if not db.execute('SELECT 1 FROM map_lists WHERE id=?',(identifier,)).fetchone():raise HTTPException(404,'Liste introuvable.')


def overview():
    with store.connect() as db:
        lists=[dict(r) for r in db.execute('SELECT * FROM map_lists ORDER BY created,id')]
        points=[dict(r) for r in db.execute('SELECT * FROM map_points ORDER BY updated,id')]
        routes=[]
        for row in db.execute('SELECT * FROM map_routes ORDER BY created DESC,id'):
            data=json.loads(row['data']);routes.append({k:row[k] for k in ('id','list_id','title','mode','created')}|{k:data.get(k) for k in ('distance_m','duration_s','speed_kmh','created_at')})
    return {'lists':lists,'points':points,'routes':routes}


def save_list(title,identifier=None):
    title=title.strip()
    if not title:raise HTTPException(400,'Donnez un nom à la liste.')
    with store.connect() as db:
        if identifier:
            require_list(db,identifier);db.execute('UPDATE map_lists SET title=? WHERE id=?',(title,identifier))
        else:
            if db.execute('SELECT count(*) FROM map_lists').fetchone()[0]>=50:raise HTTPException(409,'Limite de 50 listes atteinte.')
            identifier=uuid.uuid4().hex;db.execute('INSERT INTO map_lists VALUES(?,?,?)',(identifier,title,time.time()))
    return {'id':identifier,'title':title}


def delete_list(identifier):
    with store.connect() as db:
        require_list(db,identifier)
        if db.execute('SELECT 1 FROM map_points WHERE list_id=? UNION ALL SELECT 1 FROM map_routes WHERE list_id=?',(identifier,identifier)).fetchone():raise HTTPException(409,'Cette liste contient des points ou trajets. Déplacez-les ou supprimez-les d’abord.')
        db.execute('DELETE FROM map_lists WHERE id=?',(identifier,))


def save_point(body,identifier=None):
    lat,lon=geography.coordinates(body['lat'],body['lon']);title=body['title'].strip()
    if not title:raise HTTPException(400,'Donnez un nom au point.')
    with store.connect() as db:
        require_list(db,body['list_id'])
        if identifier:
            if not db.execute('SELECT 1 FROM map_points WHERE id=?',(identifier,)).fetchone():raise HTTPException(404,'Point introuvable.')
            db.execute('UPDATE map_points SET list_id=?,title=?,lat=?,lon=?,kind=?,notes=?,updated=? WHERE id=?',(body['list_id'],title,lat,lon,body['kind'],body['notes'],time.time(),identifier))
        else:
            if db.execute('SELECT count(*) FROM map_points').fetchone()[0]>=1000:raise HTTPException(409,'Limite de 1 000 points atteinte.')
            identifier=uuid.uuid4().hex
            db.execute('INSERT INTO map_points VALUES(?,?,?,?,?,?,?,?)',(identifier,body['list_id'],title,lat,lon,body['kind'],body['notes'],time.time()))
    return {'id':identifier}


def delete_point(identifier):
    with store.connect() as db:
        if not db.execute('SELECT 1 FROM map_points WHERE id=?',(identifier,)).fetchone():raise HTTPException(404,'Point introuvable.')
        db.execute('DELETE FROM map_points WHERE id=?',(identifier,))
    # Saved routes are snapshots, so editing/deleting a reference point cannot corrupt them.


def draft(user_id,data):
    identifier=uuid.uuid4().hex
    with store.connect() as db:
        db.execute('DELETE FROM map_drafts WHERE created<?',(time.time()-3600,))
        db.execute('DELETE FROM map_drafts WHERE id IN (SELECT id FROM map_drafts WHERE user_id=? ORDER BY created DESC LIMIT -1 OFFSET 9)',(user_id,))
        db.execute('INSERT INTO map_drafts VALUES(?,?,?,?)',(identifier,user_id,json.dumps(data,ensure_ascii=False),time.time()))
    return {**data,'draft_id':identifier}


def save_route(user_id,draft_id,list_id,title):
    with store.connect() as db:
        require_list(db,list_id)
        row=db.execute('SELECT data FROM map_drafts WHERE id=? AND user_id=? AND created>?',(draft_id,user_id,time.time()-3600)).fetchone()
        if not row:raise HTTPException(409,'Calcul expiré. Recalculez le trajet avant de l’enregistrer.')
        if db.execute('SELECT count(*) FROM map_routes').fetchone()[0]>=100:raise HTTPException(409,'Limite de 100 trajets enregistrés atteinte.')
        identifier=uuid.uuid4().hex;data=json.loads(row['data'])
        db.execute('INSERT INTO map_routes VALUES(?,?,?,?,?,?)',(identifier,list_id,title.strip(),data['mode'],row['data'],time.time()))
        db.execute('DELETE FROM map_drafts WHERE id=?',(draft_id,))
    return {'id':identifier}


def route(identifier):
    with store.connect() as db:
        row=db.execute('SELECT * FROM map_routes WHERE id=?',(identifier,)).fetchone()
    if not row:raise HTTPException(404,'Trajet introuvable.')
    return {'id':row['id'],'list_id':row['list_id'],'title':row['title'],**json.loads(row['data'])}


def delete_route(identifier):
    with store.connect() as db:
        if not db.execute('SELECT 1 FROM map_routes WHERE id=?',(identifier,)).fetchone():raise HTTPException(404,'Trajet introuvable.')
        db.execute('DELETE FROM map_routes WHERE id=?',(identifier,))


def gpx(list_id=None,route_id=None):
    namespace='http://www.topografix.com/GPX/1/1';ET.register_namespace('',namespace)
    def child(parent,tag,text=None,**attributes):
        el=ET.SubElement(parent,'{'+namespace+'}'+tag,attributes)
        if text is not None:el.text=str(text)
        return el
    root=ET.Element('{'+namespace+'}gpx',{'version':'1.1','creator':'SetupSurvie'})
    if route_id:
        item=route(route_id)
        for point in item.get('points',[]):
            origin=child(root,'wpt',lat=str(point['lat']),lon=str(point['lon']));child(origin,'name',point['title'])
            child(origin,'desc','Point d’origine. Liaison vers la voie à vérifier, non incluse dans la trace calculée.')
            if point.get('offset_m',0)>5:
                access=child(root,'wpt',lat=str(point['snapped_lat']),lon=str(point['snapped_lon']))
                child(access,'name','Accès · '+point['title']);child(access,'desc',str(round(point['offset_m']))+' m à vol d’oiseau du point. Liaison non vérifiée.')
        track=child(root,'trk');child(track,'name',item['title']);child(track,'desc',item['note'])
        segment=child(track,'trkseg')
        for lon,lat in item['geometry']['coordinates']:child(segment,'trkpt',lat=str(lat),lon=str(lon))
    else:
        with store.connect() as db:
            require_list(db,list_id)
            points=db.execute('SELECT * FROM map_points WHERE list_id=? ORDER BY updated,id',(list_id,)).fetchall()
        for point in points:
            el=child(root,'wpt',lat=str(point['lat']),lon=str(point['lon']));child(el,'name',point['title']);child(el,'desc',point['notes'])
    return ET.tostring(root,encoding='utf-8',xml_declaration=True)
