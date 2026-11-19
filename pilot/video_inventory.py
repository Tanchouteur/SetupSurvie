#!/usr/bin/env python3
"""Inventaire local en lecture seule ; bibliothèque standard Python uniquement."""
import argparse
from datetime import datetime, timezone
import hashlib
import html
import json
import math
import os
from pathlib import Path
import re
import stat
import sys

VIDEO_EXTENSIONS = {'.mp4', '.mkv', '.webm', '.mov', '.avi', '.m4v', '.ogv', '.mpeg', '.mpg'}
SUBTITLE_EXTENSIONS = {'.srt', '.vtt'}
MAX_SIDECAR_BYTES = 8 * 1024 * 1024
INCOMPLETE = re.compile(r'(?:\.(?:part|ytdl|tmp|temp|download|crdownload)(?:[.-]|$)|\.f\d+\.[^.]+$)', re.I)
LANGUAGE = re.compile(r'^[a-zA-Z]{2,3}(?:[-_][a-zA-Z0-9]{2,8})*$')
STAMP = re.compile(r'(?:(\d{2,}):)?([0-5]\d):([0-5]\d)[.,](\d{3})$')


def revision(info):
    return {'size_bytes': info.st_size, 'mtime_ns': info.st_mtime_ns}


def is_link(path):
    info = path.lstat()
    return path.is_symlink() or bool(getattr(info, 'st_file_attributes', 0)
                                     & getattr(stat, 'FILE_ATTRIBUTE_REPARSE_POINT', 0))


def regular(path):
    """Do not follow links (including Windows junctions where detectable)."""
    info = path.lstat()
    if is_link(path):
        raise ValueError('lien_exclu')
    if not stat.S_ISREG(info.st_mode):
        raise ValueError('fichier_non_ordinaire')
    return info


def read_sidecar(path):
    before = regular(path)
    with path.open('rb') as stream:
        data = stream.read(MAX_SIDECAR_BYTES + 1)
    if len(data) > MAX_SIDECAR_BYTES:
        raise ValueError('fichier_annexe_trop_gros')
    if revision(before) != revision(regular(path)):
        raise ValueError('fichier_modifie_pendant_lecture')
    return data.decode('utf-8-sig'), revision(before)


def timestamp(value):
    match = STAMP.fullmatch(value)
    if not match:
        raise ValueError('horodatage_invalide')
    hours, minutes, seconds, millis = match.groups()
    return int(hours or 0) * 3600 + int(minutes) * 60 + int(seconds) + int(millis) / 1000


def inspect_subtitle(path, duration=None, *, include_cues=False):
    try:content, rev = read_sidecar(path)
    except (OSError, ValueError, UnicodeError) as exc:
        result={'format':path.suffix.lower()[1:],'technical_status':'invalid','errors':[str(exc) if not isinstance(exc,OSError) else 'lecture_impossible'],
            'warnings':[],'cue_count':0,'language_verified':False,'synchronization_verified':False,'translation_verified':False}
        if include_cues:result['cues']=[]
        return result
    return inspect_subtitle_text(content,path.suffix,duration,include_cues=include_cues,source_revision=rev)


