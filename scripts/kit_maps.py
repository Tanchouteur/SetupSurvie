"""Publish only selected, verified public map bundles into an existing pilot kit."""
import json
from pathlib import Path
import re
import shutil
import uuid

import content
import setup


def recover(root):
    root=setup.safe_path(root);marker=content.destination(root,'kit-building.json')
    value=json.loads(marker.read_text(encoding='utf-8'))
    if value.get('kind')!='SetupSurvie maps publication' or not re.fullmatch(r'\.maps-stage-[a-f0-9]{32}',value.get('staging','')):
        raise setup.SetupError('Cette préparation ne relève pas de la récupération cartographique.')
    staging=content.destination(root,value['staging']);transaction=json.loads((staging/'transaction.json').read_text())
    for item in reversed(transaction['files']):
        target=content.destination(root,item['path']);backup=content.destination(staging,'previous/'+item['path'])
        if item['had_previous']:
            if backup.exists():target.unlink(missing_ok=True);backup.replace(target)
        else:target.unlink(missing_ok=True)
    setup.write_json(root/'manifest.json',transaction['original']);marker.unlink();shutil.rmtree(staging)


def public_maps(data,geography_ids,include_routing):
    records={}
    def add(relative,size=None,digest=None):
        path=content.destination(data,relative)
        if not path.is_file():raise setup.SetupError('Fichier cartographique absent : '+relative)
        actual=setup.file_hash(path)
        if size is not None and (path.stat().st_size!=size or actual!=digest):
            raise setup.SetupError('Fichier cartographique altéré : '+relative)
        records['payload/'+relative]={'path':'payload/'+relative,'bytes':path.stat().st_size,'sha256':actual,'source':path}
    def bundle(base):
        manifest=content.destination(data,base+'/manifest.json')
        value=json.loads(manifest.read_text(encoding='utf-8'))
        if not value.get('complete'):raise setup.SetupError('Jeu cartographique incomplet.')
        for item in value['files']:
            if base.endswith('/routing/current'):
                if not re.fullmatch(r'(?:foot|motorcycle|car)/network\.osrm[\w.-]*',item['path']):raise setup.SetupError('Fichier de routage inattendu.')
            elif not re.fullmatch(r'places\.json|attribution\.txt|[NS]\d{2}[EW]\d{3}\.hgt',item['path']):
                raise setup.SetupError('Fichier géographique inattendu.')
            add(base+'/'+item['path'],item['bytes'],item['sha256'])
        add(base+'/manifest.json')
        return value
    manifest=content.destination(data,'library/maps/manifest.json')
    value=json.loads(manifest.read_text(encoding='utf-8'))
    for item in value['maps']:
        if not re.fullmatch(r'[a-z0-9-]+\.pmtiles',item['path']):raise setup.SetupError('Archive de carte non valide.')
        add('library/maps/'+item['path'],item['bytes'],item['sha256'])
    add('library/maps/manifest.json')
    for identifier in dict.fromkeys(geography_ids):
        if not re.fullmatch('[a-f0-9]{20}',identifier):raise setup.SetupError('Identifiant géographique non valide.')
        bundle('library/maps/geography/'+identifier)
    if include_routing:
        routing=bundle('library/maps/routing/current')
        recipe=json.loads((setup.ROOT/'deploy/routing-engine.json').read_text(encoding='utf-8'))
        if routing.get('image')!=recipe['image'] or set(routing.get('profiles',[]))!=set(recipe['profiles']):
            raise setup.SetupError('Le réseau ne correspond pas au moteur de routage épinglé.')
    return list(records.values())


def image_records(lab,include_routing):
    references={name:setup.VERSIONS['images'][name] for name in ('open-webui','kiwix','portal','ollama')}
    if include_routing:references['routing']=json.loads((setup.ROOT/'deploy/routing-engine.json').read_text())['image']
    records=[];estimate=0
    for name,reference in references.items():
        inspected=json.loads(lab.podman('image','inspect',reference if name=='routing' else lab.reference(name),capture=True).stdout)[0]
        records.append({'service':name,'id':inspected['Id'],'reference':reference})
        estimate+=inspected.get('Size',0)
    return records,estimate


