"""Conservative local worker sizing; no model launch and no GPU helper process."""
import os
from pathlib import Path


def cpu_count():
    count=getattr(os,'process_cpu_count',os.cpu_count)() or 1
    try:
        quota,period=Path('/sys/fs/cgroup/cpu.max').read_text().split()
        if quota!='max':count=min(count,max(1,(int(quota)+int(period)-1)//int(period)))
    except (OSError,ValueError):pass
    return count


def available_memory():
    value=None
    if os.name=='nt':
        try:
            import ctypes
            class Memory(ctypes.Structure):
                _fields_=[('length',ctypes.c_ulong),('load',ctypes.c_ulong)]+[(k,ctypes.c_ulonglong) for k in ('total','available','total_page','available_page','total_virtual','available_virtual','extended')]
            info=Memory();info.length=ctypes.sizeof(info)
            if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(info)):value=info.available
        except (OSError,AttributeError):pass
    else:
        try:value=next(int(line.split()[1])*1024 for line in Path('/proc/meminfo').read_text().splitlines() if line.startswith('MemAvailable:'))
        except (OSError,ValueError,StopIteration):pass
        try:
            limit=Path('/sys/fs/cgroup/memory.max').read_text().strip()
            if limit!='max':
                remaining=max(0,int(limit)-int(Path('/sys/fs/cgroup/memory.current').read_text()))
                value=min(value,remaining) if value is not None else remaining
        except (OSError,ValueError):pass
    return value


def index_workers(requested=None):
    count=requested or min(16,max(1,cpu_count()-1))
    memory=available_memory()
    if not requested and memory is not None:count=min(count,max(1,(memory-4*1024**3)//(256*1024**2)))
    return count


def background_worker():
    if os.name=='nt':
        try:
            import ctypes
            kernel=ctypes.windll.kernel32
            kernel.GetCurrentProcess.restype=ctypes.c_void_p
            kernel.SetPriorityClass.argtypes=(ctypes.c_void_p,ctypes.c_ulong)
            kernel.SetPriorityClass(kernel.GetCurrentProcess(),0x4000)
        except (OSError,AttributeError):pass
    else:
        try:os.nice(5)
        except OSError:pass
