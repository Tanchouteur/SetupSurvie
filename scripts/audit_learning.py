#!/usr/bin/env python3
"""Audit the declared learning needs against catalogue metadata, without downloading contents."""
import argparse
from datetime import datetime,timezone
import hashlib
from pathlib import Path
import xml.etree.ElementTree as ET

import content
import kiwix_select as ks
import setup


def audit(raw,data_dir=None):
    entries=ks.parse_feed(raw);rules=ks.themes();requested=[k for k,v in rules.items() if 'learning' in v]
    candidates={}
    for entry in entries:
        if not {'fra','eng'}.intersection(entry['languages']):continue
        reasons=ks.matches(entry,rules,requested)
        if not reasons:continue
        key=ks.family(entry['filename'])
        row=candidates.setdefault(key,{'filename':entry['filename'],'filenames':[],'title':entry['title'],'themes':[],'status':'catalogue_only'})
        if entry['filename'] not in row['filenames']:row['filenames'].append(entry['filename'])
        row['themes']=list(dict.fromkeys(row['themes']+list(reasons)))
    for item in content.catalog():
        if not {'fr','en','fra','eng','mul'}.intersection(item['language'].split(',')):continue
        themes=[t for t in requested if item['id'] in rules[t].get('guides',[])]
        if themes:candidates[item['path']]={'filename':Path(item['path']).name,'filenames':[Path(item['path']).name],'title':item['title'],'themes':themes,'status':'catalogue_only'}
    if data_dir:
        # Presence is distinct from integrity and editorial validation.
        for row in candidates.values():
            for name in row['filenames']:
                relative=('library/zim/' if name.endswith('.zim') else 'library/guides/')+name
                path=content.destination(data_dir,relative)
                if path.is_file() and not path.is_symlink():
                    row['status']='already_local';break
    return {'schema':1,'created_at':datetime.now(timezone.utc).isoformat(),
            'catalog_url':ks.CATALOG_URL,'catalog_sha256':hashlib.sha256(raw).hexdigest(),'catalog_entries':len(entries),
            'coverage':ks.learning_coverage(rules,requested,list(candidates.values()),presence_known=data_dir is not None),
            'references':list(candidates.values()),
            'notice':'Correspondances de métadonnées à examiner. Aucun contenu téléchargé ou lu, aucune intégrité ni couverture pédagogique validée.'}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--feed',type=Path,help='Catalogue XML existant ; sinon lecture du catalogue officiel en ligne.')
    parser.add_argument('--data-dir',type=Path,help='Facultatif : relever aussi la présence des fichiers, sans les lire.')
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if args.output.exists() or args.output.is_symlink():parser.error('Choisissez un nouveau rapport ; aucun fichier existant ne sera remplacé.')
    if args.data_dir and not args.data_dir.is_dir():parser.error('Dossier de données existant requis.')
    if args.feed and args.feed.stat().st_size>25_000_000:parser.error('Catalogue XML trop volumineux.')
    raw=args.feed.read_bytes() if args.feed else ks.fetch(ks.CATALOG_URL)
    report=audit(raw,args.data_dir)
    setup.write_json(args.output,report)
    for row in report['coverage']:
        presence=f"{row['local_references']} fichier(s) présent(s)" if row['local_references'] is not None else 'présence locale non examinée'
        print(f"{row['label']} : {row['references']} référence(s) repérée(s), {presence} ; sujets à examiner : {len(row['skills_to_review'])}.")
    print(report['notice'])


if __name__=='__main__':
    try:main()
    except (setup.SetupError,OSError,ValueError,ET.ParseError) as exc:raise SystemExit('ERREUR : '+str(exc))
