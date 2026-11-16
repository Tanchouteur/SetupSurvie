"""Read-only host counters. No benchmark, helper process, credentials or disk scan.

Linux: /proc/stat and /proc/diskstats. Windows: language-neutral PDH counters,
with GetSystemTimes as a CPU-only fallback. All activities on the host are included.
"""
import ctypes
import math
import os
from pathlib import Path
import re
import sys
import threading
import time


def cpu_rows(raw):
    result={}
    for line in raw.splitlines():
        row=line.split()
        if not row or not re.fullmatch(r'cpu\d*',row[0]) or len(row)<5:continue
        try:values=[int(value) for value in row[1:9]]
        except ValueError:continue
        if any(value<0 for value in values):continue
        result[row[0]]={'total':sum(values),'idle':values[3]+(values[4] if len(values)>4 else 0),'iowait':values[4] if len(values)>4 else 0}
        if len(result)>=4097:break
    return result


def disk_rows(raw):
    result={}
    for line in raw.splitlines():
        row=line.split()
        if len(row)<14 or not re.fullmatch(r'[a-zA-Z0-9_-]{1,80}',row[2]) or row[2].startswith(('loop','ram','fd','sr')):continue
        try:values=[int(value) for value in row[3:14]];major,minor=int(row[0]),int(row[1])
        except ValueError:continue
        if min(values+[major,minor])<0:continue
        result[row[2]]={'device':f'{major}:{minor}','reads':values[0],'read_bytes':values[2]*512,'read_ms':values[3],
            'writes':values[4],'write_bytes':values[6]*512,'write_ms':values[7],'in_progress':values[8],'busy_ms':values[9],'weighted_ms':values[10]}
        if len(result)>=128:break
    return result


def cpu_delta(current,previous):
    if not previous or not all(key in current and key in previous for key in ('total','idle')):return None
    total=current['total']-previous['total'];idle=current['idle']-previous['idle'];wait=current.get('iowait',0)-previous.get('iowait',0)
    if total<=0 or min(idle,wait)<0 or idle>total:return None
    return {'percent':round(100*(total-idle)/total,2),'iowait_percent':round(100*wait/total,2)}


def disk_delta(current,previous,seconds):
    empty={'read_bytes_per_second':None,'write_bytes_per_second':None,'busy_percent':None,'average_latency_ms':None,'average_queue':None}
    if not previous or seconds<=0:return empty
    delta={key:current[key]-previous[key] for key in ('reads','read_bytes','read_ms','writes','write_bytes','write_ms','busy_ms','weighted_ms')}
    if min(delta.values())<0:return empty
    count=delta['reads']+delta['writes']
    return {'read_bytes_per_second':round(delta['read_bytes']/seconds,2),'write_bytes_per_second':round(delta['write_bytes']/seconds,2),
        'busy_percent':round(min(100,100*delta['busy_ms']/(seconds*1000)),2),
        'average_latency_ms':round((delta['read_ms']+delta['write_ms'])/count,3) if count else None,
        'average_queue':round(delta['weighted_ms']/(seconds*1000),3)}


class CounterUnion(ctypes.Union):
    _fields_=[('longValue',ctypes.c_int32),('doubleValue',ctypes.c_double),('largeValue',ctypes.c_int64),('stringValue',ctypes.c_void_p)]


class CounterValue(ctypes.Structure):
    _anonymous_=('value',)
    _fields_=[('status',ctypes.c_uint32),('value',CounterUnion)]


class CounterItem(ctypes.Structure):
    _fields_=[('name',ctypes.c_wchar_p),('value',CounterValue)]


def windows_library(name):
    kernel=ctypes.WinDLL('kernel32',use_last_error=True)
    kernel.GetSystemDirectoryW.argtypes=[ctypes.c_wchar_p,ctypes.c_uint];kernel.GetSystemDirectoryW.restype=ctypes.c_uint
    directory=ctypes.create_unicode_buffer(32768);length=kernel.GetSystemDirectoryW(directory,len(directory))
    if not 0<length<len(directory):raise OSError('Windows system directory unavailable.')
    return ctypes.WinDLL(directory.value+'\\'+name,use_last_error=True)


