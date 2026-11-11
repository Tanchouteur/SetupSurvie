#!/usr/bin/env python3
"""Verify actual search/reading tools over HTTP, without generating an AI answer."""
import argparse
import json
from pathlib import Path
import urllib.parse
import urllib.request

import setup
import content


def local_coverage(root,coverage):
    guides=root/'library/guides'
    expected={p.relative_to(guides).as_posix() for p in guides.rglob('*')
              if p.is_file() and not p.is_symlink() and p.suffix.lower() in ('.pdf','.html','.txt','.md','.epub')
              and not p.name.startswith(('box.','boite.'))}
    indexed={r['path'] for r in coverage['documents'] if r['status']=='indexed'}
    errors=[]
    for item in content.catalog():
        path=content.destination(root,item['path'])
        if item['path'].startswith('library/guides/') and path.is_file():
            if path.stat().st_size!=item['bytes'] or setup.file_hash(path)!=item['sha256']:errors.append(item['id'])
    return {'missing_index':sorted(expected-indexed),'integrity_errors':errors,'files_checked':len(expected)}


def audit(base,data_root=None):
    def get(path):
        with urllib.request.urlopen(base+path,timeout=90) as response:return json.load(response)
    fixture=json.loads((setup.ROOT/'fixtures/evaluation/library-coverage.json').read_text())
    report={'cases':[],'coverage':get('/api/library/coverage'),'maps':get('/api/maps')['maps']}
    for case in fixture['cases']:
        results=get('/api/search?'+urllib.parse.urlencode({'q':case['query'],'language':'','limit':3}))['results'][:5]
        found=next((item for item in results if case['expected'] in item['id']),None)
        record={**case,'found':bool(found)}
        if found:
            source=get('/api/source?'+urllib.parse.urlencode({'id':found['id']}))
            record.update(source_id=source['id'],url=source['url'],readable=bool(source.get('text','').strip()),
                          characters=len(source.get('text','')),title=source['title'])
            local=urllib.parse.urlsplit(source['url'])
            if local.scheme or not local.path.startswith('/guides/'):raise ValueError('Lien de guide local attendu.')
            with urllib.request.urlopen(base+local.path,timeout=30) as response:
                prefix=response.read(32);record['original_accessible']=response.status==200
                if '.pdf' in local.path:record['original_accessible'] &= prefix.startswith(b'%PDF-')
        report['cases'].append(record)
        print(case['id'], 'OK' if record.get('readable') and record.get('original_accessible') else 'À CORRIGER',flush=True)
    report['passed']=all(c.get('found') and c.get('readable') and c.get('original_accessible') for c in report['cases'])
    report['index_issues']=[r for r in report['coverage']['documents'] if r['status']!='indexed']
    report['passed'] &= report['coverage'].get('status')=='ready' and not report['index_issues'] and len(report['maps'])>=2
    inventory=get('/api/inventory')
    report['archives_not_ready']=[b['id'] for b in inventory['books'] if not b['ready']]
    report['passed'] &= not report['archives_not_ready']
    if data_root:
        report['local_files']=local_coverage(data_root,report['coverage'])
        report['map_integrity_errors']=[m['id'] for m in report['maps']
            if setup.file_hash(content.destination(data_root,'library/maps/'+m['path']))!=m['sha256']]
        report['passed'] &= not report['local_files']['missing_index'] and not report['local_files']['integrity_errors'] and not report['map_integrity_errors']
    return report


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--url',default='http://127.0.0.1:8080')
    parser.add_argument('--data-dir',type=Path)
    parser.add_argument('--output',required=True,type=Path);args=parser.parse_args()
    result=audit(args.url.rstrip('/'),args.data_dir);setup.write_json(args.output,result)
    print('Résultat :',result['passed'])
    raise SystemExit(0 if result['passed'] else 1)


if __name__=='__main__':main()
