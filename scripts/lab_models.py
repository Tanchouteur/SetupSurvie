#!/usr/bin/env python3
"""Give the three installed models names people can understand, without copying weights."""
import json
import urllib.parse

import linux_lab as lab
from lab_api import WebUI

MODELS = (
    ('qwen3.5:4b-q4_K_M', 'Réponse rapide · Qwen3.5 4B', False),
    ('qwen3.5:9b-q4_K_M', 'Réponse moyenne · Qwen3.5 9B', True),
    ('qwen3.5:27b-q4_K_M', 'Réponse approfondie · Qwen3.5 27B', True),
)

# Keep the native harness focused on the offline knowledge appliance.
# Unspecified categories default to enabled upstream, so opt out explicitly.
BUILTIN_TOOLS = {name: name in {'time', 'user_input', 'files', 'knowledge'} for name in (
    'time', 'user_input', 'files', 'knowledge', 'chats', 'subagents', 'memory',
    'web_search', 'image_generation', 'code_interpreter', 'notes', 'channels',
    'skills', 'tasks', 'automations', 'calendar', 'notifications')}


def main():
    api = WebUI()
    available = {x['name'] for x in lab.setup.Installation.request('http://127.0.0.1:11435/api/tags')['models']}
    if not {x[0] for x in MODELS}.issubset(available):
        raise RuntimeError('Les trois téléchargements doivent être terminés avant de publier les choix.')
    current = api.request('/api/models')['data']
    result = []
    for identifier, name, thinking in MODELS:
        existing = next((m for m in current if m['id'] == identifier), {})
        payload = {'id': identifier, 'base_model_id': None, 'name': name, 'meta': {},
                   'params': {'num_ctx': 8192, 'think': thinking,
                              'system': (lab.setup.ROOT / 'deploy/assistant-system.fr.txt').read_text()},
                   'is_active': True}
        if existing.get('info'):
            full = api.request('/api/v1/models/model?' + urllib.parse.urlencode({'id': identifier}))
            payload['meta'] = full.get('meta') or {}
            payload['params'] = {**(full.get('params') or {}), **payload['params']}
            payload['access_grants'] = full.get('access_grants')
        payload['meta']['builtinTools'] = BUILTIN_TOOLS
        endpoint = '/api/v1/models/model/update' if existing.get('info') else '/api/v1/models/create'
        api.request(endpoint, payload)
        result.append({'id': identifier, 'name': name, 'thinking': thinking})
    actual = api.request('/api/models')['data']
    for item in result:
        if not any(m['id'] == item['id'] and m['name'] == item['name'] for m in actual):
            raise RuntimeError('Le nom du modèle ne correspond pas dans le sélecteur.')
        full = api.request('/api/v1/models/model?' + urllib.parse.urlencode({'id': item['id']}))
        if full.get('params', {}).get('think') != item['thinking']:
            raise RuntimeError('Le réglage du raisonnement n’a pas été conservé.')
    lab.setup.write_json(lab.MOUNT / 'results/model-labels.json', result)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
