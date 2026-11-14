"""Read NVIDIA metrics in-process on Windows. Never start a helper executable."""
import ctypes
from ctypes import wintypes
import threading

_lock=threading.Lock()


class Memory(ctypes.Structure):
    _fields_=[('total',ctypes.c_ulonglong),('free',ctypes.c_ulonglong),('used',ctypes.c_ulonglong)]


class Utilization(ctypes.Structure):
    _fields_=[('gpu',ctypes.c_uint),('memory',ctypes.c_uint)]


def load_library():
    # Load only the driver library in the real Windows system directory.
    kernel=ctypes.WinDLL('kernel32',use_last_error=True)
    kernel.GetSystemDirectoryW.argtypes=[wintypes.LPWSTR,wintypes.UINT]
    kernel.GetSystemDirectoryW.restype=wintypes.UINT
    directory=ctypes.create_unicode_buffer(32768)
    length=kernel.GetSystemDirectoryW(directory,len(directory))
    if not 0<length<len(directory):raise OSError('Répertoire système Windows indisponible.')
    return ctypes.WinDLL(directory.value+'\\nvml.dll')


def query(*, loader=load_library):
    with _lock:
        library=loader()
        def bind(name,args):
            function=getattr(library,name);function.argtypes=args;function.restype=ctypes.c_int
            return function
        init=bind('nvmlInit_v2',[]);shutdown=bind('nvmlShutdown',[])
        count=bind('nvmlDeviceGetCount_v2',[ctypes.POINTER(ctypes.c_uint)])
        handle=bind('nvmlDeviceGetHandleByIndex_v2',[ctypes.c_uint,ctypes.POINTER(ctypes.c_void_p)])
        name=bind('nvmlDeviceGetName',[ctypes.c_void_p,ctypes.c_char_p,ctypes.c_uint])
        memory=bind('nvmlDeviceGetMemoryInfo',[ctypes.c_void_p,ctypes.POINTER(Memory)])
        utilization=bind('nvmlDeviceGetUtilizationRates',[ctypes.c_void_p,ctypes.POINTER(Utilization)])
        temperature=bind('nvmlDeviceGetTemperature',[ctypes.c_void_p,ctypes.c_uint,ctypes.POINTER(ctypes.c_uint)])
        if init()!=0:return []
        try:
            amount=ctypes.c_uint()
            if count(ctypes.byref(amount))!=0:return []
            result=[]
            for index in range(min(amount.value,32)):
                device=ctypes.c_void_p();label=ctypes.create_string_buffer(256);ram=Memory();load=Utilization();heat=ctypes.c_uint()
                if handle(index,ctypes.byref(device)) or name(device,label,len(label)) or memory(device,ctypes.byref(ram)):continue
                load_ok=utilization(device,ctypes.byref(load))==0
                heat_ok=temperature(device,0,ctypes.byref(heat))==0
                result.append({'name':label.value.decode('utf-8',errors='replace'),'total':ram.total,'used':ram.used,
                               'utilization':load.gpu if load_ok else None,'temperature':heat.value if heat_ok else None})
            return result
        finally:shutdown()
