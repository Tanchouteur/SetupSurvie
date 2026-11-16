"""Optional profile-owned folders. Legacy conversation IDs and tables stay intact."""
from fastapi import HTTPException
from . import store


def initialize(db):
    db.execute('CREATE TABLE IF NOT EXISTS conversation_folders(id TEXT PRIMARY KEY,user_id TEXT NOT NULL,name TEXT NOT NULL,created REAL NOT NULL)')
    db.execute('CREATE TABLE IF NOT EXISTS conversation_filing(conversation_id TEXT PRIMARY KEY REFERENCES conversations(id) ON DELETE CASCADE,folder_id TEXT REFERENCES conversation_folders(id) ON DELETE SET NULL)')


def folders(owner):
    with store.connect() as db:
        initialize(db)
        rows=db.execute('SELECT f.*,count(c.id) AS count FROM conversation_folders f LEFT JOIN conversation_filing x ON x.folder_id=f.id LEFT JOIN conversations c ON c.id=x.conversation_id AND c.user_id=f.user_id WHERE f.user_id=? GROUP BY f.id ORDER BY f.name COLLATE NOCASE,f.created',(owner,)).fetchall()
        return {'folders':[dict(row) for row in rows]}


def name(value):
    value=value.strip()
    if not value:raise HTTPException(400,'Donnez un nom au dossier.')
    return value


def save_folder(owner,label,identifier=None):
    import time
    label=name(label)
    with store.connect() as db:
        initialize(db)
        if identifier:
            if not db.execute('UPDATE conversation_folders SET name=? WHERE id=? AND user_id=?',(label,identifier,owner)).rowcount:raise HTTPException(404,'Dossier introuvable.')
        else:
            identifier=store.new_id()
            db.execute('INSERT INTO conversation_folders VALUES(?,?,?,?)',(identifier,owner,label,time.time()))
    return {'id':identifier,'name':label}


def delete_folder(owner,identifier):
    with store.connect() as db:
        initialize(db)
        if not db.execute('DELETE FROM conversation_folders WHERE id=? AND user_id=?',(identifier,owner)).rowcount:raise HTTPException(404,'Dossier introuvable.')
    return {'ok':True,'notice':'Dossier supprimé. Les conversations sont conservées dans Sans dossier.'}


def move(owner,conversation,folder):
    with store.connect() as db:
        initialize(db)
        if not db.execute('SELECT 1 FROM conversations WHERE id=? AND user_id=?',(conversation,owner)).fetchone():raise HTTPException(404,'Conversation introuvable.')
        if folder and not db.execute('SELECT 1 FROM conversation_folders WHERE id=? AND user_id=?',(folder,owner)).fetchone():raise HTTPException(404,'Dossier introuvable.')
        db.execute('INSERT INTO conversation_filing VALUES(?,?) ON CONFLICT(conversation_id) DO UPDATE SET folder_id=excluded.folder_id',(conversation,folder))
    return {'ok':True}


def rename(owner,conversation,title):
    title=name(title)
    with store.connect() as db:
        if not db.execute('UPDATE conversations SET title=? WHERE id=? AND user_id=?',(title,conversation,owner)).rowcount:raise HTTPException(404,'Conversation introuvable.')
        db.execute('INSERT OR REPLACE INTO settings VALUES(?,?)',('conversation-title:'+conversation,'manual'))
    return {'ok':True,'title':title}


def listing(owner,q='',folder=None,offset=0):
    with store.connect() as db:
        initialize(db)
        where=['c.user_id=?'];args=[owner]
        if folder is not None and folder!='all':
            where.append('x.folder_id IS NULL' if folder=='unfiled' else 'x.folder_id=?')
            if folder!='unfiled':args.append(folder)
        if q.strip():
            pattern='%'+q.strip().replace('\\','\\\\').replace('%','\\%').replace('_','\\_')+'%'
            where.append("(c.title LIKE ? ESCAPE '\\' OR EXISTS(SELECT 1 FROM messages m WHERE m.conversation_id=c.id AND m.content LIKE ? ESCAPE '\\'))")
            args.extend([pattern,pattern])
        rows=db.execute('SELECT c.*,x.folder_id FROM conversations c LEFT JOIN conversation_filing x ON x.conversation_id=c.id WHERE '+' AND '.join(where)+' ORDER BY c.created DESC,c.id LIMIT 101 OFFSET ?',(*args,offset)).fetchall()
        return {'conversations':[dict(row) for row in rows[:100]],'has_more':len(rows)>100}
