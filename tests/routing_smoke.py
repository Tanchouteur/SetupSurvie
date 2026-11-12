"""Real OSRM smoke test, run only on GitHub CI; no map/model download in the runner.

Uses the 1.3 KB synthetic OSM fixture and the pinned routing image. The image is
pulled only in the CI job. No Ollama, real account or real document is started.
"""
import asyncio
import json
from pathlib import Path
import sys
import tempfile
import time

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'scripts'))
import setup
import routing_prepare
from pilot import maps,routing


async def main():
    with tempfile.TemporaryDirectory(prefix='survie-routing-ci-') as folder:
        root=Path(folder);app=setup.Installation(root/'private');config=app.init('linux',root/'data',cpu=True)
        data=Path(config['data_dir']);started=False
        try:
            routing_prepare.build(data,ROOT/'fixtures/maps/routing-small.osm',[6.09,43.09,6.12,43.12],allow_download=True,progress=print)
            maps.ROOT=data/'library/maps'
            started=True;routing_prepare.start_services(app,config,'compose')
            for mode in ('foot','motorcycle','car'):
                identifier=app.compose(config,'ps','-q','router-'+mode,capture=True)
                inspected=json.loads(setup.run(['docker','inspect',identifier],capture=True))[0]
                ip=next(iter(inspected['NetworkSettings']['Networks'].values()))['IPAddress']
                routing.URLS[mode]='http://'+ip+':5000'
            results={}
            for mode in ('foot','motorcycle','car'):
                for attempt in range(30):
                    try:
                        results[mode]=await routing.calculate([{'lat':43.1,'lon':6.1,'title':'Départ'},{'lat':43.1,'lon':6.104,'title':'Arrivée'}],mode,4 if mode=='foot' else 40)
                        break
                    except Exception:
                        if attempt==29:raise
                        await asyncio.sleep(1)
            assert results['foot']['distance_m'] < results['motorcycle']['distance_m'] < results['car']['distance_m'],{m:r['distance_m'] for m,r in results.items()}
            assert results['foot']['duration_s']==round(results['foot']['distance_m']/4*3.6)
            assert all(len(r['geometry']['coordinates'])>=2 for r in results.values())
            print(json.dumps({'passed':True,'synthetic_osm_bytes':(ROOT/'fixtures/maps/routing-small.osm').stat().st_size,'distance_m':{m:r['distance_m'] for m,r in results.items()},'no_llm':True,'no_real_documents':True}))
        finally:
            if started:app.compose(config,'down','--volumes','--remove-orphans')


if __name__=='__main__':asyncio.run(main())
