"""Frozen plan audit is read-only and never starts transfers or hashes a corpus."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import audit_selection as audit


class SelectionAuditTests(unittest.TestCase):
    def test_sizes_overlaps_supplements_and_unmatched_are_reported_without_touching_plan(self):
        with tempfile.TemporaryDirectory() as folder:
            plan=Path(folder)/'plan.json'
            def item(name):return {'id':name,'title':name,'path':'library/zim/'+name+'_2026-01.zim','bytes':100,'sha256':'a'*64,'url':'https://example.org/'+name+'.zim','language':'en'}
            names=['gutenberg_en_all','gutenberg_en_lcc-t','wiki_en_all','appropedia_en_all','unknown_en_all']
            plan.write_text(json.dumps({'schema':1,'items':[item(n) for n in names]}));before=plan.read_bytes()
            entries=[{'filename':n+'_2026-01.zim','name':n,'title':n,'summary':''} for n in names[:-1]]
            with patch.object(audit.ks,'fetch',side_effect=AssertionError('No network')),patch.object(audit.content,'download',side_effect=AssertionError('No download')):
                report=audit.audit(plan,entries)
            self.assertEqual(report['total_bytes'],500)
            self.assertEqual(set(report['bytes_by_status']),{'supplement','overlap','out_of_scope','relevant_reference','manual_review'})
            self.assertEqual(before,plan.read_bytes())


if __name__=='__main__':unittest.main()