def inspect_subtitle_text(content, format, duration=None, *, include_cues=False, source_revision=None):
    """Conservative structural checks, never a language or playback validation."""
    result = {'format': format.lower().lstrip('.'), 'technical_status': 'invalid',
              'errors': [], 'warnings': [], 'cue_count': 0,
              'language_verified': False, 'synchronization_verified': False,
              'translation_verified': False}
    cues=[]
    try:
        if source_revision is not None:result['revision'] = source_revision
        result['text_utf8_sha256'] = hashlib.sha256(content.encode('utf-8')).hexdigest()
        if '\x00' in content:
            raise ValueError('caractere_nul')
        content = content.replace('\r\n', '\n').replace('\r', '\n').strip()
        blocks = re.split(r'\n[ \t]*\n', content) if content else []
        vtt = format.lower().lstrip('.') == 'vtt'
        if vtt:
            if not blocks or not re.match(r'^WEBVTT(?:[ \t].*)?(?:\n|$)', blocks[0]):
                raise ValueError('entete_webvtt_manquante')
            # Header metadata is allowed, but a cue must be separated by a blank line.
            if '-->' in blocks[0]:
                raise ValueError('entete_webvtt_non_separee')
            blocks = blocks[1:]
        ends, previous_start, previous_end, gaps = [], None, None, []
        for number, block in enumerate(blocks, 1):
            lines = block.splitlines()
            if not lines:
                continue
            if vtt and (re.match(r'^NOTE(?:[ \t]|$)', lines[0]) or lines[0] in {'STYLE', 'REGION'}):
                continue
            try:
                if not vtt and not lines[0].strip().isdigit():
                    raise ValueError('numero_srt_manquant')
                if '-->' not in lines[0]:
                    lines = lines[1:]
                if not lines or '-->' not in lines[0]:
                    raise ValueError('intervalle_manquant')
                left, right = lines[0].split('-->')
                end_fields = right.strip().split()
                if not end_fields or (not vtt and len(end_fields) != 1):
                    raise ValueError('intervalle_invalide')
                pattern = r'\d{2,}:[0-5]\d:[0-5]\d,\d{3}' if not vtt else r'(?:\d{2,}:)?[0-5]\d:[0-5]\d\.\d{3}'
                if not re.fullmatch(pattern, left.strip()) or not re.fullmatch(pattern, end_fields[0]):
                    raise ValueError('horodatage_invalide_pour_format')
                start, end = timestamp(left.strip()), timestamp(end_fields[0])
                if end <= start:
                    raise ValueError('temps_inverses_ou_nuls')
                text = html.unescape(re.sub(r'<[^>]*>', '', '\n'.join(lines[1:]))).strip()
                if not text:
                    raise ValueError('segment_vide')
                if previous_start is not None and start < previous_start:
                    result['errors'].append(f'segment_{number}:ordre_invalide')
                if previous_end is not None and start < previous_end:
                    result['errors'].append(f'segment_{number}:chevauchement')
                if previous_end is not None and start > previous_end:
                    gaps.append({'start': previous_end, 'end': start})
                if duration is not None and end > duration:
                    result['errors'].append(f'segment_{number}:depasse_duree_declaree')
                previous_start, previous_end = start, end
                ends.append(end)
                result['cue_count'] += 1
                if include_cues:cues.append({'start_ms':round(start*1000),'end_ms':round(end*1000),'text':text})
            except (ValueError, IndexError) as exc:
                result['errors'].append(f'segment_{number}:{exc}')
        if not ends:
            result['errors'].append('aucun_segment_exploitable')
        result['last_end_seconds'] = max(ends) if ends else None
        result['gap_count'] = len(gaps)
        result['gaps_sample'] = gaps[:20]
        if gaps:
            result['warnings'].append('intervalles_sans_texte_paroles_non_verifiees')
        if duration is None:
            result['warnings'].append('duree_media_inconnue')
        result['technical_status'] = 'passed' if not result['errors'] else 'invalid'
    except (OSError, ValueError, UnicodeError) as exc:
        result['errors'].append(str(exc) if not isinstance(exc, OSError) else 'lecture_impossible')
    if include_cues:result['cues']=cues if result['technical_status']=='passed' else []
    return result


def positive_number(value):
    if type(value) is int:
        return value if value > 0 else None
    return value if type(value) is float and math.isfinite(value) and value > 0 else None


def text_field(data, key):
    value = data.get(key)
    return value.strip() if isinstance(value, str) and value.strip() else None


def metadata(path):
    result = {'path': path.name, 'status': 'missing', 'errors': []}
    data = {}
    try:
        content, rev = read_sidecar(path)
        data = json.loads(content)
        # Reject escaped lone surrogates before they can break UTF-8 export.
        json.dumps(data, ensure_ascii=False).encode('utf-8')
        if not isinstance(data, dict):
            raise ValueError('objet_json_attendu')
        result.update(status='read', revision=rev)
    except FileNotFoundError:
        pass
    except (OSError, ValueError, UnicodeError, RecursionError):
        result.update(status='invalid', errors=['metadonnees_illisibles_ou_invalides'])
        data = {}
    return result, data


