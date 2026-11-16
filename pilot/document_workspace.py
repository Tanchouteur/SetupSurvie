"""Find a profile's saved work by original, without reading texts or launching AI."""
from . import store,catalogue


def work(owner,source):
    source=catalogue.canonical(source.split('#page=')[0])
    pattern=source.replace('\\','\\\\').replace('%','\\%').replace('_','\\_')+'#page=%'
    with store.connect() as db:
        translations=[dict(row) for row in db.execute("SELECT id,conversation_id,source_id,title,status,mode,created,updated FROM translations WHERE user_id=? AND (source_id=? OR source_id LIKE ? ESCAPE '\\') ORDER BY created DESC LIMIT 100",(owner,source,pattern))]
    return {'translations':translations}
