"""Small persistent application store; no plaintext passwords or recovery codes."""
import hashlib
from contextlib import contextmanager
import hmac
import json
import os
from pathlib import Path
import secrets
import sqlite3
import time
import uuid
from . import durable

ROOT = Path(os.environ.get('PILOT_STATE_DIR', '/pilot-data'))


@contextmanager
def connect():
    durable.mkdir(ROOT)
    ROOT.chmod(0o700)
    db = sqlite3.connect(ROOT / 'pilot.db', timeout=20)
    db.row_factory = sqlite3.Row
    db.execute('PRAGMA journal_mode=WAL')
    db.execute('PRAGMA synchronous=FULL')
    db.execute('PRAGMA foreign_keys=ON')
    (ROOT / 'pilot.db').chmod(0o600)
    try:
        with db:yield db
    finally:db.close()


def init():
    with connect() as db:
        db.executescript('''
        CREATE TABLE IF NOT EXISTS work_history(id TEXT PRIMARY KEY, data TEXT NOT NULL, updated REAL NOT NULL);
        CREATE TABLE IF NOT EXISTS youtube_pipeline(id TEXT PRIMARY KEY, kind TEXT NOT NULL, data TEXT NOT NULL, updated REAL NOT NULL);
        CREATE TABLE IF NOT EXISTS profiles(id TEXT PRIMARY KEY,name TEXT NOT NULL,email TEXT NOT NULL UNIQUE,role TEXT NOT NULL,origin TEXT NOT NULL,created REAL NOT NULL);
        CREATE TABLE IF NOT EXISTS recovery(user_id TEXT PRIMARY KEY,salt TEXT NOT NULL,digest TEXT NOT NULL,used INTEGER NOT NULL DEFAULT 0);
        CREATE TABLE IF NOT EXISTS limits(key TEXT PRIMARY KEY,count INTEGER NOT NULL,until REAL NOT NULL);
        CREATE TABLE IF NOT EXISTS revoked(digest TEXT PRIMARY KEY,expires REAL NOT NULL);
        CREATE TABLE IF NOT EXISTS conversations(id TEXT PRIMARY KEY,user_id TEXT NOT NULL,title TEXT NOT NULL,created REAL NOT NULL);
        CREATE TABLE IF NOT EXISTS conversation_sources(conversation_id TEXT PRIMARY KEY REFERENCES conversations(id) ON DELETE CASCADE,source_id TEXT NOT NULL,title TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS translations(id TEXT PRIMARY KEY,user_id TEXT NOT NULL,conversation_id TEXT NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,source_id TEXT NOT NULL,title TEXT NOT NULL,mode TEXT NOT NULL,status TEXT NOT NULL,error TEXT,created REAL NOT NULL,updated REAL NOT NULL);
        CREATE TABLE IF NOT EXISTS translation_parts(translation_id TEXT NOT NULL REFERENCES translations(id) ON DELETE CASCADE,position INTEGER NOT NULL,page INTEGER NOT NULL,source_text TEXT NOT NULL,translated TEXT NOT NULL DEFAULT '',status TEXT NOT NULL DEFAULT 'pending',model TEXT,PRIMARY KEY(translation_id,position));
        CREATE TABLE IF NOT EXISTS translation_checks(translation_id TEXT NOT NULL REFERENCES translations(id) ON DELETE CASCADE,position INTEGER NOT NULL,report TEXT NOT NULL,candidate TEXT NOT NULL DEFAULT '',PRIMARY KEY(translation_id,position));
        CREATE TABLE IF NOT EXISTS translation_guidance(translation_id TEXT PRIMARY KEY REFERENCES translations(id) ON DELETE CASCADE,version INTEGER NOT NULL,terms TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS messages(id INTEGER PRIMARY KEY,conversation_id TEXT NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,role TEXT NOT NULL,content TEXT NOT NULL,sources TEXT NOT NULL DEFAULT '[]',created REAL NOT NULL);
        CREATE TABLE IF NOT EXISTS jobs(id TEXT PRIMARY KEY,user_id TEXT NOT NULL,conversation_id TEXT NOT NULL REFERENCES conversations(id),mode TEXT NOT NULL,status TEXT NOT NULL,answer TEXT NOT NULL DEFAULT '',sources TEXT NOT NULL DEFAULT '[]',error TEXT,created REAL NOT NULL,updated REAL NOT NULL);
        CREATE TABLE IF NOT EXISTS feedback(id TEXT PRIMARY KEY,user_id TEXT,content TEXT NOT NULL,view TEXT,created REAL NOT NULL);
        CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY,value TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS guide_meta(path TEXT PRIMARY KEY,title TEXT,language TEXT,provenance TEXT,licence TEXT);
        CREATE TABLE IF NOT EXISTS guide_search_domains(id TEXT PRIMARY KEY,domains TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS guide_dates(path TEXT PRIMARY KEY,document_date TEXT NOT NULL DEFAULT '',edition TEXT NOT NULL DEFAULT '',collected_at TEXT NOT NULL DEFAULT '');
        CREATE VIRTUAL TABLE IF NOT EXISTS documents USING fts5(id UNINDEXED,title,url UNINDEXED,language UNINDEXED,text,tokenize='unicode61 remove_diacritics 2');
        CREATE VIRTUAL TABLE IF NOT EXISTS passages USING fts5(id UNINDEXED,title,url UNINDEXED,language UNINDEXED,text,tokenize='unicode61 remove_diacritics 2');
        ''')
        db.execute("UPDATE translations SET status='paused',error='Le service a redémarré. Reprenez la traduction pour continuer.',updated=? WHERE status IN ('queued','running')",(time.time(),))
        columns={row['name'] for row in db.execute('PRAGMA table_info(messages)')}
        for column in ('model','mode'):
            if column not in columns:db.execute('ALTER TABLE messages ADD COLUMN '+column+' TEXT')
        db.execute("UPDATE jobs SET status='interrupted',error='Le service a redémarré. Vous pouvez relancer la question.',updated=? WHERE status IN ('queued','running')", (time.time(),))

    # Optional schema cannot roll back or prevent the core initialization.
    schemas={
        'summaries':[
            "CREATE TABLE IF NOT EXISTS summary_jobs(id TEXT PRIMARY KEY,user_id TEXT NOT NULL,conversation_id TEXT NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,question TEXT NOT NULL,mode TEXT NOT NULL,status TEXT NOT NULL,error TEXT,created REAL NOT NULL,updated REAL NOT NULL,answer TEXT NOT NULL DEFAULT '',message_id INTEGER REFERENCES messages(id) ON DELETE SET NULL)",
            "CREATE TABLE IF NOT EXISTS summary_inputs(summary_id TEXT NOT NULL REFERENCES summary_jobs(id) ON DELETE CASCADE,number INTEGER NOT NULL,source_id TEXT NOT NULL,title TEXT NOT NULL,metadata TEXT NOT NULL DEFAULT '{}',status TEXT NOT NULL DEFAULT 'pending',error TEXT,PRIMARY KEY(summary_id,number))",
            "CREATE TABLE IF NOT EXISTS summary_parts(summary_id TEXT NOT NULL REFERENCES summary_jobs(id) ON DELETE CASCADE,position INTEGER NOT NULL,source_number INTEGER NOT NULL,page INTEGER NOT NULL,offset INTEGER NOT NULL,text TEXT NOT NULL,status TEXT NOT NULL DEFAULT 'pending',PRIMARY KEY(summary_id,position))",
            "CREATE TABLE IF NOT EXISTS summary_nodes(summary_id TEXT NOT NULL REFERENCES summary_jobs(id) ON DELETE CASCADE,id INTEGER NOT NULL,level INTEGER NOT NULL,children TEXT NOT NULL,result TEXT NOT NULL,model TEXT NOT NULL,parent INTEGER,PRIMARY KEY(summary_id,id))",
            "UPDATE summary_jobs SET status='paused',error='Le service a redémarré. Reprenez la synthèse pour continuer.' WHERE status IN ('queued','running','preparing')"],
        'associations':[
            'CREATE TABLE IF NOT EXISTS conversation_document_choices(conversation_id TEXT NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,source_id TEXT NOT NULL,title TEXT NOT NULL,position INTEGER NOT NULL,PRIMARY KEY(conversation_id,source_id))'],
        'documentary':[
            "CREATE TABLE IF NOT EXISTS documentary_evidence(job_id TEXT PRIMARY KEY,conversation_id TEXT NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,message_id INTEGER UNIQUE REFERENCES messages(id) ON DELETE CASCADE,summary TEXT NOT NULL,sources TEXT NOT NULL DEFAULT '[]')",
            'CREATE INDEX IF NOT EXISTS documentary_conversation ON documentary_evidence(conversation_id)'],
        'favorites':[
            'CREATE TABLE IF NOT EXISTS favorites(user_id TEXT NOT NULL,source_id TEXT NOT NULL,title TEXT NOT NULL,url TEXT NOT NULL,language TEXT NOT NULL,created REAL NOT NULL,PRIMARY KEY(user_id,source_id))',
            "CREATE VIRTUAL TABLE IF NOT EXISTS favorite_articles USING fts5(user_id UNINDEXED,id UNINDEXED,title,url UNINDEXED,language UNINDEXED,text,tokenize='unicode61 remove_diacritics 2')"],
        'publications':[
            'CREATE TABLE IF NOT EXISTS translation_publications(translation_id TEXT PRIMARY KEY,user_id TEXT NOT NULL,source_id TEXT NOT NULL,title TEXT NOT NULL,source_meta TEXT NOT NULL,auto_publish INTEGER NOT NULL DEFAULT 0,published_path TEXT UNIQUE,published_at REAL,error TEXT)']}
    for feature,statements in schemas.items():
        try:
            with connect() as db:
                for statement in statements:db.execute(statement)
        except Exception:
            import logging
            logging.getLogger(__name__).warning('Initialisation de %s indisponible ; état principal conservé.',feature)


