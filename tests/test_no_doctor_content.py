"""The offline book must include every chapter and its reference appendices."""
from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import content


class NoDoctorCatalogTests(unittest.TestCase):
    def test_complete_2025_book_is_pinned_to_its_publisher(self):
        parts=[i for i in content.catalog() if i['pack']=='no-doctor']
        expected={f'{n:02}' for n in range(1,24)}|{'fm','toc','int','gp','info','gloss','resc','indx','bm'}
        self.assertEqual(len(parts),32)
        self.assertEqual({p['book_part'] for p in parts},expected)
        for part in parts:
            self.assertEqual(part['edition'],'2025')
            self.assertEqual(part['language'],'en')
            self.assertTrue(part['url'].startswith('https://hesperian.org/wp-content/uploads/pdf/en_wtnd_2025/'))
            self.assertEqual(part['source_url'],'https://languages.hesperian.org/pages/en/pdf.html')
            self.assertTrue(part['commercial_review'])


if __name__=='__main__':unittest.main()
