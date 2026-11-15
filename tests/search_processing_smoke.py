"""Compare repeated and incremental selection on tiny fictional text, no corpus/model."""
import argparse
import json
from pathlib import Path
import sys
import tempfile
import time
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from pilot import catalogue,library,retrieval


def measure(guides,zims,count,text_size,compare_capacity=False):
    rows=[{'id':'zim:fixture_'+str(i%12)+'/Fire_'+str(i),'book':'fixture_'+str(i%12),
               'title':'Fire making, fictional article '+str(i),
               'excerpt':'Fire making and friction. Synthetic text, no instructions. '+str(i),
               '_text':('Fictional fire making and friction. '*600)[:text_size]+str(i),
               'kind':'article','language':'en','_rank':i%20} for i in range(count)]
    plan=retrieval.plan('comment faire du feu',library.search_terms('comment faire du feu'),library.SYNONYMS)
    measurements={};outcomes={};source=catalogue.revision
    modes=('repeated','incremental_8mb','incremental') if compare_capacity else ('repeated','incremental')
    for mode in modes:
        context=catalogue.SearchAnnotations(guides,zims,catalogue.Snapshot());normalize=retrieval.NormalCache()
        if mode=='incremental_8mb':normalize.MAX_BYTES=8_000_000
        started=time.monotonic();cpu=time.process_time();snapshots=[]
        with patch.object(catalogue,'revision',wraps=source) as checks:
            for end in range(20,count+1,20):
                items=[dict(row) for row in rows[:end]]
                if mode=='repeated':
                    for row in items:
                        info=catalogue.classification(row,guides,zims,catalogue.Snapshot())
                        row['classification']=info;row['domains']=info['domains']
                else:context.annotate(items)
                snapshots.append(retrieval.ordered(items,plan,10,normalizer=retrieval.normal if mode=='repeated' else normalize))
            measurements[mode]={'elapsed_ms':round((time.monotonic()-started)*1000),
                'cpu_ms':round((time.process_time()-cpu)*1000),'revision_checks':checks.call_count,
                'normalizations':normalize.misses if mode!='repeated' else None,
                'normalization_hits':normalize.hits if mode!='repeated' else None,
                'normalization_cache_bytes':normalize.bytes if mode!='repeated' else None}
        outcomes[mode]=snapshots
    assert all(value==outcomes['repeated'] for value in outcomes.values()),'Incremental selection changed an intermediate result'
    assert measurements['repeated']['revision_checks']==sum(range(20,count+1,20))
    assert measurements['incremental']['revision_checks']==12
    return {'candidates':count,'archives':12,'snapshots':count//20,'text_chars':text_size,'same_results':True,'measurements':measurements}


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path);args=parser.parse_args()
    with tempfile.TemporaryDirectory(prefix='setupsurvie-processing-') as folder:
        root=Path(folder);guides=root/'guides';zims=root/'zim';guides.mkdir();zims.mkdir()
        for i in range(12):(zims/('fixture_'+str(i)+'.zim')).write_bytes(b'fictional source metadata')
        receipt={'passed':True,'workloads':[measure(guides,zims,400,400),measure(guides,zims,200,20000,True)],
                 'real_corpus':False,'marc_performance':False}
        if args.output:args.output.write_text(json.dumps(receipt,ensure_ascii=False,indent=2))
        print(json.dumps(receipt,ensure_ascii=False))


if __name__=='__main__':main()
