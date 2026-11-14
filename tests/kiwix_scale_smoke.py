"""135 tiny generated archives, real pinned Kiwix, no downloaded corpus or model."""
import argparse
import asyncio
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
import uuid
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from libzim.writer import Creator
from kiwix_search_smoke import Article
from pilot import library,store,archive_index,kiwix_queries,search_cache
from fastapi import HTTPException


DOCUMENTS=[
 ('Fire','Techniques de production de feu','Fire making, friction. Fixture fictive sans instructions.'),
 ('Generator','Fabrication d’un générateur à pédales','Pedal generator construction. Fixture fictive.'),
 ('Water','Guide de purification de l’eau','Water purification and drinking water. Fixture fictive.'),
 ('Bicycle','Réparation vélo et crevaison','Bicycle puncture repair. Fixture fictive.'),
 ('Clothes','Recoudre un vêtement','Sewing clothes, fictional fixture.'),
 ('Solar','Installation panneau solaire','Solar panel installation, fictional fixture.'),
 ('Seeds','Conserver les semences','Seeds storage and preservation, fictional fixture.'),
 ('Comet','Trajectoire comète','Trajectoire comète, exemple scientifique fictif.'),
 ('Language','Grammaire conjugaison','Grammaire conjugaison, exemple pédagogique fictif.'),
 ('Music','Histoire musique','Histoire musique, fixture culturelle fictive.'),
 ('Fraction','Calcul fraction','Calcul fraction, exercice fictif.'),
]


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path);args=parser.parse_args()
    image=json.loads((ROOT/'deploy/versions.json').read_text())['images']['kiwix'];checks=[]
    def check(ok,label):
        if not ok:raise AssertionError(label)
        checks.append(label)
    with tempfile.TemporaryDirectory(prefix='.kiwix-scale-',dir=ROOT) as tmp:
        folder=Path(tmp);zims=folder/'zim';zims.mkdir();state=folder/'state';manifest={}
        for i in range(135):
            name=('wikipedia_fr' if i==0 else 'appropedia_en' if i==1 else 'wikibooks_fr' if i==2 else 'fixture_'+str(i))
            language='fra,eng' if i>=120 else 'eng' if i%3 else 'fra';path=zims/(name+'.zim')
            with Creator(path).config_indexing(True,language.split(',')[0]) as creator:
                for key,value in {'Name':name,'Title':'Fixture '+str(i),'Language':language,'Creator':'SetupSurvie synthetic tests','Publisher':'Synthetic','Date':'2026-11-14','Description':'Tiny fictional fixture','Tags':'_ftindex:yes'}.items():creator.add_metadata(key,value)
                creator.set_mainpath('Home');creator.add_item(Article('Home','Accueil fictif','Tiny synthetic index.'))
                for target,title,body in DOCUMENTS:creator.add_item(Article(target,title,body))
            manifest[path.name]=archive_index.build_archive(path,state/'archive-index',reserve=100_000_000)
        (state/'archive-index/manifest.json').write_text(json.dumps({'schema':1,'archives':manifest}))
        total=sum(p.stat().st_size for p in zims.iterdir());check(total<12_000_000,'Generated corpus remains below 12 MB')
        compose=folder/'compose.yaml';compose.write_text('services:\n  kiwix:\n    image: '+image+'\n    user: "0:0"\n    entrypoint: ["/usr/local/bin/kiwix-serve"]\n    volumes:\n      - '+json.dumps(str(zims)+':/data:ro')+'\n    command: '+json.dumps(['--port=8080']+['/data/'+name for name in manifest])+'\n')
        command=(['task-compose'] if shutil.which('task-compose') else ['docker','compose','--project-name','setupsurvie-scale-'+uuid.uuid4().hex[:10]])+['-f',str(compose)]
        calls=0
        async def get(path,maximum=2_000_000):
            nonlocal calls;calls+=1
            process=await asyncio.create_subprocess_exec(*command,'exec','-T','kiwix','wget','-q','-O','-','http://127.0.0.1:8080'+path,stdout=asyncio.subprocess.PIPE,stderr=asyncio.subprocess.DEVNULL,cwd=ROOT)
            try:raw,_=await process.communicate()
            except asyncio.CancelledError:
                if process.returncode is None:process.kill()
                await process.wait();raise
            if process.returncode:raise HTTPException(502,'Synthetic service unavailable')
            if len(raw)>maximum:raise HTTPException(413,'Synthetic response too large')
            return raw,'application/json' if path.startswith('/suggest') else 'application/xml'
        measurements=[]
        async def run():
            for _ in range(60):
                try:await get('/catalog/v2/entries?count=1');break
                except HTTPException:await asyncio.sleep(.1)
            else:raise RuntimeError('Synthetic Kiwix unavailable')
            with patch.object(store,'ROOT',state),patch.object(library,'get',get),patch.object(search_cache,'RESERVE_BYTES',0),patch.dict('os.environ',{'ZIM_DIR':str(zims)}):
                store.init();check(len(await library.books())==135,'Actual catalogue contains 135 generated archives')
                for query,target in [('faire du feu','Fire'),('fabriquer un générateur à pédales','Generator'),('rendre eau potable','Water'),('réparer vélo crevaison','Bicycle'),('trajectoire comète','Comet'),('grammaire conjugaison','Language'),('histoire musique','Music'),('calcul fraction','Fraction')]:
                    started=time.monotonic();first=None;updates=0
                    async def update(rows):
                        nonlocal first,updates;updates+=1
                        if rows and first is None:first=round((time.monotonic()-started)*1000)
                    found=await library.search(query,on_update=update,budget=60)
                    check(any(row['id'].endswith('/'+target) for row in found),'Retrieval finds '+target)
                    check(found.coverage['searched']+found.coverage['locally_indexed']==135 and found.coverage['failed']==0 and found.coverage['not_searched']==0,'All 135 collections examined for '+target)
                    check(first is not None and updates>1,'Progressive results delivered for '+target)
                    measurements.append({'case':target,'first_results_ms':first,'total_ms':round((time.monotonic()-started)*1000),'updates':updates,'coverage':found.coverage['status']})
                before=calls;await library.search('faire du feu',budget=60)
                check(calls==before,'Warm repeated query reuses validated successful responses')
                await kiwix_queries.close()
                found=await library.search('faire du feu',budget=60)
                check(calls==before and found.coverage['cache_hits']>0 and any(row['id'].endswith('/Fire') for row in found),'Disk cache reuses real native responses after clearing process memory')
            await kiwix_queries.close()
        try:
            subprocess.run([*command,'up','-d'],check=True,cwd=ROOT,stdout=subprocess.DEVNULL);asyncio.run(run())
        finally:subprocess.run([*command,'down','--volumes','--remove-orphans'],check=True,cwd=ROOT,stdout=subprocess.DEVNULL)
        receipt={'passed':True,'archives':135,'total_bytes':total,'kiwix_image':image,'checks':checks,'measurements':measurements,'real_corpus':False,'real_model':False,'marc_performance':False}
        if args.output:args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(receipt,ensure_ascii=False,indent=2))
        print(json.dumps(receipt,ensure_ascii=False))


if __name__=='__main__':main()
