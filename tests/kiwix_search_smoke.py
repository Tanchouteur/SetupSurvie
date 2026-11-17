"""Real pinned Kiwix + generated archives smaller than 1 MB; no corpus or model.
Run in a task worktree: python tests/kiwix_search_smoke.py
Uses task-compose when available, otherwise a unique CI Docker Compose project.
"""
import argparse
import asyncio
import json
import re
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import uuid
from unittest.mock import patch
from urllib.parse import urlencode

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from fastapi import HTTPException
from libzim.writer import Creator,Item,StringProvider,Hint
from pilot import library,store


class Article(Item):
    def __init__(self,path,title,text):
        super().__init__();self.path=path;self.title=title;self.text=text
    def get_path(self):return self.path
    def get_title(self):return self.title
    def get_mimetype(self):return 'text/html'
    def get_contentprovider(self):
        return StringProvider('<html><head><meta charset="UTF-8"><title>'+self.title+'</title></head><body><h1>'+self.title+'</h1><p>'+self.text+'</p></body></html>')
    def get_hints(self):return {Hint.FRONT_ARTICLE:True}


def create_archives(folder):
    specs=[('wikipedia_fr','fra',True,'_ftindex:yes'),('manual_en','eng',True,'_ftindex:yes'),
           ('multilingual','fra,eng',True,'_ftindex:yes'),('missing_tag_fr','fra',True,''),
           ('title_only_fr','fra',False,'_ftindex:no')]
    paths=[]
    for name,language,indexed,tags in specs:
        path=folder/(name+'.zim')
        with Creator(path).config_indexing(indexed,language.split(',')[0]) as creator:
            metadata={'Name':name,'Title':name,'Language':language,'Creator':'Synthetic test','Publisher':'SetupSurvie tests','Date':'2026-11-14','Description':'Fictional protocol fixture','Tags':tags}
            for key,value in metadata.items():creator.add_metadata(key,value)
            creator.set_mainpath('home');creator.add_item(Article('home','Accueil','Index fictif.'))
            creator.add_item(Article('Techniques_de_production_de_feu','Techniques de production de feu','Friction et percussion. Extrait fictif de test sans instructions pratiques.'))
            creator.add_item(Article('Fire_making','Fire making','Fire starting. Synthetic text, no practical instructions.'))
            creator.add_item(Article('Fire_by_friction','Fire making by friction','Friction and wood, fictional fire making topic. No actual instructions.'))
            creator.add_item(Article('Generateur_a_pedales','Fabrication d’un générateur à pédales','Générateur à pédales : construction et contrôles. Extrait fictif sans procédure.'))
            creator.add_item(Article('Pedal_generator','Pedal generator construction','Pedal generator materials and checks. Fictional fixture.'))
            creator.add_item(Article('Eau_potable','Guide de potabilisation de l’eau','Eau potable, purification et vérifications. Extrait fictif sans procédure.'))
            creator.add_item(Article('Shelter_construction','Shelter construction','Shelter construction and roof design. Fictional fixture.'))
            creator.add_item(Article('Mending_clothes','Mending clothes','Sewing and mending a garment. Fictional fixture without instructions.'))
            creator.add_item(Article('Solar_panel','Solar panel installation','Solar panel installation and electrical checks. Fictional fixture without instructions.'))
            for key,title,text in [
                ('Solar_question','Should I upgrade my electrical panel during a solar installation','Fictional solar panel installation question.'),
                ('Solar_hazards','Occupational hazards of solar panel installation','Fictional solar panel installation overview.'),
                ('Solar_quantity','How many solar panels should a beginner install?','Fictional solar panel installation question.'),
                ('Radio_screen','1998-2003 Mazda Radio LCD Screen Repair','Fictional radio repair example.'),
                ('Radio_howto','How to diagnose and repair a radio?','Fictional radio repair diagnostic example.'),
                ('Bicycle_history','Histoire du vélo','Fictional bicycle history example.'),
                ('History_specific','Any help with the History of a Fleetwood Bicycle 1963','Fictional bicycle history example.'),
                ('History_museum','Pedaling History Bicycle Museum','Fictional bicycle history example.'),
            ]:creator.add_item(Article(key,title,text))
            creator.add_item(Article('Bicycle_repair','Bicycle repair','Bicycle maintenance, fictional fixture without instructions.'))
            creator.add_item(Article('Couteaux','Affûtage des couteaux','Texte fictif : affûtage des couteaux, sans conseil réel.'))
            creator.add_item(Article('Tuyau_cuivre','Réparer un tuyau de cuivre','Extrait fictif : réparer un tuyau de cuivre, sans procédure réelle.'))
            creator.add_item(Article('Tuyaux_plastique','Réparer des tuyaux de plastique','Extrait fictif : réparer des tuyaux de plastique, sans procédure réelle.'))
            creator.add_item(Article("Compost_et_l'urbanisme","Compost et l'urbanisme",'Compost jardin, chemin fictif de contrôle.'))
            creator.add_item(Article('Compost & jardin','Compost et jardin','Compost jardin, chemin fictif de contrôle.'))
            creator.add_item(Article('Compost_été','Compost été','Compost jardin, chemin fictif de contrôle.'))
            creator.add_item(Article('Compost_&amp;','Compost symbole littéral','Compost jardin, chemin fictif de contrôle.'))
            creator.add_item(Article('Vegetable_canning','Vegetable canning and food preservation','Canning vegetables for food storage. Fictional fixture without instructions.'))
            creator.add_item(Article('Tool_sharpening','Tool sharpening','Tool sharpening and maintenance. Fictional fixture without instructions.'))
            creator.add_item(Article('Fictional_propulsion','Propulsion quantique fictive','Propulsion quantique : mots de test, sans technologie réelle.'))
            creator.add_redirection('Fire_alias','Alias de production de feu','Techniques_de_production_de_feu',{})
        paths.append(path)
    if sum(path.stat().st_size for path in paths)>1_000_000:raise RuntimeError('Synthetic fixture exceeded 1 MB')
    return paths


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path)
    args=parser.parse_args()
    image=json.loads((ROOT/'deploy/versions.json').read_text())['images']['kiwix']
    checks=[]
    def check(value,label,details=None):
        if not value:raise AssertionError(label+(': '+json.dumps(details,ensure_ascii=False) if details else ''))
        checks.append(label)
    with tempfile.TemporaryDirectory(prefix='.kiwix-search-',dir=ROOT) as temporary:
        folder=Path(temporary);archives=folder/'zim';archives.mkdir();paths=create_archives(archives)
        compose=folder/'compose.yaml'
        compose.write_text('services:\n  kiwix:\n    image: '+image+'\n    user: "0:0"\n    entrypoint: ["/usr/local/bin/kiwix-serve"]\n    volumes:\n      - '+json.dumps(str(archives)+':/data:ro')+'\n    command: '+json.dumps(['--port=8080']+['/data/'+p.name for p in paths])+'\n')
        command=(['task-compose'] if shutil.which('task-compose') else ['docker','compose','--project-name','setupsurvie-search-'+uuid.uuid4().hex[:10]])+['-f',str(compose)]
        async def real_get(path,maximum=2_000_000):
            # HTTP runs inside our synthetic service. No published port, host
            # credentials, model or user files are needed by the service.
            process=await asyncio.create_subprocess_exec(*command,'exec','-T','kiwix','wget','-S','-O','-','http://127.0.0.1:8080'+path,stdout=asyncio.subprocess.PIPE,stderr=asyncio.subprocess.PIPE,cwd=ROOT)
            try:raw,detail=await process.communicate()
            except asyncio.CancelledError:
                if process.returncode is None:process.kill()
                await process.wait();raise
            if process.returncode:
                error=HTTPException(404,'Synthetic Kiwix HTTP request failed');status=re.search(rb'HTTP/\S+ (\d+)',detail)
                if status:error.upstream_status=int(status[1])
                raise error
            if len(raw)>maximum:raise HTTPException(413,'Synthetic response exceeded bound')
            return raw,'application/json' if path.startswith('/suggest?') else 'application/xml'
        async def run():
            for _ in range(60):
                try:await real_get('/catalog/v2/entries?count=1');break
                except HTTPException:await asyncio.sleep(.1)
            else:raise RuntimeError('Synthetic Kiwix did not become ready')
            with patch.object(store,'ROOT',folder/'state'),patch.object(library,'get',real_get):
                store.init()
                check(len(await library.books())==5,'Catalogue reads five actual generated archives')
                try:await real_get('/search?'+urlencode({'books.name':'multilingual','pattern':'fire','format':'xml'}))
                except HTTPException as error:check(getattr(error,'upstream_status',None)==400,'Single multilingual archive is rejected with native HTTP 400')
                else:raise AssertionError('Pinned server unexpectedly accepted multilingual metadata')
                root=folder/'state/archive-index';complement=library.archive_index.build_archive(archives/'multilingual.zim',root)
                check(complement['has_fulltext_index'] and not complement['kiwix_language_compatible'] and complement['status']=='ready','Present native index gets a local complement when its language metadata is incompatible')
                (root/'manifest.json').write_text(json.dumps({'schema':1,'archives':{'multilingual.zim':complement}}))
                restored=await library.search('faire du feu',collection='multilingual')
                check(any(row.get('match')=='local_index' and row['id'].startswith('zim:multilingual/') for row in restored),'Local complement restores actual multilingual article retrieval')
                check(restored.coverage['native_incompatible']==0 and restored.coverage['locally_indexed']==1,'Prepared multilingual collection is no longer an unresolved native failure')
                for query in ['faire du feu','allumer un feu','peux-tu m’expliquer comment faire du feu',
                              'Fait un synthese sur les info des document sur comment faire du feux']:
                    found=await library.search(query)
                    check(any(r['id']=='zim:wikipedia_fr/Techniques_de_production_de_feu' for r in found),query+' reaches French article')
                    check(any(r['id']=='zim:manual_en/Fire_making' for r in found),query+' reaches English article')
                    check(all('<b>' not in r['title'] for r in found),'Highlights do not leak into titles: '+query)
                friction=await library.search('Des méthodes d’allumage au frottement (comme le feu de bois) ?',limit=20)
                check(any(row['id']=='zim:wikipedia_fr/Techniques_de_production_de_feu' for row in friction),'Friction request reaches the actual French friction excerpt')
                check(any(row['id']=='zim:manual_en/Fire_by_friction' for row in friction),'Friction request reaches the actual English friction topic')
                check('Friction and wood' in (await library.source('zim:manual_en/Fire_by_friction'))['text'],'The selected fictional friction source opens')
                for query,expected in [('fabriquer un générateur à pédales','Generateur_a_pedales'),('rendre eau potable','Eau_potable'),('toit abri','Shelter_construction'),('inconnu eau potable','Eau_potable')]:
                    found=await library.search(query)
                    check(any(r['id'].endswith('/'+expected) for r in found),query+' reaches an actual indexed technical article',{'ids':[r['id'] for r in found],'coverage':found.coverage})
                scoped=await library.search('faire du feu dans Wikipédia')
                check(bool(scoped) and all(r['id'].startswith('zim:wikipedia_fr/') for r in scoped),'Wikipedia is a real archive scope')
                for query,target in [('affûter un couteau','Couteaux'),('réparer des tuyaux de cuivre','Tuyau_cuivre')]:
                    found=await library.search(query,collection='wikipedia',limit=20);ids=[row['id'] for row in found]
                    check(bool(ids) and ids[0]=='zim:wikipedia_fr/'+target,query+' crosses number variants in native fulltext',{'ids':ids})
                    check('zim:wikipedia_fr/Tuyaux_plastique' not in ids,query+' retains its separate subject constraints')
                    check('fictif' in (await library.source(found[0]['id']))['text'],query+' opens its actual synthetic source')
                for query,expected in [('recoudre un vêtement','Mending_clothes'),('installer un panneau solaire','Solar_panel'),('faire des conserves de légumes','Vegetable_canning'),('aiguiser un outil','Tool_sharpening')]:
                    found=await library.search(query,limit=5,collection='manualen',domain='resilience')
                    check(bool(found) and found[0]['id']=='zim:manual_en/'+expected,query+' ranks its actual English source first',{'ids':[r['id'] for r in found],'coverage':found.coverage})
                    check(found[0].get('match')!='title',query+' has an actual fulltext match, not only a title suggestion')
                for query,target,context in [
                    ('installer un panneau solaire','Solar_panel',['Solar_question','Solar_hazards','Solar_quantity']),
                    ('réparer un poste radio','Radio_howto',['Radio_screen']),
                    ('histoire du vélo','Bicycle_history',['History_specific','History_museum']),
                ]:
                    found=await library.search(query,limit=20,collection='manualen');ids=[row['id'].split('/')[-1] for row in found]
                    check(bool(ids) and ids[0]==target,query+' prioritizes a direct title over incidental context',{'ids':ids})
                    check(all(key in ids for key in context),query+' preserves its contextual sources',{'ids':ids})
                    check('Fictional' in (await library.source('zim:manual_en/'+target))['text'],query+' opens its selected fictional source')
                guides=folder/'guides';guides.mkdir()
                for name,title,text in [
                    ('solar.fr.txt','Les panneaux solaires modernes','Analyse fictive : installer un panneau solaire influence le coût de l’énergie, sans procédure.'),
                    ('bicycle.fr.txt','Les vélos d’aujourd’hui','Analyse fictive de la réparation des vélos et de leur durée de vie, sans étapes.'),
                ]:
                    (guides/name).write_text(text,encoding='utf-8')
                (guides/'metadata.json').write_text(json.dumps([
                    {'path':'solar.fr.txt','title':'Les panneaux solaires modernes','language':'fr'},
                    {'path':'bicycle.fr.txt','title':'Les vélos d’aujourd’hui','language':'fr'},
                ]),encoding='utf-8')
                with patch.object(library,'GUIDES',guides):
                    library.index_guides()
                    for query,target,background in [('installer un panneau solaire','Solar_panel','solar.fr.txt'),('réparer un vélo','Bicycle_repair','bicycle.fr.txt')]:
                        for domain in ('all','resilience'):
                            found=await library.search(query,limit=20,domain=domain)
                            ids=[row['id'] for row in found]
                            check(bool(ids) and ids[0].endswith('/'+target),query+' prioritizes the native task title in '+domain,{'ids':ids})
                            check('guide:'+background in ids,query+' retains the broader guide in '+domain,{'ids':ids})
                tagged=await library.search('allumer un feu',collection='missingtagfr')
                check(bool(tagged) and tagged.coverage['searched']==1,'Missing ftindex tag does not hide a working fulltext index')
                titles=await library.search('allumer un feu',collection='titleonlyfr')
                check(any(r.get('match')=='title' for r in titles),'Title fallback works without fulltext index')
                check(titles.coverage['status']=='partial','Missing fulltext coverage is explicit')
                for query,target in [('couteau','Couteaux'),('couteaux','Couteaux'),('tuyau cuivre','Tuyau_cuivre'),('tuyaux cuivre','Tuyau_cuivre')]:
                    found=await library.search(query,collection='titleonlyfr',limit=20)
                    check(any(r['id']=='zim:title_only_fr/'+target for r in found),query+' crosses number variants in title-only fallback',{'ids':[r['id'] for r in found]})
                for collection in ('wikipedia','titleonlyfr'):
                    found=await library.search('compost',limit=20,collection=collection)
                    check(len(found)==4 and len({row['id'] for row in found})==4,'Escaped paths and a literal entity have no phantom duplicate in '+collection,{'ids':[row['id'] for row in found]})
                    for row in found:
                        source=await library.source(row['id'])
                        check('Compost' in source['text'],'Actual suggested path opens locally: '+row['id'])
                    if collection=='wikipedia':
                        check(all('compost' in row['excerpt'].lower() and 'chemin fictif' in row['excerpt'].lower() for row in found),'Native XML excerpts retain highlighted matches and following words')
                source=await library.source('zim:wikipedia_fr/Techniques_de_production_de_feu')
                check('Friction' in source['text'] and source['language'] in ('fr','fra'),'Actual source can be read with its language after retrieval')
                alias=await library.source('zim:wikipedia_fr/Fire_alias')
                check('Friction' in alias['text'] and alias['id'].endswith('/Fire_alias'),'A generated Kiwix alias reaches its actual target')
                native,_=await real_get('/search?'+urlencode({'books.name':'wikipedia_fr','pattern':'propulsion quantique','format':'xml'}))
                check(b'Fictional_propulsion' in native,'Two literal words reach the generated native document')
                native,_=await real_get('/search?'+urlencode({'books.name':'wikipedia_fr','pattern':'propulsion AND quantique','format':'xml'}))
                check(b'Fictional_propulsion' not in native,'Do not force Boolean AND unsupported by the pinned parser')
                try:await real_get('/search?'+urlencode({'books.filter.lang':'fra','pattern':'feu','format':'xml'}))
                except HTTPException as error:check(getattr(error,'upstream_status',None)==400,'Broad multilingual request is rejected by the pinned server')
        try:
            subprocess.run([*command,'up','-d'],check=True,cwd=ROOT,stdout=subprocess.DEVNULL)
            asyncio.run(run())
        finally:subprocess.run([*command,'down','--volumes','--remove-orphans'],check=True,cwd=ROOT,stdout=subprocess.DEVNULL)
        receipt={'passed':True,'kiwix_image':image,'archives':len(paths),'total_bytes':sum(p.stat().st_size for p in paths),'checks':checks,'real_model':False,'real_corpus':False}
        if args.output:args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
        print(json.dumps(receipt,ensure_ascii=False))


if __name__=='__main__':main()