def language_from_name(video, subtitle):
    tag = subtitle.stem[len(video.stem):].lstrip('.')
    return tag.replace('_', '-').lower() if LANGUAGE.fullmatch(tag) else None


def track_origin(data, language, subtitle):
    """Only attribute origin when the local request can be linked unambiguously."""
    requested = data.get('requested_subtitles')
    if not isinstance(requested, dict):
        return 'unknown'
    for lang, entry in requested.items():
        if not isinstance(entry, dict) or lang.replace('_', '-').lower() != language:
            continue
        filename = entry.get('filepath')
        if filename and (not isinstance(filename, str) or re.split(r'[/\\]', filename)[-1] != subtitle.name):
            continue
        url = entry.get('url')
        if not isinstance(url, str):
            continue
        matches = []
        for field, origin in [('subtitles', 'provided'), ('automatic_captions', 'automatic')]:
            tracks = data.get(field)
            entries = tracks.get(lang, []) if isinstance(tracks, dict) else []
            if isinstance(entries, list) and any(isinstance(t, dict) and t.get('url') == url for t in entries):
                matches.append(origin)
        if len(matches) == 1:
            return matches[0]
    return 'unknown'


def advertised_languages(data, key):
    value = data.get(key)
    return sorted(k for k in value if isinstance(k, str)) if isinstance(value, dict) else []


def inspect_video(path, root, siblings, video_stems, hash_media=False):
    before = regular(path)
    if before.st_size == 0:
        raise ValueError('media_vide')
    relative = path.relative_to(root).as_posix()
    info, data = metadata(path.with_suffix('.info.json'))
    info['path'] = path.with_suffix('.info.json').relative_to(root).as_posix()
    duration = positive_number(data.get('duration'))
    source_language = text_field(data, 'language')
    if source_language:
        source_language = source_language.replace('_', '-').lower()
    source_id = text_field(data, 'id')
    extractor = text_field(data, 'extractor_key') or text_field(data, 'extractor')
    source_key = f'{extractor}:{source_id}' if extractor and source_id else None
    tracks = []
    for subtitle in siblings:
        if subtitle.suffix.lower() not in SUBTITLE_EXTENSIONS or INCOMPLETE.search(subtitle.name):
            continue
        # Longest media stem wins: 'cours.en.srt' belongs to 'cours.en.mp4' if present.
        owners = [stem for stem in video_stems if subtitle.stem == stem or subtitle.stem.startswith(stem + '.')]
        if not owners or max(owners, key=len) != path.stem:
            continue
        language = language_from_name(path, subtitle)
        track = {'path': subtitle.relative_to(root).as_posix(), 'language_declared': language,
                 'language_basis': 'filename' if language else 'unknown',
                 'origin': track_origin(data, language, subtitle),
                 **inspect_subtitle(subtitle, duration)}
        tracks.append(track)
    usable = [t for t in tracks if t['technical_status'] == 'passed']
    french = [t for t in usable if t['language_declared'] and t['language_declared'].split('-')[0] == 'fr']
    source = [t for t in usable if source_language and t['language_declared'] == source_language]
    if french:
        status, action = 'french_available', 'Vérifier la langue, le sens et la synchronisation de la piste française en lecture locale.'
    elif source:
        status, action = 'source_only', 'Examiner les pistes françaises annoncées ; sinon préparer une traduction de la piste source, puis la contrôler.'
    elif usable:
        status, action = 'unknown', 'Identifier la langue des pistes et la langue parlée avant de choisir une traduction.'
    elif tracks:
        status, action = 'invalid', 'Examiner les erreurs et récupérer une piste exploitable ; conserver les originaux.'
    else:
        status, action = 'missing', 'Examiner les pistes françaises puis source disponibles ; sinon envisager une transcription locale.'
    digest = None
    if hash_media:
        hasher = hashlib.sha256()
        with path.open('rb') as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b''):
                hasher.update(chunk)
        digest = hasher.hexdigest()
    if revision(before) != revision(regular(path)):
        raise ValueError('media_modifie_pendant_inventaire')
    unknowns = ['audio_non_verifie', 'lecture_media_non_verifiee', 'synchronisation_non_verifiee',
                'sens_traduction_non_verifie', 'couverture_paroles_non_verifiee', 'droits_usage_non_verifies']
    for field, value in [('source', source_key), ('duree', duration), ('langue_source', source_language),
                         ('chaine', text_field(data, 'channel')), ('revision_contenu', digest)]:
        if value is None:
            unknowns.append(field + '_inconnue')
    if any(t['origin'] == 'unknown' for t in tracks):
        unknowns.append('origine_pistes_inconnue')
    if any(not t['language_declared'] for t in tracks):
        unknowns.append('langue_pistes_inconnue')
    if info['status'] != 'read':
        unknowns.append('metadonnees_absentes_ou_invalides')
    return {
        'schema_version': 1,
        'inventory_id': hashlib.sha256(relative.encode('utf-8')).hexdigest(),
        'path': relative, 'collection': path.parent.relative_to(root).as_posix(),
        'title': text_field(data, 'title') or path.stem,
        'title_basis': 'info_json' if text_field(data, 'title') else 'filename',
        'source': {'id': source_id, 'extractor': extractor, 'key': source_key,
                   'url': text_field(data, 'webpage_url'), 'channel': text_field(data, 'channel'),
                   'upload_date_declared': text_field(data, 'upload_date')},
        'description': text_field(data, 'description'),
        'media': {'present': True, 'completion': 'presumed_from_filename',
                  'format': path.suffix.lower()[1:], 'revision_stat': revision(before),
                  'sha256': digest, 'duration_seconds_declared': duration,
                  'language_declared': source_language, 'audio_present': None,
                  'height_declared': positive_number(data.get('height'))},
        'metadata': info, 'tracks': tracks,
        'remote_tracks_advertised_only': {
            'provided': advertised_languages(data, 'subtitles'),
            'automatic': advertised_languages(data, 'automatic_captions')},
        'subtitle_status': status, 'next_action': action, 'unknowns': unknowns,
        'validation': {'translation': 'not_verified', 'synchronization': 'not_verified',
                       'human_review': 'not_performed', 'missing_parts': 'unknown'},
    }


