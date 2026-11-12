#!/usr/bin/env python3
"""Review a frozen download plan without changing it or touching its downloads."""
import argparse
from collections import Counter
from datetime import datetime,timezone
import json
from pathlib import Path

import content
import kiwix_select as ks
import setup


def audit(plan,entries):
    items=content.catalog(plan)
    index={e['filename']:e for e in entries}
    rules=ks.themes();families={ks.family(Path(i['path']).name) for i in items if i['path'].endswith('.zim')}
    seen=set();rows=[]
    for item in items:
        name=Path(item['path']).name;entry=index.get(name);status='manual_review';reason='Référence absente du catalogue actuel ; vérifier sa provenance et son contenu.'
        reasons={}
        if item['path'] in seen:status='duplicate';reason='Même chemin présent plusieurs fois dans le plan.'
        elif not name.endswith('.zim'):
            status='guide';reason='Guide référencé ; couverture, édition et droits restent à vérifier.'
        elif ks.full_collection(name) in families:
            status='overlap';reason='Une collection complète de même langue est aussi prévue ; chevauchement à éviter.'
        elif entry:
            reasons=ks.matches(entry,rules,list(rules));policy=ks.collection_policy(entry['name'])
            if policy=='excluded':status='out_of_scope';reason='Correspondance hors du fonds pratique retenu.'
            elif policy=='optional':status='supplement';reason='Fonds culturel complet ou grande collection vidéo : choix explicite recommandé.'
            elif reasons:status='relevant_reference';reason='Collection cohérente par ses métadonnées ; contenu et utilité à examiner.'
            else:reason='Aucune correspondance actuelle : vérifier avant de conserver dans la prochaine sélection.'
        seen.add(item['path'])
        rows.append({'filename':name,'title':item['title'],'bytes':item['bytes'],'status':status,'reason':reason,'themes':list(reasons)})
    totals=Counter()
    for row in rows:totals[row['status']]+=row['bytes']
    return {'schema':1,'created_at':datetime.now(timezone.utc).isoformat(),'plan_sha256':setup.file_hash(plan),
            'items':sorted(rows,key=lambda r:r['bytes'],reverse=True),'count':len(rows),'total_bytes':sum(r['bytes'] for r in rows),
            'bytes_by_status':dict(totals),'notice':'Audit de métadonnées du plan, pas inspection des contenus ni validation médicale ou pédagogique. Aucun fichier supprimé, aucun transfert modifié.'}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('plan',type=Path)
    parser.add_argument('--feed',type=Path)
    parser.add_argument('--output',required=True,type=Path)
    args=parser.parse_args()
    if args.output.exists() or args.output.is_symlink():parser.error('Choisissez un nouveau rapport.')
    if args.feed and args.feed.stat().st_size>25_000_000:parser.error('Catalogue trop volumineux.')
    raw=args.feed.read_bytes() if args.feed else ks.fetch(ks.CATALOG_URL)
    report=audit(args.plan,ks.parse_feed(raw));report['catalog_sha256']=__import__('hashlib').sha256(raw).hexdigest()
    setup.write_json(args.output,report)
    print(f"{report['count']} ajouts, {report['total_bytes']/1e9:.2f} Go de fichiers complets (pas le reste à transférer).")
    for key,size in report['bytes_by_status'].items():print(f'{key}: {size/1e9:.2f} Go')
    for row in report['items'][:20]:print(f"{row['bytes']/1e9:.2f} Go — {row['status']} — {row['title']}")
    print(report['notice'])


if __name__=='__main__':
    try:main()
    except (setup.SetupError,OSError,ValueError) as exc:raise SystemExit('ERREUR : '+str(exc))