def canonical(code):
    return ''.join(ch for ch in str(code).upper() if ch.isalnum())


def code_digest(code, salt):
    return hashlib.pbkdf2_hmac('sha256', canonical(code).encode(), bytes.fromhex(salt), 310000).hex()


def recovery_code(user_id):
    raw = secrets.token_hex(16).upper()
    code = '-'.join(raw[i:i+4] for i in range(0, len(raw), 4))
    salt = secrets.token_hex(16)
    with connect() as db:
        db.execute('INSERT OR REPLACE INTO recovery VALUES(?,?,?,0)', (user_id, salt, code_digest(code, salt)))
    return code


def consume_code(user_id, code):
    with connect() as db:
        row = db.execute('SELECT * FROM recovery WHERE user_id=?', (user_id,)).fetchone()
        if not row or row['used']:
            return False
        digest = code_digest(code, row['salt'])
        if not hmac.compare_digest(digest, row['digest']):
            return False
        result = db.execute('UPDATE recovery SET used=1 WHERE user_id=? AND digest=? AND used=0', (user_id, digest))
        return result.rowcount == 1


def limit(key, maximum=5, period=900):
    now = time.time()
    with connect() as db:
        db.execute('BEGIN IMMEDIATE')
        row = db.execute('SELECT * FROM limits WHERE key=?', (key,)).fetchone()
        count = row['count'] if row and row['until'] > now else 0
        until = row['until'] if row and row['until'] > now else now + period
        if count >= maximum:
            return False
        db.execute('INSERT OR REPLACE INTO limits VALUES(?,?,?)', (key, count+1, until))
        return True


