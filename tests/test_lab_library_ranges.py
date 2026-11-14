import io
import os
import json
from pathlib import Path
import re
import tempfile
import unittest
from unittest.mock import patch
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import lab_library_ranges as ranges


class RangeTransferTests(unittest.TestCase):
    @unittest.skipUnless(hasattr(os,'pwrite'),'Écriture positionnelle du laboratoire Linux uniquement.')
    def test_preserves_prefix_and_resumes_completed_ranges(self):
        payload = b'abcdefghijklmnopqrstuvwxyz'
        requested = []

        def response(request, timeout):
            start, end = map(int, re.search(r'bytes=(\d+)-(\d+)', request.headers['Range']).groups())
            requested.append((start, end))
            stream = io.BytesIO(payload[start:end + 1])
            stream.status = 206
            stream.headers = {'Content-Range': f'bytes {start}-{end}/{len(payload)}'}
            return stream

        with tempfile.TemporaryDirectory() as root:
            mount = Path(root)
            partial = mount / 'test.zim.part'
            partial.write_bytes(payload[:4])
            with patch.object(ranges.lab, 'MOUNT', mount), patch.object(ranges.lab, 'checked_mount'), \
                 patch.object(ranges, 'CHUNK', 5), patch.object(ranges.urllib.request, 'urlopen', side_effect=response):
                ranges.download(partial, 'test.zim', len(payload))
                self.assertEqual(partial.read_bytes(), payload)
                self.assertNotIn((0, 3), requested)
                previous = len(requested)
                ranges.download(partial, 'test.zim', len(payload))
                self.assertEqual(len(requested), previous)

    def test_rejects_server_ignoring_range_without_marking_complete(self):
        def response(request, timeout):
            stream = io.BytesIO(b'incorrect')
            stream.status = 200
            stream.headers = {}
            return stream

        with tempfile.TemporaryDirectory() as root:
            partial = Path(root) / 'test.zim.part'
            with patch.object(ranges.lab, 'MOUNT', Path(root)), patch.object(ranges.lab, 'checked_mount'), \
                 patch.object(ranges.urllib.request, 'urlopen', side_effect=response), patch.object(ranges.time, 'sleep'):
                with self.assertRaises(RuntimeError):
                    ranges.download(partial, 'test.zim', 4)
            state = json.loads(partial.with_suffix('.parts.json').read_text())
            self.assertEqual(state['completed'], [])


if __name__ == '__main__':
    unittest.main()