def inventory(root, hash_media=False, *, cancelled=None):
    root = Path(root).resolve(strict=True)
    if not root.is_dir():
        raise ValueError('Le dossier vidéo doit être un répertoire.')
    reports, skipped, errors, sidecars, unexamined = [], [], [], [], []

    def walk_error(exc):
        errors.append({'path': os.path.relpath(exc.filename, root), 'reason': 'repertoire_illisible'})

    for directory, dirs, files in os.walk(root, followlinks=False, onerror=walk_error):
        if cancelled and cancelled():raise InterruptedError('Inventaire interrompu.')
        parent = Path(directory)
        for name in list(dirs):
            child = parent / name
            try:
                reason = 'lien_exclu' if is_link(child) else (
                    'repertoire_telechargement_incomplet' if INCOMPLETE.search(name) else None)
            except OSError:
                dirs.remove(name)
                errors.append({'path': child.relative_to(root).as_posix(), 'reason': 'repertoire_illisible'})
                continue
            if reason:
                dirs.remove(name)
                skipped.append({'path': child.relative_to(root).as_posix(), 'reason': reason})
        dirs.sort()
        siblings = sorted((parent / name for name in files), key=lambda p: p.name)
        videos = [p for p in siblings if p.suffix.lower() in VIDEO_EXTENSIONS and not INCOMPLETE.search(p.name)]
        stems = {p.stem for p in videos}
        for path in siblings:
            if cancelled and cancelled():raise InterruptedError('Inventaire interrompu.')
            relative = path.relative_to(root).as_posix()
            if INCOMPLETE.search(path.name):
                skipped.append({'path': relative, 'reason': 'telechargement_incomplet_ou_intermediaire'})
            elif path.suffix.lower() in SUBTITLE_EXTENSIONS or path.name.endswith('.info.json'):
                sidecars.append(relative)
            elif path in videos:
                # yt-dlp fragment/continuation markers can coexist with a final-looking file.
                markers = [p for p in siblings if INCOMPLETE.search(p.name)
                           and (p.name.startswith(path.name + '.') or p.name.startswith(path.stem + '.'))]
                if markers:
                    skipped.append({'path': relative, 'reason': 'marqueur_telechargement_associe'})
                    continue
                try:
                    reports.append(inspect_video(path, root, siblings, stems, hash_media))
                except (OSError, ValueError) as exc:
                    errors.append({'path': relative, 'reason': str(exc) if isinstance(exc, ValueError) else 'media_illisible'})
            else:
                unexamined.append({'path': relative, 'reason': 'format_non_examine'})
    associated = {t['path'] for r in reports for t in r['tracks']}
    associated.update(r['metadata']['path'] for r in reports if r['metadata']['status'] != 'missing')
    unexamined.extend({'path': p, 'reason': 'annexe_sans_video_inventoriee'}
                      for p in sidecars if p not in associated)
    generated_at = datetime.now(timezone.utc).isoformat()
    # Group by source for review, without claiming identical editions or deleting copies.
    groups = {}
    for report in reports:
        key = report['source']['key']
        if key:
            groups.setdefault(key, []).append(report['path'])
    for report in reports:
        report['same_source_paths'] = groups.get(report['source']['key'], [])
        report['generated_at'] = generated_at
    return {'schema_version': 1, 'generated_at': generated_at,
            'root': str(root), 'scope': 'local_sidecars_only', 'videos': reports,
            'skipped': skipped, 'errors': errors, 'unexamined': unexamined, 'exhaustive': False,
            'limitations': ['Fin du téléchargement présumée par nom et marqueurs, sans décodage du média.',
                            'Pistes intégrées aux conteneurs et vidéos dans les ZIM non examinées.',
                            'Langue, sens et synchronisation non vérifiés ; aucun accès réseau.']}


