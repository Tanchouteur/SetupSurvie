"""Real OSRM smoke test, run only on GitHub CI; no map/model download in the runner.

Uses the 1.3 KB synthetic OSM fixture and the pinned routing image. The image is
pulled only in the CI job. No Ollama, real account or real document is started.
"""
import asyncio
import json
from pathlib import Path
import sys
import tempfile
import shutil
from unittest.mock import patch
import time
import subprocess

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'scripts'))
import setup
import routing_prepare
from pilot import maps,routing


def ci_engine(*args,**kwargs):
    try:return routing_prepare.engine(*args,**kwargs)
    except setup.SetupError as exc:
        cause=exc.__cause__
        if isinstance(cause,subprocess.CalledProcessError):
            print('Synthetic graph engine diagnostics:',(cause.stdout or '')[-4000:],(cause.stderr or '')[-4000:],flush=True)
        raise


async def main():
    with tempfile.TemporaryDirectory(prefix='survie-routing-ci-') as folder:
        root=Path(folder);app=setup.Installation(root/'private');config=app.init('linux',root/'data',cpu=True)
        data=Path(config['data_dir']);started=False
        try:
            # This tiny CI fixture does not need the production 10 GB build reserve.
            # Keep the application checks intact; verify a real 2 GB minimum here.
            assert shutil.disk_usage(root).free>2_000_000_000,'CI needs 2 GB for the pinned engine and tiny graph'
            with patch.object(routing_prepare.content,'check_capacity'):
                routing_prepare.build(data,ROOT/'fixtures/maps/routing-small.osm',[6.09,43.09,6.12,43.12],allow_download=True,progress=print,runner=ci_engine)
            maps.ROOT=data/'library/maps'
            started=True;routing_prepare.start_services(app,config,'compose')
            for mode in ('foot','motorcycle','car'):
                identifier=app.compose(config,'ps','-q','router-'+mode,capture=True)
                inspected=json.loads(setup.run(['docker','inspect',identifier],capture=True))[0]
                ip=next(iter(inspected['NetworkSettings']['Networks'].values()))['IPAddress']
                routing.URLS[mode]='http://'+ip+':5000'
            results={}
            for mode in ('foot','motorcycle','car'):
                for attempt in range(5):
                    try:
                        results[mode]=await routing.calculate([{'lat':43.1,'lon':6.1,'title':'Départ'},{'lat':43.1,'lon':6.104,'title':'Arrivée'}],mode,4 if mode=='foot' else 40)
                        break
                    except Exception as exc:
                        print('Routing request',mode,'attempt',attempt+1,repr(exc),flush=True)
                        if attempt==4:
                            for candidate in ('foot','motorcycle','car'):
                                identifier=app.compose(config,'ps','-q','router-'+candidate,capture=True)
                                if identifier:
                                    details=routing_prepare.engine('compose','logs',identifier,check=False)
                                    print('Synthetic service',candidate,(details.stdout or '')[-2500:],(details.stderr or '')[-2500:],flush=True)
                            raise
                        await asyncio.sleep(1)
            access_results={}
            for mode in ('foot','motorcycle','car'):
                proposal=await routing.accesses(43.099,6.1,mode)
                assert proposal['candidates'],(mode,proposal)
                candidate=proposal['candidates'][0]
                assert 100<candidate['distance_m']<1000,candidate
                selected=await routing.calculate([{'lat':43.099,'lon':6.1,'title':'Point éloigné','access_token':candidate['token']},
                                                 {'lat':43.1,'lon':6.104,'title':'Arrivée'}],mode,4 if mode=='foot' else 40)
                assert selected['connectors'] and selected['points'][0]['lat']==43.099
                assert selected['points'][0]['access_selected']
                access_results[mode]=candidate['distance_m']
            assert results['foot']['distance_m'] < results['motorcycle']['distance_m'] < results['car']['distance_m'],{m:r['distance_m'] for m,r in results.items()}
            assert results['foot']['duration_s']==round(results['foot']['distance_m']/4*3.6)
            assert all(len(r['geometry']['coordinates'])>=2 for r in results.values())
            print(json.dumps({'passed':True,'synthetic_osm_bytes':(ROOT/'fixtures/maps/routing-small.osm').stat().st_size,'distance_m':{m:r['distance_m'] for m,r in results.items()},'access_offsets_m':access_results,'no_llm':True,'no_real_documents':True}))
        finally:
            if started:app.compose(config,'down','--volumes','--remove-orphans')


if __name__=='__main__':asyncio.run(main())
