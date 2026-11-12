#!/usr/bin/env python3
"""Prepare tiny fictional documents and a manual model-evaluation sheet. No inference."""
import argparse
import json
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]


def prepare(destination):
    path=Path(destination).expanduser().absolute()
    if any(p.is_symlink() for p in (path,*path.parents)) or path.exists():
        raise ValueError('Choisissez un nouveau dossier hors de votre bibliothèque réelle.')
    recipe=json.loads((ROOT/'fixtures/evaluation/reliability.json').read_text(encoding='utf-8'))
    path.mkdir(parents=True)
    guides=path/'guides';guides.mkdir()
    metadata=[]
    for item in recipe['sources']:
        if not re.fullmatch('[a-z0-9-]+',item['id']):raise ValueError('Identifiant de fixture non valide.')
        name='TEST-fiabilite-'+item['id']+'.fr.txt'
        (guides/name).write_text(item['title']+'\n\n'+item['text']+'\n',encoding='utf-8')
        metadata.append({'path':name,'title':item['title'],'language':'fr','provenance':'Fixture synthétique SetupSurvie, aucun usage pratique',
                         'licence':'Document fictif du projet','document_date':item['document_date'],'edition':item['edition'],'collected_at':''})
    (guides/'metadata.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    lines=['# Recette manuelle de fiabilité — documents fictifs','',
           'Aucun modèle n’a été lancé. Importer ces fichiers dans une installation de test isolée, jamais dans le fonds familial.',
           'Pour chaque essai : nouvelle conversation, modèle/mode, version, machine, réponse, sources ouvertes, délai et appréciation humaine.','']
    for case in recipe['cases']:
        lines.extend(['## '+case['id'],'',case['question'],'','Sources : '+(', '.join(case['sources']) or 'aucune notice correspondante'),'',
                      *['- '+criterion for criterion in case['criteria']],'','Résultat réel : non exécuté.',''])
    (path/'RECETTE.md').write_text('\n'.join(lines),encoding='utf-8')
    return path


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('destination')
    args=parser.parse_args()
    try:print('Fixtures préparées, aucun modèle lancé :',prepare(args.destination))
    except (OSError,ValueError) as exc:parser.exit(1,'ERREUR : '+str(exc)+'\n')
