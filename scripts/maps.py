#!/usr/bin/env python3
"""Prepare bounded offline map extracts, retaining attribution and verification."""
import argparse
import json
from pathlib import Path
import subprocess
import time

import content
import setup
from pilot import durable


def prepare(root,tool,*,storage_root=None,max_bytes=20_000_000_000):
    root=setup.safe_path(root)
    recipe=json.loads((setup.ROOT/'deploy/map-catalog.json').read_text())
    maps=content.destination(root,'library/maps');durable.mkdir(maps)
    manifest=maps/'manifest.json'
    previous=json.loads(manifest.read_text()) if manifest.exists() else {'maps':[]}
    records={m['id']:m for m in previous['maps']}
    with content.locked(root/'catalog/content.lock'):
        for item in recipe['maps']:
            name=item['id']+'-'+recipe['edition']+'.pmtiles'
            final=content.destination(root,'library/maps/'+name)
            prior=records.get(item['id'],{})
            if final.exists():
                if prior.get('path')!=name or setup.file_hash(final)!=prior.get('sha256'):
                    raise setup.SetupError('Carte existante non vérifiée, conservée : '+name)
                continue
            content.check_capacity(root,max_bytes,storage_root=storage_root)
            partial=final.with_suffix('.pmtiles.part')
            if partial.exists():raise setup.SetupError('Extraction partielle existante : '+str(partial))
            command=[str(tool),'extract',recipe['source'],str(partial),
                     '--bbox='+','.join(map(str,item['bbox'])),
                     '--maxzoom='+str(item['maxzoom']),'--download-threads=3']
            log=root/'catalog'/('map-'+item['id']+'.log')
            print('Extraction :',item['title'],flush=True)
            with log.open('w') as out:
                process=subprocess.Popen(command,stdout=out,stderr=subprocess.STDOUT)
                try:
                    while process.poll() is None:
                        size=partial.stat().st_size if partial.exists() else 0
                        if size>max_bytes:raise setup.SetupError('Extraction trop volumineuse ; fichier non publié.')
                        content.check_capacity(root,10_000_000,storage_root=storage_root)
                        setup.write_json(root/'catalog/map-progress.json',{'id':item['id'],'status':'extracting','bytes':size})
                        time.sleep(1)
                    if process.returncode:raise setup.SetupError('Extraction interrompue ; consulter '+str(log))
                finally:
                    if process.poll() is None:
                        process.terminate()
                        try:process.wait(timeout=10)
                        except subprocess.TimeoutExpired:process.kill();process.wait()
            if not partial.is_file() or partial.stat().st_size>max_bytes:raise setup.SetupError('Taille de carte non valide.')
            subprocess.run([str(tool),'verify',str(partial)],check=True,stdout=subprocess.DEVNULL)
            record={**item,'path':name,'bytes':partial.stat().st_size,'sha256':setup.file_hash(partial),
                    'source':recipe['source'],'edition':recipe['edition'],'attribution':recipe['attribution']}
            durable.sync_file(partial);partial.chmod(0o644);durable.publish(partial,final)
            records[item['id']]=record
            setup.write_json(manifest,{'schema':1,'maps':list(records.values())})
            print('Carte vérifiée :',name,record['bytes'],flush=True)
        guide=content.destination(root,'library/guides/MAP-cartes-sud.fr.html')
        durable.write_bytes(guide,('<!doctype html><html lang="fr"><meta charset="utf-8"><title>Cartes hors ligne de Solliès-Ville et du Sud</title>'
            '<h1>Cartes hors ligne : Solliès-Ville, Var, PACA, Occitanie et Corse</h1>'
            '<p>Carte des routes, chemins, bâtiments, localités et cours d’eau. '
            'Fond OpenStreetMap/Protomaps du '+recipe['edition']+'.</p>'
            '<p><a href="/cartes.html" target="_blank" rel="noopener">Ouvrir les cartes locales</a></p>'
            '<p>Le fond régional est détaillé jusqu’au zoom 13 ; les alentours de Solliès-Ville jusqu’au zoom 15. '
            'La carte ne calcule pas d’itinéraire et ne garantit pas les conditions actuelles des routes, '
            'l’accès à un lieu ou la potabilité d’un point d’eau. Le fond seul ne contient pas de relief altimétrique. Les altitudes se préparent séparément depuis Données locales.</p>'
            '<p>Attribution : '+recipe['attribution']+'. Ces cartes se consultent sans Internet.</p></html>').encode('utf-8'))
        guide.chmod(0o644)
        setup.write_json(root/'catalog/map-progress.json',{'status':'done','maps':list(records)})
    return records


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--lab',action='store_true');parser.add_argument('--data-dir')
    parser.add_argument('--tool',required=True,type=Path)
    args=parser.parse_args()
    scope=None
    if args.lab:
        import linux_lab as lab
        lab.checked_mount();scope=lab.MOUNT
        if args.data_dir:parser.error('--lab choisit le volume dédié.')
        root=lab.MOUNT/'data'
    elif args.data_dir:root=Path(args.data_dir)
    else:parser.error('--lab ou --data-dir requis.')
    prepare(root,args.tool,storage_root=scope)


if __name__=='__main__':main()
