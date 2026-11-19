"""Download the portal's local models through its private Ollama connection."""
import asyncio
import json
from uuid import uuid4

import httpx
from fastapi import HTTPException


def byte_count(value):
    return value if type(value) is int and value >= 0 else None


class ModelDownloads:
    def __init__(self, endpoint, config):
        self.endpoint = endpoint
        self.sizes = config.get('download_sizes', {})
        self.catalogue = {}
        for profile in config['profiles']:
            model, category = profile['model'], profile['category']
            self.catalogue.setdefault(model, {
                'category': category,
                'name': profile['name'].split(' · ', 1)[-1],
            })
        self.job = None
        self.task = None
        self.lock = asyncio.Lock()

    async def installed(self):
        try:
            async with httpx.AsyncClient(trust_env=False, timeout=4) as client:
                response = await client.get(self.endpoint + '/api/tags')
                response.raise_for_status()
            return {entry['model'] if 'model' in entry else entry['name']: byte_count(entry.get('size'))
                    for entry in response.json()['models']}
        except (httpx.HTTPError, ValueError, KeyError, TypeError):
            return None

    async def status(self):
        installed = await self.installed()
        known = installed if installed is not None else {}
        models = [
            {
                'model': model,
                **card,
                'installed': None if installed is None else model in known,
                'size': known.get(model) or self.sizes.get(model),
            }
            for model, card in self.catalogue.items()
        ]
        return {'available': installed is not None, 'models': models,
                'download': self.job.copy() if self.job else None}

    async def start(self, model):
        if model not in self.catalogue:
            raise HTTPException(400, 'Ce modèle ne figure pas dans le catalogue SetupSurvie.')
        async with self.lock:
            if self.task and not self.task.done():
                if self.job['model'] == model:
                    return self.job.copy()
                raise HTTPException(409, 'Un téléchargement de modèle est déjà en cours.')
            installed = await self.installed()
            if installed is None:
                raise HTTPException(503, 'Le moteur IA est indisponible. Démarrez-le depuis les réglages.')
            if model in installed:
                return {'model': model, 'state': 'complete', 'completed': None, 'total': None,
                        'message': 'Ce modèle est déjà installé.'}
            self.job = {'id': uuid4().hex, 'model': model, 'state': 'downloading', 'completed': None,
                        'total': self.sizes.get(model), 'message': 'Connexion au catalogue Ollama…'}
            self.task = asyncio.create_task(self.run(self.job))
            return self.job.copy()

    async def cancel(self, identifier=None):
        async with self.lock:
            if self.task and not self.task.done():
                if identifier is not None and identifier != self.job['id']:
                    raise HTTPException(409, 'Le téléchargement a changé. Actualisez les réglages.')
                self.task.cancel()
                await asyncio.gather(self.task, return_exceptions=True)
                self.job.update(state='cancelled', message='Téléchargement annulé. Vous pouvez le relancer.')
            return self.job.copy() if self.job else None

    async def run(self, job):
        layers = {}
        try:
            async with httpx.AsyncClient(trust_env=False, timeout=httpx.Timeout(180, connect=5)) as client:
                async with client.stream('POST', self.endpoint + '/api/pull',
                                         json={'model': job['model'], 'stream': True}) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if not line:
                            continue
                        event = json.loads(line)
                        if event.get('error'):
                            message = self.error_message(str(event['error']))
                            job.update(state='error', message=message)
                            return
                        phase = event.get('status')
                        if phase == 'success':
                            job.update(state='complete', completed=job['total'], message='Modèle prêt à utiliser.')
                            return
                        digest = event.get('digest')
                        total = byte_count(event.get('total'))
                        completed = byte_count(event.get('completed'))
                        if isinstance(digest, str) and total:
                            previous = layers.get(digest, (0, 0))[0]
                            layers[digest] = (min(total, max(previous, completed or 0)), total)
                            job.update(
                                completed=sum(layer[0] for layer in layers.values()),
                                total=max(self.sizes.get(job['model'], 0), sum(layer[1] for layer in layers.values())),
                                message='',
                            )
                        elif phase in ('verifying sha256 digest', 'writing manifest'):
                            job['message'] = 'Vérification et installation du modèle…'
        except (httpx.HTTPError, ValueError, AttributeError):
            pass
        job.update(state='error', message='Téléchargement interrompu. Vérifiez Internet sur le PC serveur et réessayez.')

    @staticmethod
    def error_message(error):
        error = error.lower()
        if 'no space left' in error or 'disk full' in error or 'not enough space' in error:
            return 'Le disque des modèles est plein. Libérez de la place sur le PC serveur et réessayez.'
        if 'not found' in error or 'does not exist' in error:
            return 'Ce modèle est indisponible dans le catalogue Ollama.'
        if 'newer version' in error or 'upgrade ollama' in error:
            return 'Ce modèle nécessite une version plus récente du moteur IA.'
        return 'Le téléchargement a échoué. Vérifiez Internet sur le PC serveur et réessayez.'
