import ctypes
import sys
from pathlib import Path
import unittest
from unittest.mock import MagicMock

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import gpu_windows


class NativeGpuTests(unittest.TestCase):
    def library(self):
        dll=MagicMock()
        dll.nvmlInit_v2.return_value=0
        def count(pointer):pointer._obj.value=1;return 0
        def handle(index,pointer):pointer._obj.value=123;return 0
        def name(device,buffer,length):buffer.value=b'NVIDIA test';return 0
        def memory(device,pointer):pointer._obj.total=8192;pointer._obj.used=2048;pointer._obj.free=6144;return 0
        def utilization(device,pointer):pointer._obj.gpu=23;return 0
        def temperature(device,sensor,pointer):pointer._obj.value=48;return 0
        for key,value in [('nvmlDeviceGetCount_v2',count),('nvmlDeviceGetHandleByIndex_v2',handle),('nvmlDeviceGetName',name),('nvmlDeviceGetMemoryInfo',memory),('nvmlDeviceGetUtilizationRates',utilization),('nvmlDeviceGetTemperature',temperature)]:
            getattr(dll,key).side_effect=value
        return dll

    def test_native_metrics_and_shutdown(self):
        dll=self.library();value=gpu_windows.query(loader=lambda:dll)
        self.assertEqual(value,[{'name':'NVIDIA test','total':8192,'used':2048,'utilization':23,'temperature':48}])
        dll.nvmlShutdown.assert_called_once()

    def test_partial_metrics_and_failure_release_the_driver(self):
        dll=self.library();dll.nvmlDeviceGetTemperature.side_effect=None;dll.nvmlDeviceGetTemperature.return_value=3
        self.assertIsNone(gpu_windows.query(loader=lambda:dll)[0]['temperature'])
        dll.nvmlDeviceGetMemoryInfo.side_effect=OSError('driver reset')
        with self.assertRaises(OSError):gpu_windows.query(loader=lambda:dll)
        self.assertEqual(dll.nvmlShutdown.call_count,2)

    def test_unavailable_driver_returns_no_metrics(self):
        dll=self.library();dll.nvmlInit_v2.return_value=9
        self.assertEqual(gpu_windows.query(loader=lambda:dll),[])
        dll.nvmlShutdown.assert_not_called()
