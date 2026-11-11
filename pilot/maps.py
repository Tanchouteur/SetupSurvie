"""Public, read-only access to verified offline map archives."""
import json
import os
from pathlib import Path
import re

from fastapi import HTTPException

ROOT=Path(os.environ.get('MAPS_DIR','/maps'))


def available():
    manifest=ROOT/'manifest.json'
    if not manifest.is_file() or manifest.is_symlink() or manifest.stat().st_size>100_000:return []
    try:items=json.loads(manifest.read_text())['maps']
    except (OSError,ValueError,KeyError,TypeError):return []
    result=[]
    for item in items:
        try:
            name=item['path'];identifier=item['id']
            if not re.fullmatch(r'[a-z0-9-]+',identifier) or not re.fullmatch(r'[a-z0-9-]+\.pmtiles',name):continue
            path=ROOT/name
            if not path.is_file() or path.is_symlink() or not path.resolve().is_relative_to(ROOT.resolve()):continue
            if path.stat().st_size!=item['bytes'] or not re.fullmatch(r'[a-f0-9]{64}',item['sha256']):continue
            with path.open('rb') as stream:
                if stream.read(8)!=b'PMTiles\x03':continue
            result.append({**item,'url':'/api/maps/'+identifier+'/archive'})
        except (OSError,ValueError,KeyError,TypeError):continue
    return result


def archive(identifier):
    item=next((m for m in available() if m['id']==identifier),None)
    if item is None:raise HTTPException(404,'Cette carte n’est pas encore disponible hors ligne.')
    return ROOT/item['path']
