"""Public learning entry points; the shared catalogue contains no private data."""
import json
from pathlib import Path

RULES=Path('/srv/kiwix-themes.json')
if not RULES.exists():RULES=Path(__file__).resolve().parents[1]/'deploy/kiwix-themes.json'


def pathways():
    config=json.loads(RULES.read_text(encoding='utf-8'))
    ordered=list(dict.fromkeys(config.get('learning_order',[])+list(config['themes'])))
    return {'steps':config.get('learning_steps',[]),
            'domains':[{'id':key,'label':config['themes'][key]['label'],**config['themes'][key]['learning']}
                       for key in ordered if key in config['themes'] and 'learning' in config['themes'][key]],
            'notice':'Ces parcours guident la recherche. Les documents disponibles et les informations manquantes sont à vérifier pour chaque sujet.'}
