from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from pilot import durable


class WindowsPublicationTests(unittest.TestCase):
    def test_temporary_reader_lock_is_retried_without_losing_previous_file(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); source = root/'new'; target = root/'current'
            source.write_bytes(b'new'); target.write_bytes(b'old')
            replace = durable.os.replace
            calls = 0
            def locked_then_replace(a, b):
                nonlocal calls
                calls += 1
                if calls < 3:
                    self.assertEqual(target.read_bytes(), b'old')
                    error = PermissionError('Windows sharing violation'); error.winerror = 32
                    raise error
                replace(a, b)
            with patch.object(durable.os, 'replace', side_effect=locked_then_replace), patch.object(durable.time, 'sleep'):
                durable.publish(source, target)
            self.assertEqual(calls, 3)
            self.assertEqual(target.read_bytes(), b'new')

    def test_unrelated_permission_error_is_not_retried(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); source = root/'new'; source.write_bytes(b'new')
            with patch.object(durable.os, 'replace', side_effect=PermissionError('ordinary denial')) as replace, patch.object(durable.time, 'sleep') as sleep:
                with self.assertRaises(PermissionError): durable.publish(source, root/'target')
            self.assertEqual(replace.call_count, 1)
            sleep.assert_not_called()
