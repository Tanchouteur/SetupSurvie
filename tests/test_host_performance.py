"""Read-only native counters: rates, missing data and localized Windows PDH API."""
import ctypes
from pathlib import Path
import sys
import unittest
from unittest.mock import Mock,patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import host_performance as host


class CounterTests(unittest.TestCase):
    def test_cpu_deltas_include_each_core_and_do_not_count_guest_twice(self):
        before=host.cpu_rows('cpu 100 0 20 80 0 0 0 0 40 0\ncpu0 30 0 10 60\n')
        after=host.cpu_rows('cpu 160 0 40 100 0 0 0 0 80 0\ncpu0 50 0 20 80\n')
        self.assertEqual(host.cpu_delta(after['cpu'],before['cpu'])['percent'],80)
        self.assertEqual(host.cpu_delta(after['cpu0'],before['cpu0'])['percent'],60)
        self.assertIsNone(host.cpu_delta({},before['cpu']))
        self.assertIsNone(host.cpu_delta(before['cpu'],after['cpu']))
        self.assertIsNone(host.cpu_delta(after['cpu'],after['cpu']))

    def test_disk_rates_units_latency_queue_reset_and_first_sample(self):
        before=host.disk_rows('8 0 sda 10 0 100 20 5 0 200 10 0 100 200')['sda']
        after=host.disk_rows('8 0 sda 12 0 108 26 6 0 204 13 1 600 1700')['sda']
        value=host.disk_delta(after,before,1)
        self.assertEqual(value['read_bytes_per_second'],4096)
        self.assertEqual(value['write_bytes_per_second'],2048)
        self.assertEqual(value['busy_percent'],50)
        self.assertEqual(value['average_latency_ms'],3)
        self.assertEqual(value['average_queue'],1.5)
        self.assertIsNone(host.disk_delta(after,None,1)['busy_percent'])
        self.assertIsNone(host.disk_delta(before,after,1)['busy_percent'])
        self.assertEqual(host.disk_rows('7 0 loop0 0 0 0 0 0 0 0 0 0 0 0'),{})

    @unittest.skipIf(sys.platform=='win32','Linux proc fixture')
    def test_disappearing_proc_files_do_not_create_zero_load_or_crash(self):
        sampler=host.Sampler()
        with patch.object(host.Path,'read_text',return_value='cpu 10 0 10 80'):
            first=sampler.sample('/nonexistent-fixture')
        with patch.object(host.Path,'read_text',side_effect=OSError('missing')):
            second=sampler.sample('/nonexistent-fixture')
        self.assertIsNone(first['cpu']['percent']);self.assertIsNone(second['cpu']['percent'])
        self.assertIn('disk_counters_unavailable',second['issues'])

    def test_pdh_uses_english_counter_paths_and_checks_values(self):
        functions={name:Mock(return_value=0) for name in ('PdhOpenQueryW','PdhAddEnglishCounterW','PdhCollectQueryData','PdhCloseQuery','PdhGetFormattedCounterArrayW')}
        library=type('DLL',(),functions)();texts=[]
        def opened(name,user,query):query._obj.value=123;return 0
        def added(query,path,user,handle):texts.append(path);handle._obj.value=len(texts);return 0
        functions['PdhOpenQueryW'].side_effect=opened;functions['PdhAddEnglishCounterW'].side_effect=added
        names=[ctypes.create_unicode_buffer('_Total'),ctypes.create_unicode_buffer('0')]
        def array(handle,flags,size,count,buffer):
            count._obj.value=2;size._obj.value=2*ctypes.sizeof(host.CounterItem)
            if buffer is None:return 0x800007D2
            items=ctypes.cast(buffer,ctypes.POINTER(host.CounterItem))
            for index in range(2):
                items[index].name=ctypes.cast(names[index],ctypes.c_wchar_p);items[index].value.status=0
                items[index].value.doubleValue=25 if index==0 else float('nan')
            return 0
        functions['PdhGetFormattedCounterArrayW'].side_effect=array
        counter=host.WindowsCounters(loader=lambda _:library);value=counter.sample();counter.dispose()
        self.assertIn(r'\Processor(*)\% Processor Time',texts)
        self.assertEqual(value['cpu'],{'_Total':25})
        self.assertEqual(ctypes.sizeof(host.CounterValue),16)
        functions['PdhCloseQuery'].assert_called_once()

    @unittest.skipUnless(sys.platform=='win32','Windows native API only')
    def test_actual_windows_counter_access_is_read_only_and_optional(self):
        values=host.windows_cpu_times()
        self.assertGreater(values['cpu']['total'],0)
        # Some Windows runners have disabled disk counters: that remains unknown.
        sampler=host.Sampler();sample=sampler.sample(Path.cwd())
        self.assertEqual(sample['source'],'host_controller')
        if sampler.windows:sampler.windows.dispose()