class WindowsCounters:
    PATHS={'cpu':r'\Processor(*)\% Processor Time','read_bytes_per_second':r'\PhysicalDisk(*)\Disk Read Bytes/sec',
        'write_bytes_per_second':r'\PhysicalDisk(*)\Disk Write Bytes/sec','read_latency_seconds':r'\PhysicalDisk(*)\Avg. Disk sec/Read',
        'write_latency_seconds':r'\PhysicalDisk(*)\Avg. Disk sec/Write','idle_percent':r'\PhysicalDisk(*)\% Idle Time',
        'average_queue':r'\PhysicalDisk(*)\Avg. Disk Queue Length'}
    SCALARS={'pages_input_per_second':r'\Memory\Pages Input/sec','pages_output_per_second':r'\Memory\Pages Output/sec'}

    def __init__(self,loader=windows_library):
        self.library=loader('pdh.dll');self.query=ctypes.c_void_p();self.counters={}
        def bind(name,args):
            function=getattr(self.library,name);function.argtypes=args;function.restype=ctypes.c_uint32;return function
        self.open=bind('PdhOpenQueryW',[ctypes.c_wchar_p,ctypes.c_size_t,ctypes.POINTER(ctypes.c_void_p)])
        self.add=bind('PdhAddEnglishCounterW',[ctypes.c_void_p,ctypes.c_wchar_p,ctypes.c_size_t,ctypes.POINTER(ctypes.c_void_p)])
        self.collect=bind('PdhCollectQueryData',[ctypes.c_void_p]);self.close=bind('PdhCloseQuery',[ctypes.c_void_p])
        self.array=bind('PdhGetFormattedCounterArrayW',[ctypes.c_void_p,ctypes.c_uint32,ctypes.POINTER(ctypes.c_uint32),ctypes.POINTER(ctypes.c_uint32),ctypes.c_void_p])
        self.scalar=bind('PdhGetFormattedCounterValue',[ctypes.c_void_p,ctypes.c_uint32,ctypes.c_void_p,ctypes.POINTER(CounterValue)])
        if self.open(None,0,ctypes.byref(self.query)):raise OSError('PDH unavailable.')
        for key,path in {**self.PATHS,**self.SCALARS}.items():
            handle=ctypes.c_void_p()
            if not self.add(self.query,path,0,ctypes.byref(handle)):self.counters[key]=handle

    def sample(self):
        if self.collect(self.query):return {}
        result={}
        for key,handle in self.counters.items():
            if key in self.SCALARS:
                value=CounterValue()
                if not self.scalar(handle,0x200,None,ctypes.byref(value)) and value.status in (0,1) and math.isfinite(value.doubleValue) and 0<=value.doubleValue<1e16:
                    result[key]={'_Total':value.doubleValue}
                continue
            size=ctypes.c_uint32();count=ctypes.c_uint32()
            code=self.array(handle,0x200|0x800,ctypes.byref(size),ctypes.byref(count),None)
            if code!=0x800007D2 or not 0<size.value<=4_000_000:continue
            buffer=ctypes.create_string_buffer(size.value)
            if self.array(handle,0x200|0x800,ctypes.byref(size),ctypes.byref(count),buffer) or count.value>4096 or count.value*ctypes.sizeof(CounterItem)>size.value:continue
            items=ctypes.cast(buffer,ctypes.POINTER(CounterItem));values={}
            for index in range(count.value):
                item=items[index];value=item.value.doubleValue;name=item.name
                if item.value.status in (0,1) and name and len(name)<=100 and math.isfinite(value) and 0<=value<1e16:values[name]=value
            result[key]=values
        return result

    def dispose(self):
        if self.query:
            self.close(self.query);self.query=ctypes.c_void_p()


def windows_cpu_times():
    class FileTime(ctypes.Structure):_fields_=[('low',ctypes.c_uint32),('high',ctypes.c_uint32)]
    kernel=windows_library('kernel32.dll');function=kernel.GetSystemTimes
    function.argtypes=[ctypes.POINTER(FileTime)]*3;function.restype=ctypes.c_int
    idle,user,system=FileTime(),FileTime(),FileTime()
    if not function(ctypes.byref(idle),ctypes.byref(system),ctypes.byref(user)):return {}
    value=lambda row:(row.high<<32)|row.low
    return {'cpu':{'total':value(system)+value(user),'idle':value(idle),'iowait':0}}