def export_reports(result, output):
    root = Path(result['root']).resolve()
    output = Path(output).resolve()
    if output == root or root in output.parents:
        raise ValueError('Le rapport doit être placé hors du dossier vidéo.')
    # A new directory only: never overwrite an original or an older report.
    output.mkdir(parents=True, exist_ok=False)
    for report in result['videos']:
        with (output / (report['inventory_id'] + '.json')).open('x', encoding='utf-8') as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2, allow_nan=False)
            stream.write('\n')
    summary = {k: v for k, v in result.items() if k != 'videos'}
    summary['videos'] = [{'path': r['path'], 'report': r['inventory_id'] + '.json',
                          'subtitle_status': r['subtitle_status']} for r in result['videos']]
    summary['video_count'] = len(result['videos'])
    with (output / 'inventory.json').open('x', encoding='utf-8') as stream:
        json.dump(summary, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--video-dir', type=Path, required=True, help='Dossier library/video à examiner récursivement')
    parser.add_argument('--output-dir', type=Path, required=True, help='Nouveau dossier de rapports, hors des vidéos')
    parser.add_argument('--hash-media', action='store_true', help='Lire intégralement les médias pour calculer leur SHA-256 (plus lent)')
    args = parser.parse_args(argv)
    try:
        root = args.video_dir.resolve(strict=True)
        output = args.output_dir.resolve()
        if output.exists() or output == root or root in output.parents:
            raise ValueError('Choisir un nouveau dossier de rapports hors du dossier vidéo.')
        result = inventory(root, args.hash_media)
        export_reports(result, output)
    except (OSError, ValueError) as exc:
        print(f'Inventaire impossible : {exc}', file=sys.stderr)
        return 2
    print(f"{len(result['videos'])} vidéo(s), {len(result['skipped'])} exclusion(s), "
          f"{len(result['errors'])} erreur(s). Rapports : {output}")
    return 1 if result['errors'] else 0


if __name__ == '__main__':
    raise SystemExit(main())
