"""Rebuildable native-search responses. Snapshot keys, bounded disk, no AI state."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import sqlite3
import time
from contextlib import closing

DEFAULT_BYTES=2_000_000_000
RESERVE_BYTES=15_000_000_000
MAX_AGE=24*60*60
MAX_ENTRY=1_000_000
MAX_ENTRIES=50_000


def budget():
    try:return max(0,int(os.environ.get('PILOT_SEARCH_CACHE_BYTES',DEFAULT_BYTES)))
    except (ValueError,OverflowError):return DEFAULT_BYTES


def snapshot(zims,books,index):
    """Always stat current sources; a replacement invalidates even a warm catalogue."""
    rows=[];zims=Path(zims)
    for book in books:
        name=book.get('book','')
        if not isinstance(name,str) or not name or Path(name).name!=name:continue
        path=zims/(name+'.zim')
        try:stat=path.stat();fingerprint=(stat.st_size,stat.st_mtime_ns)
        except OSError:fingerprint=None
        rows.append((name,book.get('search_id',''),book.get('language',''),fingerprint))
    try:stat=(Path(index)/'manifest.json').stat();manifest=(stat.st_size,stat.st_mtime_ns)
    except OSError:manifest=None
    return hashlib.sha256(json.dumps([2,sorted(rows),manifest],ensure_ascii=True).encode()).hexdigest()


def token(key):return hashlib.sha256(json.dumps(key,ensure_ascii=True).encode()).hexdigest()


def read(root,key):
    path=Path(root)/'cache/search/responses.sqlite'
    if not budget() or not path.is_file() or path.is_symlink():return None
    try:
        with closing(sqlite3.connect(path.resolve().as_uri()+'?mode=ro',uri=True,timeout=.1)) as db:
            db.execute('PRAGMA query_only=ON')
            row=db.execute('SELECT created,content,raw FROM responses WHERE key=? AND bytes<=? AND length(raw)<=?',(token(key),MAX_ENTRY,MAX_ENTRY)).fetchone()
        if row and 0<=time.time()-row[0]<MAX_AGE and isinstance(row[2],bytes) and len(row[2])<=MAX_ENTRY:return row[2],row[1]
    except (OSError,sqlite3.Error,ValueError):pass
    return None


def write(root,key,value):write_many(root,[(key,value)])


def write_many(root,entries):
    """One transaction per batch: a single synchronised commit instead of one
    per Kiwix response, and readers wait for one short lock, not hundreds."""
    maximum=budget()
    entries=[(key,value) for key,value in entries if maximum and len(value[0])<=min(maximum,MAX_ENTRY)]
    if not entries:return
    folder=Path(root)/'cache/search';path=folder/'responses.sqlite'
    try:
        # Optional cache must not consume the installation's remaining workspace.
        folder.mkdir(parents=True,exist_ok=True)
        if path.is_symlink() or shutil.disk_usage(folder).free<RESERVE_BYTES+sum(len(value[0]) for _,value in entries):return
        with closing(sqlite3.connect(path,timeout=.1)) as db:
            db.execute('PRAGMA auto_vacuum=INCREMENTAL')
            db.execute('PRAGMA journal_mode=DELETE');db.execute('PRAGMA synchronous=NORMAL')
            db.execute('CREATE TABLE IF NOT EXISTS responses(key TEXT PRIMARY KEY,created REAL,content TEXT,bytes INTEGER,raw BLOB)')
            db.execute('CREATE INDEX IF NOT EXISTS response_age ON responses(created)')
            now=time.time();db.execute('DELETE FROM responses WHERE created<?',(now-MAX_AGE,))
            db.executemany('INSERT OR REPLACE INTO responses VALUES(?,?,?,?,?)',[(token(key),now,str(content)[:100],len(raw),raw) for key,(raw,content) in entries])
            total,count=db.execute('SELECT COALESCE(sum(bytes),0),count(*) FROM responses').fetchone()
            if total>maximum or count>MAX_ENTRIES:
                for old,size in db.execute('SELECT key,bytes FROM responses ORDER BY created').fetchall():
                    if total<=maximum and count<=MAX_ENTRIES:break
                    db.execute('DELETE FROM responses WHERE key=?',(old,));total-=size;count-=1
            db.commit();db.execute('PRAGMA incremental_vacuum(256)')
        if os.name!='nt':path.chmod(0o600)
    except (OSError,sqlite3.Error,ValueError):return
