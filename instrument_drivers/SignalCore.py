# -*- coding: utf-8 -*-
"""
Created on Wed Jun 23 17:47:32 2021

@author: normaluser
"""

import sys
import time
import ctypes
import types

NUM_MAX_DEVICES = 5
ID_BUFFER_SIZE = 8

LB_DLL = 'C:\\Program Files\\SignalCore\\SC5511A\\api\\c\\x64\\sc5511a.dll'

# lb_dll = ctypes.CDLL(LB_DLL)
# lb_dll = ctypes.windll.LoadLibrary(LB_DLL)
lb_dll = ctypes.cdll.LoadLibrary(LB_DLL)

string_buffers = [ctypes.create_string_buffer(ID_BUFFER_SIZE) for i in range(NUM_MAX_DEVICES)]
pointers = (ctypes.c_char_p*NUM_MAX_DEVICES)(*map(ctypes.addressof, string_buffers))
results = [s.value for s in string_buffers]
devid = b'100020C3'
dev_num = ctypes.c_char_p(devid)
lb_dll.sc5511a_open_device.restype = ctypes.POINTER(ctypes.c_int)
handle = lb_dll.sc5511a_open_device(dev_num)

lb_dll.sc5511a_set_clock_reference(handle, 1000000,1)
lb_dll.sc5511a_set_freq(handle, ctypes.c_ulonglong(int(1.0e9)))
lb_dll.sc5511a_set_level(handle, ctypes.c_float(-25))
lb_dll.sc5511a_set_output(handle, 1)

def signal_core_frequency(fre):
    lb_dll.sc5511a_set_freq(handle, ctypes.c_ulonglong(int(fre)))
    pass

def signal_core_level(lev):
    lb_dll.sc5511a_set_level(handle, ctypes.c_float(lev))
    pass

def signal_core_rf_on_off(boo):
    if boo:
        lb_dll.sc5511a_set_output(handle, 1)
    else:
        lb_dll.sc5511a_set_output(handle, 0)
    pass

    
