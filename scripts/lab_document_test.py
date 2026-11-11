#!/usr/bin/env python3
"""Import a real file into Open WebUI, retrieve in French, and ask the assistant."""
import json
import time
import urllib.request
import uuid

import linux_lab as lab


def main():
    lab.require_inference()
    _, c = lab.configuration()
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    token = None

    def api(path, payload=None, *, data=None, content_type='application/json'):
        if payload is not None:
            data = json.dumps(payload).encode()
        headers = {'Content-Type': content_type}
        if token:
            headers['Authorization'] = 'Bearer ' + token
        request = urllib.request.Request('http://127.0.0.1:3000' + path, data=data, headers=headers)
        with opener.open(request, timeout=600) as response:
            return json.load(response)

    signin = api('/api/v1/auths/signin', {'email': c['admin_email'], 'password': c['admin_password']})
    token = signin['token']  # Never written to reports or logs.
    checkpoint = lab.MOUNT / 'results/document-import.json'
    if checkpoint.exists():
        imported = json.loads(checkpoint.read_text())
    else:
        knowledge = api('/api/v1/knowledge/create', {'name': 'Essai multilingue ALPHA',
            'description': 'Fiche de démonstration anglaise pour les essais français.'})
        boundary = 'survie-' + uuid.uuid4().hex
        content = (lab.MOUNT / 'data/library/guides/box.en.txt').read_bytes()
        body = (f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="box.en.txt"\r\n'
                'Content-Type: text/plain\r\n\r\n').encode() + content + f'\r\n--{boundary}--\r\n'.encode()
        file = api('/api/v1/files/?process=true&process_in_background=false', data=body,
                   content_type=f'multipart/form-data; boundary={boundary}')
        imported = {'file_id': file['id'], 'knowledge_id': knowledge['id']}
        lab.setup.write_json(checkpoint, imported)
    file_id = imported['file_id']
    status = api(f'/api/v1/files/{file_id}/process/status')
    if status.get('status') != 'completed':
        raise RuntimeError(f'Import non terminé : {status}')
    api(f'/api/v1/knowledge/{imported["knowledge_id"]}/file/add', {'file_id': file_id})
    question = 'Quel est le volume intérieur de la boîte ALPHA ? Peut-on en déduire sa charge maximale ?'
    retrieval = api('/api/v1/retrieval/query/doc', {'collection_name': 'file-' + file_id,
                    'query': question, 'k': 3, 'hybrid': False})
    documents = json.dumps(retrieval.get('documents', []), ensure_ascii=False)
    if '72' not in documents or 'maximum safe load' not in documents:
        raise RuntimeError('La recherche ne retrouve pas les deux éléments attendus.')
    started = time.monotonic()
    answer = api('/api/chat/completions', {'model': c['chat_model'], 'stream': False,
        'messages': [{'role': 'user', 'content': question + ' Réponds brièvement en français avec ta source.'}],
        'files': [{'type': 'file', 'id': file_id}],
        'options': {'num_ctx': 4096, 'num_predict': 512, 'think': False, 'temperature': 0}})
    result = {'import': imported, 'status': status, 'question': question,
              'retrieval': retrieval, 'completion': answer,
              'completion_wall_seconds': time.monotonic() - started}
    lab.setup.write_json(lab.MOUNT / 'results/document-test.json', result)
    choice = answer.get('choices', [{}])[0]
    text = choice.get('message', {}).get('content', '')
    if not text.strip() or choice.get('finish_reason') == 'length' or not answer.get('sources'):
        raise RuntimeError('Réponse vide, tronquée ou sans source ; consulter document-test.json.')
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