def new_id():
    return str(uuid.uuid4())


def owned_conversation(identifier, user_id):
    with connect() as db:
        row = db.execute('SELECT * FROM conversations WHERE id=? AND user_id=?', (identifier,user_id)).fetchone()
        return dict(row) if row else None


def messages(identifier):
    with connect() as db:
        rows=[{**dict(row),'sources':json.loads(row['sources'])} for row in db.execute('SELECT * FROM messages WHERE conversation_id=? ORDER BY id', (identifier,))]
    from . import documentary
    recorded=documentary.for_messages(identifier)
    return [{**row,**({'documentary':recorded[row['id']]} if row['id'] in recorded else {})} for row in rows]


def conversation_source(identifier):
    with connect() as db:
        row=db.execute('SELECT source_id AS id,title FROM conversation_sources WHERE conversation_id=?',(identifier,)).fetchone()
    return dict(row) if row else None


def set_conversation_source(db,identifier,source):
    if source:
        db.execute('INSERT INTO conversation_sources VALUES(?,?,?) ON CONFLICT(conversation_id) DO UPDATE SET source_id=excluded.source_id,title=excluded.title',(identifier,source['id'],source['title']))
    else:db.execute('DELETE FROM conversation_sources WHERE conversation_id=?',(identifier,))
    try:db.execute('DELETE FROM conversation_document_choices WHERE conversation_id=?',(identifier,))
    except sqlite3.OperationalError:pass # Legacy single-document use remains available.


