"""Account-owned bookmarks; local documents use the complete page index."""
import time
from fastapi import HTTPException
from . import library, store


def canonical(identifier):
    return identifier.split('#page=', 1)[0] if identifier.startswith('guide:') else identifier


def listing(user_id, language=''):
    with store.connect() as db:
        rows=db.execute("SELECT source_id AS id,title,url,language,created FROM favorites WHERE user_id=? AND (?='' OR language IN (?,?)) ORDER BY created DESC",(user_id,language,language,{'fr':'fra','en':'eng'}.get(language,language))).fetchall()
        return [{**dict(row),'kind':'guide' if row['id'].startswith('guide:') else 'video' if row['id'].startswith('video:') else 'article','excerpt':'',
                 **(library.guide_metadata(db,row['id']) if row['id'].startswith('guide:') else {})} for row in rows]


async def add(user_id, identifier):
    identifier=canonical(identifier)
    source=await library.source(identifier)
    with store.connect() as db:
        db.execute('BEGIN IMMEDIATE')
        existing=db.execute('SELECT 1 FROM favorites WHERE user_id=? AND source_id=?',(user_id,identifier)).fetchone()
        if not existing and db.execute('SELECT count(*) FROM favorites WHERE user_id=?',(user_id,)).fetchone()[0]>=1000:
            raise HTTPException(409,'Votre liste atteint 1 000 favoris. Retirez un favori avant d’en ajouter un autre.')
        db.execute('INSERT INTO favorites VALUES(?,?,?,?,?,?) ON CONFLICT(user_id,source_id) DO UPDATE SET title=excluded.title,url=excluded.url,language=excluded.language',
                   (user_id,identifier,source['title'],source['url'],source.get('language',''),time.time()))
        db.execute('DELETE FROM favorite_articles WHERE user_id=? AND id=?',(user_id,identifier))
        if identifier.startswith('zim:'):
            db.execute('INSERT INTO favorite_articles VALUES(?,?,?,?,?,?)',(user_id,identifier,source['title'],source['url'],source.get('language',''),source['text']))


def remove(user_id, identifier):
    with store.connect() as db:
        db.execute('DELETE FROM favorites WHERE user_id=? AND source_id=?',(user_id,canonical(identifier)))
        db.execute('DELETE FROM favorite_articles WHERE user_id=? AND id=?',(user_id,canonical(identifier)))