def refresh(root,data,geography_ids,include_routing,images,save_images,*,image_bytes=0):
    """Stage first, then publish with rollback; existing unrelated files are preserved."""
    root=setup.safe_path(root);data=setup.safe_path(data)
    marker=content.destination(root,'kit-building.json')
    if marker.exists():raise setup.SetupError('Kit déjà en préparation ; terminer ou récupérer cette opération.')
    old=json.loads((root/'manifest.json').read_text(encoding='utf-8'))
    if old.get('kind')!='SetupSurvie public pilot kit':raise setup.SetupError('Destination non reconnue comme kit public.')
    with content.locked(content.destination(root,'maps-refresh.lock')):
        sources=public_maps(data,geography_ids,include_routing)
        existing={item['path']:item for item in old['files']}
        if len(existing)!=len(old['files']):raise setup.SetupError('Manifeste de kit ambigu.')
        archive=root/'images.tar';metadata=root/'images.tar.json'
        previous=json.loads(metadata.read_text(encoding='utf-8'))
        reuse=previous.get('images')==images
        if reuse and setup.file_hash(archive)!=previous.get('sha256'):
            raise setup.SetupError('Archive d’images existante altérée ; elle est conservée pour examen.')
        required=sum(item['bytes'] for item in sources)
        if not reuse:required+=max(image_bytes*2,archive.stat().st_size*2)
        if shutil.disk_usage(root).free<required+15_000_000_000:
            raise setup.SetupError('Espace insuffisant pour préparer le kit en conservant 15 Go libres.')
        staging=root/('.maps-stage-'+uuid.uuid4().hex);staging.mkdir()
        prepared=[];publishing=False
        try:
            for item in sources:
                target=content.destination(root,item['path'])
                if target.exists():
                    if item['path'] not in existing:raise setup.SetupError('Fichier non géré conservé : '+item['path'])
                    if target.stat().st_size==item['bytes'] and setup.file_hash(target)==item['sha256']:
                        existing[item['path']]={k:item[k] for k in ('path','bytes','sha256')};continue
                staged=content.destination(staging,item['path']);staged.parent.mkdir(parents=True,exist_ok=True)
                shutil.copyfile(item['source'],staged);staged.chmod(0o644)
                if setup.file_hash(staged)!=item['sha256']:raise setup.SetupError('Source modifiée pendant la copie cartographique.')
                prepared.append(item['path']);existing[item['path']]={k:item[k] for k in ('path','bytes','sha256')}
            if not reuse:
                print('Export des cinq images locales, sans accès au registre…',flush=True)
                save_images(staging/'images.tar',images)
                digest=setup.file_hash(staging/'images.tar')
                setup.write_json(staging/'images.tar.json',{'images':images,'sha256':digest})
                for relative in ('images.tar','images.tar.json'):
                    path=staging/relative
                    existing[relative]={'path':relative,'bytes':path.stat().st_size,'sha256':setup.file_hash(path)}
                    prepared.append(relative)
            if shutil.disk_usage(root).free<15_000_000_000:raise setup.SetupError('Marge physique insuffisante avant publication.')
            setup.write_json(staging/'transaction.json',{'original':old,'files':[{'path':relative,'had_previous':content.destination(root,relative).exists()} for relative in prepared]})
            # The marker blocks installation throughout the short publication.
            with marker.open('x',encoding='utf-8') as stream:json.dump({'kind':'SetupSurvie maps publication','staging':staging.name},stream)
            publishing=True
            for relative in prepared:
                target=content.destination(root,relative);target.parent.mkdir(parents=True,exist_ok=True)
                previous_path=content.destination(staging,'previous/'+relative)
                had_previous=target.exists()
                if had_previous:
                    previous_path.parent.mkdir(parents=True,exist_ok=True);target.replace(previous_path)
                content.destination(staging,relative).replace(target)
            updated={**old,'files':list(existing.values()),'map_bundles':{'geography':list(dict.fromkeys(geography_ids)),'routing':include_routing}}
            setup.write_json(root/'manifest.json',updated)
            marker.unlink();publishing=False
        except BaseException:
            if publishing:
                recover(root);publishing=False
            raise
        finally:
            if not publishing and staging.exists():shutil.rmtree(staging)
    return {'files':len(sources),'geography':geography_ids,'routing':include_routing,'image_archive_reused':reuse}


def refresh_lab(root,geography_ids,include_routing):
    import linux_lab as lab
    lab.checked_mount();root=setup.safe_path(root)
    if not root.is_relative_to(lab.MOUNT):raise setup.SetupError('Le kit doit rester sur le volume SSD dédié.')
    images,estimate=image_records(lab,include_routing)
    def save(path,records):
        lab.podman('save','--format','docker-archive','--multi-image-archive','-o',str(path),*[r['id'] for r in records],capture=True)
    result=refresh(root,lab.MOUNT/'data',geography_ids,include_routing,images,save,image_bytes=estimate)
    print('Cartes du kit actualisées :',result,flush=True)
    return result