class AssociationUnavailable(RuntimeError):pass


def conversation_source_choices(identifier,db=None):
    if db is None:
        with connect() as connection:return conversation_source_choices(identifier,connection)
    primary=db.execute('SELECT source_id AS id,title FROM conversation_sources WHERE conversation_id=?',(identifier,)).fetchone()
    if not primary:return []
    try:rows=[dict(row) for row in db.execute('SELECT source_id AS id,title FROM conversation_document_choices WHERE conversation_id=? ORDER BY position',(identifier,))]
    except sqlite3.OperationalError:rows=[]
    # A rollback can leave the new table intact while an old client changes the
    # legacy association. Never resurrect choices after that explicit change.
    if not rows or rows[0]['id']!=primary['id']:return [dict(primary)]
    return [dict(primary),*rows[1:]]


def set_conversation_source_choices(db,identifier,sources):
    sources=list({source['id']:source for source in sources}.values())
    if len(sources)>12:raise ValueError('Douze documents au maximum par conversation.')
    if len(sources)>1 and not db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='conversation_document_choices'").fetchone():
        raise AssociationUnavailable('La sélection de plusieurs documents est momentanément indisponible.')
    set_conversation_source(db,identifier,sources[0] if sources else None)
    if len(sources)>1:
        db.executemany('INSERT INTO conversation_document_choices VALUES(?,?,?,?)',[(identifier,source['id'],source['title'],position) for position,source in enumerate(sources)])


def add_conversation_source(db,identifier,source):
    # Starting a translation chooses its source without discarding the others.
    choices=conversation_source_choices(identifier,db)
    ordered=[source,*[item for item in choices if item['id']!=source['id']]]
    if len(ordered)>12:raise ValueError('Retirez un document de la sélection avant d’en ajouter un autre.')
    try:set_conversation_source_choices(db,identifier,ordered)
    except AssociationUnavailable:set_conversation_source(db,identifier,source)


def summary_active(db,conversation):
    try:return bool(db.execute("SELECT 1 FROM summary_jobs WHERE conversation_id=? AND status IN ('queued','running','preparing')",(conversation,)).fetchone())
    except sqlite3.OperationalError:return False


def conversation_summaries(conversation):
    try:
        with connect() as db:return [dict(row) for row in db.execute('SELECT id,status,created FROM summary_jobs WHERE conversation_id=? ORDER BY created DESC LIMIT 20',(conversation,))]
    except sqlite3.OperationalError:return []