class Sampler:
    def __init__(self):self.lock=threading.Lock();self.previous=None;self.windows=None;self.next_attempt=0

    def sample(self,data_dir):
        with self.lock:
            now=time.monotonic();stamp=time.time();previous=self.previous or {};seconds=now-previous.get('time',now)
            result={'schema':1,'source':'host_controller','platform':sys.platform,'sampled_at':stamp,'interval_ms':round(seconds*1000) if seconds>0 else None,
                'scope':'whole_host_including_other_activities','cpu':{},'disks':[],'issues':[]}
            current={'time':now,'cpus':{},'disks':{},'paging':{}}
            if os.name=='nt':
                try:
                    if self.windows is None and now>=self.next_attempt:self.next_attempt=now+30;self.windows=WindowsCounters()
                    raw=self.windows.sample() if self.windows else {}
                except (OSError,AttributeError,ValueError):
                    raw={}
                    if self.windows:
                        try:self.windows.dispose()
                        except (OSError,AttributeError):pass
                    self.windows=None
                cpus=raw.get('cpu',{});total=cpus.get('_Total');cores=[{'id':name,'percent':round(min(100,value),2)} for name,value in cpus.items() if name!='_Total']
                result['memory_page_io']={key:raw[key]['_Total'] for key in WindowsCounters.SCALARS if '_Total' in raw.get(key,{})}
                result['cpu']={'logical_processors':os.cpu_count(),'percent':round(min(100,total),2) if total is not None else None,'cores':cores}
                if total is None:
                    try:current['cpus']=windows_cpu_times();delta=cpu_delta(current['cpus'].get('cpu',{}),previous.get('cpus',{}).get('cpu'))
                    except (OSError,AttributeError,ValueError,KeyError):delta=None
                    if delta:result['cpu'].update(delta)
                names={name for key,values in raw.items() if key!='cpu' for name in values if name!='_Total'}
                drive=os.path.splitdrive(str(data_dir))[0].upper()
                for name in sorted(names)[:64]:
                    row={'id':name,'data_disk':bool(drive and drive in name.upper()),'provider':'windows_pdh'}
                    for key in ('read_bytes_per_second','write_bytes_per_second','average_queue'):row[key]=raw.get(key,{}).get(name)
                    idle=raw.get('idle_percent',{}).get(name);row['busy_percent']=round(max(0,100-min(100,idle)),2) if idle is not None else None
                    for key in ('read','write'):
                        value=raw.get(key+'_latency_seconds',{}).get(name);row[key+'_latency_ms']=round(value*1000,3) if value is not None else None
                    result['disks'].append(row)
            else:
                try:current['cpus']=cpu_rows(Path('/proc/stat').read_text())
                except OSError:pass
                try:current['disks']=disk_rows(Path('/proc/diskstats').read_text())
                except OSError:pass
                try:
                    vm=dict(line.split() for line in Path('/proc/vmstat').read_text().splitlines())
                    current['paging']={key:int(vm[key]) for key in ('pswpin','pswpout') if key in vm}
                    page_size=os.sysconf('SC_PAGE_SIZE')
                    result['paging_bytes_per_second']={key:round((value-previous['paging'][key])*page_size/seconds,2)
                        for key,value in current['paging'].items() if seconds>0 and key in previous.get('paging',{}) and value>=previous['paging'][key]}
                except (OSError,ValueError,KeyError):pass
                delta=cpu_delta(current['cpus'].get('cpu',{}),previous.get('cpus',{}).get('cpu'))
                result['cpu']={'logical_processors':os.cpu_count(),'percent':None,'cores':[],**(delta or {})}
                for name,row in current['cpus'].items():
                    if name=='cpu':continue
                    value=cpu_delta(row,previous.get('cpus',{}).get(name))
                    if value:result['cpu']['cores'].append({'id':name,**value})
                try:device=os.stat(data_dir).st_dev;data_device=f'{os.major(device)}:{os.minor(device)}'
                except OSError:data_device=None
                for name,row in current['disks'].items():
                    rotational=None
                    try:rotational=Path('/sys/dev/block/'+row['device']+'/queue/rotational').read_text().strip()=='1'
                    except OSError:pass
                    result['disks'].append({'id':name,'data_disk':row['device']==data_device,'rotational':rotational,'provider':'linux_diskstats',
                        'in_progress':row['in_progress'],**disk_delta(row,previous.get('disks',{}).get(name),seconds)})
            result['cpu']['max_core_percent']=max((row['percent'] for row in result['cpu'].get('cores',[]) if row.get('percent') is not None),default=None)
            if result['cpu'].get('percent') is None:result['issues'].append('cpu_not_sampled')
            if not result['disks']:result['issues'].append('disk_counters_unavailable')
            if not any(row.get('data_disk') for row in result['disks']):result['issues'].append('library_disk_mapping_unknown')
            self.previous=current
            return result


SAMPLER=Sampler()


def snapshot(data_dir):return SAMPLER.sample(data_dir)
