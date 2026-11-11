#!/usr/bin/env python3
"""Index attributed real sources, test bilingual retrieval, then an optional real UI answer."""
import argparse
import hashlib
import json
import re
import time
import uuid

import linux_lab as lab
from lab_api import WebUI


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepare-only', action='store_true')
    parser.add_argument('--model', default='qwen3.5:4b-q4_K_M')
    args = parser.parse_args()
    if not args.prepare_only:
        lab.require_inference()
    api = WebUI()
    checkpoint = lab.MOUNT / 'results/research-import.json'
    sources = json.loads((lab.MOUNT / 'results/research-sources.json').read_text())
    if checkpoint.exists():
        imported = json.loads(checkpoint.read_text())
    else:
        knowledge = api.request('/api/v1/knowledge/create', {'name': 'Évaluation — corpus réel bilingue',
            'description': 'Textes extraits de Wikipédia et Wikibooks locaux, avec référence vers les originaux illustrés.'})
        imported = {'knowledge_id': knowledge['id'], 'files': {}}
        lab.setup.write_json(checkpoint, imported)
    for source in sources:
        identifier = source['id']
        content = (lab.MOUNT / 'data/research/sources' / (identifier + '.txt')).read_bytes()
        digest = hashlib.sha256(content).hexdigest()
        if identifier in imported['files']:
            if imported['files'][identifier]['sha256'] != digest:
                raise RuntimeError('Source modifiée : préparer une nouvelle collection au lieu de mélanger les versions.')
            continue
        boundary = 'research-' + uuid.uuid4().hex
        body = (f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="{identifier}.txt"\r\nContent-Type: text/plain\r\n\r\n').encode() + content + f'\r\n--{boundary}--\r\n'.encode()
        file = api.request('/api/v1/files/?process=true&process_in_background=false', data=body,
                           content_type=f'multipart/form-data; boundary={boundary}')
        status = api.request(f'/api/v1/files/{file["id"]}/process/status')
        if status.get('status') != 'completed':
            raise RuntimeError('Import non terminé : ' + identifier)
        api.request(f'/api/v1/knowledge/{imported["knowledge_id"]}/file/add', {'file_id': file['id']})
        imported['files'][identifier] = {'id': file['id'], 'sha256': digest, 'source_url': source['url']}
        lab.setup.write_json(checkpoint, imported)
        print('INDEXED', identifier, flush=True)
    question = "Dans l'exemple du manuel de radioamateur anglais, le moteur a une résistance de 1 ohm et une batterie de 12 V. Quel courant circule et le fil prévu pour 10 A convient-il ?"
    retrieval = api.request('/api/v1/retrieval/query/doc', {'collection_name': imported['knowledge_id'],
                            'query': question, 'k': 3, 'hybrid': False})
    found = json.dumps(retrieval, ensure_ascii=False)
    if 'BOOK-EN-OHM' not in found or '10 A' not in found:
        raise RuntimeError('La recherche commune ne retrouve pas le passage anglais attendu.')
    lab.setup.write_json(lab.MOUNT / 'results/real-rag-retrieval.json', {'question': question, 'retrieval': retrieval})
    print('BILINGUAL_RETRIEVAL_OK', flush=True)
    if args.prepare_only:return
    started = time.monotonic()
    profiles=json.loads((lab.setup.ROOT/'deploy/model-profiles.json').read_text())['profiles']
    profile=next((p for p in profiles if args.model=='survie-'+p['id']),None)
    thinking=profile['think'] if profile else ('low' if args.model.startswith('gpt-oss') else False)
    response = api.request('/api/chat/completions', {'model': args.model, 'stream': False,
        'messages': [{'role': 'user', 'content': question + ' Réponds uniquement en JSON avec courant_A, fil_utilisable (booléen) et source (identifiant du document).'}],
        'files': [{'type': 'collection', 'id': imported['knowledge_id'], 'name': 'Évaluation — corpus réel bilingue'}],
        'options': {'num_ctx': 8192, 'num_predict': 4096, 'think': thinking, 'temperature': 0}})
    text = response['choices'][0]['message'].get('content', '')
    try:answer = json.loads(re.sub(r'^```(?:json)?\s*|\s*```$', '', text.strip()))
    except ValueError:answer = None
    passed = bool(response.get('sources')) and isinstance(answer, dict) and answer.get('courant_A') == 12 and answer.get('fil_utilisable') is False
    report = {'model': args.model, 'question': question, 'response': response,
              'elapsed_seconds': time.monotonic() - started, 'passed_closed_check': passed}
    name = re.sub(r'[^a-zA-Z0-9_-]', '_', args.model)
    lab.setup.write_json(lab.MOUNT / f'results/real-rag-answer-{name}.json', report)
    print('REAL_RAG_RESULT', passed, round(report['elapsed_seconds'], 2), text, flush=True)


if __name__ == '__main__':main()
