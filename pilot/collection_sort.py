"""Persistent collection selection shared by search, the host and installers."""
from dataclasses import dataclass
import hashlib
import json
import sqlite3
import stat
from pathlib import Path, PurePosixPath
import re

from . import durable

FILENAME = 'collection-sort.json'
KIND = 'SetupSurvie collection sort'
MAX_SIZE = 256_000
KEY = re.compile(r'(?:zim:[a-z0-9][a-z0-9_.-]{0,219}|video:[a-f0-9]{64})')
DATE = re.compile(r'_\d{4}-\d{2}(?:-\d{2})?[a-z]?$')


def archive(reference):
    name = PurePosixPath(reference).name.lower().removesuffix('.part').removesuffix('.zim')
    name = DATE.sub('', name)
    return 'zim:' + re.sub(r'_(maxi|nopic|mini)$', '', name)


def path_key(relative):
    if relative.startswith('library/zim/') and relative.endswith('.zim'):
        return archive(relative)
    return ''


def video(payload):
    if payload.get('provider') == 'zim':
        return archive(payload.get('archive') or '')
    source = payload.get('source') or {}
    label = source.get('channel') or payload.get('collection') or '.'
    label = ' '.join(label.casefold().split())
    return 'video:' + hashlib.sha256(label.encode('utf-8')).hexdigest()


@dataclass(frozen=True)
class Sort:
    other: frozenset = frozenset()
    excluded: frozenset = frozenset()

    def as_json(self):
        return {'schema': 1, 'kind': KIND, 'other': sorted(self.other), 'excluded': sorted(self.excluded)}

    def state(self, key):
        if key in self.excluded:
            return 'excluded'
        return 'other' if key in self.other else 'main'

    def permits(self, key, domain):
        state = self.state(key)
        if state == 'excluded':
            return False
        if domain == 'other':
            return state == 'other'
        return domain == 'all' or state == 'main'

    def change(self, keys, state):
        keys = frozenset(keys)
        return Sort((self.other - keys) | (keys if state == 'other' else frozenset()),
                    (self.excluded - keys) | (keys if state == 'excluded' else frozenset()))


def parse(value):
    error = 'Fichier de tri SetupSurvie non valide.'
    if not isinstance(value, dict) or type(value.get('schema')) is not int or value.get('schema') != 1 or value.get('kind') != KIND:
        raise ValueError(error)
    lists = []
    for field in ('other', 'excluded'):
        items = value.get(field)
        if not isinstance(items, list) or len(items) > 1200 or any(not isinstance(k, str) or not KEY.fullmatch(k) for k in items):
            raise ValueError(error)
        lists.append(frozenset(items))
    if lists[0] & lists[1]:
        raise ValueError('Une collection figure dans les deux listes du fichier de tri.')
    return Sort(*lists)


def read_file(path):
    with Path(path).open('rb') as stream:
        data = stream.read(MAX_SIZE + 1)
    if len(data) > MAX_SIZE:
        raise ValueError('Le fichier de tri est trop volumineux.')
    return parse(json.loads(data))


def load(directory):
    try:
        return read_file(Path(directory) / FILENAME)
    except FileNotFoundError:
        return Sort()


def save(directory, selection):
    value=selection.as_json()
    parse(value)
    payload=json.dumps(value,ensure_ascii=False,indent=2).encode('utf-8')
    if len(payload)>MAX_SIZE:raise ValueError('Le fichier de tri est trop volumineux.')
    durable.write_bytes(Path(directory) / FILENAME,payload)


def archive_files(directory):
    for path in sorted(Path(directory).glob('*')):
        if not path.name.endswith(('.zim', '.zim.part')) or not KEY.fullmatch(archive(path.name)):
            continue
        try:
            info = path.lstat()
        except FileNotFoundError:
            continue
        if stat.S_ISREG(info.st_mode) and not getattr(info, 'st_file_attributes', 0) & 0x400:
            yield path, info


def video_files(directory, database):
    directory = Path(directory)
    if not database.is_file():
        return
    with sqlite3.connect(database.resolve().as_uri()+'?mode=ro',uri=True) as db:
        rows = db.execute("SELECT payload FROM media WHERE json_extract(payload,'$.provider') IS NOT 'zim'").fetchall()
    for (serialized,) in rows:
        payload = json.loads(serialized)
        relative = payload.get('path')
        if not isinstance(relative,str):
            continue
        source = PurePosixPath(relative)
        if source.suffix.lower() not in ('.avi','.flv','.m4v','.mkv','.mov','.mp4','.mpeg','.mpg','.ogv','.webm','.wmv','.ts','.3gp'):
            continue
        key = video(payload)
        label = (payload.get('source') or {}).get('channel') or payload.get('collection') or '.'
        relatives = [relative,source.with_suffix('.info.json').as_posix()]
        for track in payload.get('tracks',[]):
            name = track.get('path')
            if not isinstance(name,str) or any(track.get(flag) for flag in ('prepared_job','transcription_job','acquired_job','archive_cache')):
                continue
            subtitle = PurePosixPath(name)
            if subtitle.parent==source.parent and subtitle.name.startswith(source.stem+'.') and subtitle.suffix.lower() in ('.srt','.vtt'):
                relatives.append(name)
        for name in relatives:
            if '\\\\' in name or ':' in name or any(part in ('','.','..') for part in name.split('/')):
                continue
            path=directory/name
            try:
                if not path.resolve().is_relative_to(directory.resolve()):
                    continue
                info=path.lstat()
            except OSError:
                continue
            if stat.S_ISREG(info.st_mode) and not getattr(info,'st_file_attributes',0)&0x400:
                yield key,label,path,info


def deletion_preview(archives, keys, *, video_dir=None, video_db=None):
    candidates=[(path,'library/zim/'+path.name,info) for path,info in archive_files(archives)
                if archive(path.name) in keys]
    if any(key.startswith('video:') for key in keys):
        candidates.extend((path,'library/video/'+path.relative_to(video_dir).as_posix(),info)
                          for key,_,path,info in video_files(video_dir,video_db) if key in keys)
    files=[{'name':name,'bytes':info.st_size,'mtime_ns':info.st_mtime_ns,
            'identity':[info.st_dev,info.st_ino]} for name,info in sorted({name:info for _,name,info in candidates}.items())]
    token=hashlib.sha256(json.dumps([sorted(keys),files],ensure_ascii=True).encode()).hexdigest()
    return {'files':files,'bytes':sum(item['bytes'] for item in files),'token':token}
