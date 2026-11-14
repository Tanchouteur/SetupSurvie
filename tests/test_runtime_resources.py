import sys
from pathlib import Path
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import runtime_resources as resources


class ResourceTests(unittest.TestCase):
    def test_auto_workers_reserve_cpu_and_adapt_to_available_memory(self):
        with patch.object(resources,'cpu_count',return_value=16),patch.object(resources,'available_memory',return_value=32*1024**3):
            self.assertEqual(resources.index_workers(),15)
        with patch.object(resources,'cpu_count',return_value=16),patch.object(resources,'available_memory',return_value=5*1024**3):
            self.assertEqual(resources.index_workers(),4)
        with patch.object(resources,'cpu_count',return_value=1),patch.object(resources,'available_memory',return_value=None):
            self.assertEqual(resources.index_workers(),1)
        self.assertEqual(resources.index_workers(2),2)
