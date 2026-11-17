"""Check the isolated archive reader and SQLite before declaring them usable.

Standard library only until the explicit libzim import. No archive, network or model.
"""
import importlib.metadata
import json
import platform
import sqlite3
import struct
import sys

# libzim 3.13.1 ships wheels up to CPython 3.14 only; 4.1.0 provides an abi3
# wheel covering 3.11+. Existing installations keep their pinned reader.
LEGACY='3.13.1'
CURRENT='4.1.0'


def expected_version(info=None):
    info=sys.version_info if info is None else info
    return LEGACY if tuple(info[:2])<(3,15) else CURRENT


VERSION=expected_version()
MESSAGES={
    'reader_missing':'Le lecteur d’archives manque dans l’outil isolé. Choisissez Vérifier / réparer l’outil.',
    'reader_import':'Le lecteur installé ne parvient pas à se charger sur ce PC. Vérifiez ou réparez l’outil, puis transmettez le rapport si l’échec persiste.',
    'reader_version':'La version du lecteur ne correspond pas à celle prévue. Vérifiez ou réparez l’outil.',
    'reader_api':'Le lecteur ne fournit pas les fonctions attendues. Vérifiez ou réparez l’outil.',
    'fts5_unavailable':'Ce Python ne fournit pas la recherche SQLite nécessaire. Le rapport permet de vérifier son installation.',
    'probe_unavailable':'La vérification de l’outil n’a pas abouti. Les archives n’ont pas été modifiées.',
    'probe_timeout':'La vérification de l’outil a dépassé son délai. Les archives n’ont pas été modifiées.'}


def probe():
    result={'schema':1,'ok':False,'python':platform.python_version(),'bits':struct.calcsize('P')*8,'sqlite':sqlite3.sqlite_version}
    try:
        installed=importlib.metadata.version('libzim');result['libzim']=installed
        if installed!=VERSION:return {**result,'error':'reader_version'}
        from libzim.reader import Archive
    except (ModuleNotFoundError,importlib.metadata.PackageNotFoundError):return {**result,'error':'reader_missing'}
    except Exception:return {**result,'error':'reader_import'}
    if not all(hasattr(Archive,name) for name in ('has_fulltext_index','get_metadata')) or not any(hasattr(Archive,name) for name in ('get_entry_by_id','_get_entry_by_id')):return {**result,'error':'reader_api'}
    try:
        with sqlite3.connect(':memory:') as db:
            db.execute("CREATE VIRTUAL TABLE check_fts USING fts5(text,tokenize='unicode61 remove_diacritics 2')")
            db.execute('INSERT INTO check_fts VALUES(?)',('fictional fixture',))
            if db.execute('SELECT count(*) FROM check_fts WHERE check_fts MATCH ?',('fictional',)).fetchone()[0]!=1:raise ValueError()
    except Exception:return {**result,'error':'fts5_unavailable'}
    return {**result,'ok':True,'fts5':True}


if __name__=='__main__':
    try:result=probe()
    except Exception:result={'schema':1,'ok':False,'error':'probe_unavailable'}
    print(json.dumps(result,ensure_ascii=True))
    raise SystemExit(0 if result['ok'] else 1)
