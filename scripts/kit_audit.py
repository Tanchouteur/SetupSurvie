"""Check offline payload dependencies without launching services or loading a model."""
import hashlib
import json
from pathlib import Path
import re
import tarfile

import content
import setup
from pilot_kit import KIT_APP_FILES


def validate(root,manifest):
    root=Path(root)
    if (root/'kit-building.json').exists():raise setup.SetupError('Kit encore en préparation.')
    records={item['path']:item for item in manifest['files']}
    if len(records)!=len(manifest['files']):raise setup.SetupError('Chemins de kit dupliqués.')
    def required(relative):
        if relative not in records:raise setup.SetupError('Dépendance hors ligne absente du manifeste : '+relative)
        return content.destination(root,relative)
    def read(relative):return json.loads(required(relative).read_text(encoding='utf-8'))
    for relative in records:
        content.destination(root,relative)
        if relative.startswith('payload/'):
            allowed=relative.startswith(('payload/models/','payload/library/','payload/state/openwebui/cache/')) or relative=='payload/catalog/downloaded-content.json'
            if not allowed or relative.endswith(('.db','.db-wal','.db-shm','.key','.pem','.env')) or Path(relative).name in ('settings.json','identifiants.txt'):
                raise setup.SetupError('État personnel interdit dans le kit public : '+relative)
        elif relative not in ('images.tar','images.tar.json'):
            allowed=relative in {'app/'+name for name in KIT_APP_FILES}
            allowed|=any(relative.startswith('app/'+folder+'/') for folder in ('scripts','pilot','portal','deploy','docs','fixtures','tests','assets','vendor'))
            if not allowed:raise setup.SetupError('Fichier hors périmètre du kit : '+relative)
    release=read('app/deploy/release.json')
    source=required('app/pilot/app.py').read_text(encoding='utf-8')
    match=re.search(r"^VERSION=['\"]([^'\"]+)['\"]",source,re.MULTILINE)
    if not match or match.group(1)!=release['version']:raise setup.SetupError('Version affichée par le kit incohérente.')
    versions=read('app/deploy/versions.json');profiles=read('app/deploy/model-profiles.json')['profiles']
    for item in read('app/deploy/discovery-packages.json')['files']:
        relative='app/vendor/discovery/'+item['file'];required(relative)
        if records[relative]['bytes']!=item['bytes'] or records[relative]['sha256']!=item['sha256']:
            raise setup.SetupError('Paquet de découverte réseau hors ligne incohérent.')
    models=sorted({p['model'] for p in profiles})
    for model in models:
        name,tag=model.split(':',1)
        data=read('payload/models/manifests/registry.ollama.ai/library/'+name+'/'+tag)
        for layer in [data['config'],*data['layers']]:
            if not re.fullmatch('sha256:[0-9a-f]{64}',layer['digest']):raise setup.SetupError('Référence de modèle non valide.')
            path='payload/models/blobs/'+layer['digest'].replace(':','-');required(path)
            if records[path]['bytes']!=layer['size'] or records[path]['sha256']!=layer['digest'].split(':',1)[1]:raise setup.SetupError('Couche du modèle incohérente.')
    cache='payload/state/openwebui/cache/'
    if read(cache+'embedding-ready.json')!=versions['embedding'] or read(cache+'whisper/ready.json')!=versions['speech']:
        raise setup.SetupError('Révision des caches hors ligne incorrecte.')
    for relative in ('embedding/bge-m3/config.json','embedding/bge-m3/tokenizer.json',
                     'whisper/faster-whisper-small/model.bin','whisper/faster-whisper-small/config.json','whisper/faster-whisper-small/tokenizer.json'):
        required(cache+relative)
    if not any(cache+'embedding/bge-m3/'+name in records for name in ('model.safetensors','pytorch_model.bin')):
        raise setup.SetupError('Poids du moteur de recherche absents du kit.')
    if not any(k.startswith(cache+'tiktoken/') for k in records):raise setup.SetupError('Cache de tokenisation absent.')
    images=read('images.tar.json')
    if images['sha256']!=records['images.tar']['sha256']:raise setup.SetupError('Empreinte de l’archive d’images incohérente.')
    by_service={entry['service']:entry for entry in images['images']}
    if len(by_service)!=len(images['images']):raise setup.SetupError('Images de service dupliquées.')
    expected={name:versions['images'][name] for name in ('open-webui','kiwix','portal','ollama')}
    routing_path='payload/library/maps/routing/current/manifest.json'
    if routing_path in records:
        routing=read(routing_path);recipe=read('app/deploy/routing-engine.json')
        if not routing.get('complete') or routing.get('image')!=recipe['image'] or set(routing['profiles'])!=set(recipe['profiles']):
            raise setup.SetupError('Réseau de routage incomplet ou incompatible.')
        expected['routing']=recipe['image']
        for item in routing['files']:
            path='payload/library/maps/routing/current/'+item['path'];required(path)
            if records[path]['bytes']!=item['bytes'] or records[path]['sha256']!=item['sha256']:raise setup.SetupError('Index de routage incohérent.')
    for name,reference in expected.items():
        if name not in by_service or by_service[name]['reference']!=reference:
            raise setup.SetupError('Image hors ligne absente ou incompatible : '+name)
    # Inspect Docker archive configuration IDs without extracting anything.
    with tarfile.open(required('images.tar')) as archive:
        member=archive.getmember('manifest.json')
        if not member.isfile() or member.size>2_000_000:raise setup.SetupError('Manifeste Docker non valide.')
        entries=json.load(archive.extractfile(member));ids=set()
        for item in entries:
            config=archive.getmember(item['Config'])
            if not config.isfile() or config.size>2_000_000:raise setup.SetupError('Configuration d’image non valide.')
            ids.add('sha256:'+hashlib.sha256(archive.extractfile(config).read()).hexdigest())
    if not {setup.canonical_image_id(entry['id']) for entry in by_service.values()}.issubset(ids):raise setup.SetupError('L’archive ne contient pas les ID d’images annoncés.')
    map_count=0;geography_count=0
    map_manifest='payload/library/maps/manifest.json'
    if map_manifest in records:
        maps=read(map_manifest)['maps'];map_count=len(maps)
        for item in maps:
            path='payload/library/maps/'+item['path'];required(path)
            if records[path]['sha256']!=item['sha256'] or records[path]['bytes']!=item['bytes']:raise setup.SetupError('Fond de carte incohérent.')
    for path in records:
        if re.fullmatch(r'payload/library/maps/geography/[a-f0-9]{20}/manifest.json',path):
            value=read(path);geography_count+=1
            if not value.get('complete'):raise setup.SetupError('Zone géographique incomplète.')
            for item in value['files']:
                relative=path.rsplit('/',1)[0]+'/'+item['path'];required(relative)
                if records[relative]['sha256']!=item['sha256'] or records[relative]['bytes']!=item['bytes']:raise setup.SetupError('Zone géographique incohérente.')
    for script in ('start-pilot.ps1','stop-pilot.ps1','create-shortcuts.ps1'):
        required('app/scripts/'+script)
    required('app/portal/branding/favicon.ico')
    return {'version':release['version'],'models':len(models),'images':len(by_service),'maps':map_count,'geography_zones':geography_count,
            'routing':routing_path in records,'bytes':sum(item['bytes'] for item in manifest['files']),
            'notice':'Prérequis Windows et recette réelle chez Marc à vérifier séparément.'}
