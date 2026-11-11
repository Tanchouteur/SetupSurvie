import hashlib
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import audit_library


class LibraryAuditTests(unittest.TestCase):
    def test_missing_index_and_changed_document_are_detected(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);guides=root/'library/guides';guides.mkdir(parents=True)
            (guides/'book.pdf').write_bytes(b'changed')
            (guides/'other.txt').write_text('Useful unindexed document')
            (guides/'box.en.txt').write_text('Demonstration excluded')
            item={'id':'book','path':'library/guides/book.pdf','bytes':3,'sha256':hashlib.sha256(b'pdf').hexdigest()}
            coverage={'documents':[{'path':'book.pdf','status':'indexed'}]}
            with patch.object(audit_library.content,'catalog',return_value=[item]):
                report=audit_library.local_coverage(root,coverage)
            self.assertEqual(report['missing_index'],['other.txt'])
            self.assertEqual(report['integrity_errors'],['book'])
            self.assertEqual(report['files_checked'],2)


if __name__=='__main__':unittest.main()
