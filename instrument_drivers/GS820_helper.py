# -*- coding: utf-8 -*-
"""
Created on Tue Jul 23 11:29:57 2024

@author: admin
"""
import numpy as np
import time



    
def GS820sweepVoltTo(gs820, chn=1,  setV=0, incr = 1e-3, tol=2e-3):
    sign = np.sign(setV -float(gs820.query(f'CHAN{chn}:SOUR:LEV?')))
    dummy = gs820.query('*OPC?')
    while np.abs(float(gs820.query(f'CHAN{chn}:SOUR:LEV?')) - setV) >= tol:
        dummy = gs820.query('*OPC?')
        now = float(gs820.query(f'CHAN{chn}:SOUR:LEV?'))
        dummy = gs820.query('*OPC?')
        gs820.write(f'CHAN{chn}:SOUR:LEV {now + sign*incr}')
    if np.abs(float(gs820.query(f'CHAN{chn}:SOUR:LEV?')) - setV) < tol:
        dummy = gs820.query('*OPC?')
        gs820.write(f'CHAN{chn}:SOUR:LEV {setV}')
    else:
        pass

def GS820sweepCurrTo(gs820, chn=1,  setI=0, incr = 1e-3 ):
    sign = np.sign(setI -float(gs820.query(f'CHAN{chn}:SOUR:LEV?')))
    tol = incr
    while np.abs(float(gs820.query(f'CHAN{chn}:SOUR:LEV?')) - setI) >= tol:
        dummy = gs820.query('*OPC?')
        now = float(gs820.query(f'CHAN{chn}:SOUR:LEV?'))
        dummy = gs820.query('*OPC?')
        gs820.write(f'CHAN{chn}:SOUR:LEV {now + sign*incr}')
    if np.abs(float(gs820.query(f'CHAN{chn}:SOUR:LEV?')) - setI) < tol:
        dummy = gs820.query('*OPC?')
        gs820.write(f'CHAN{chn}:SOUR:LEV {setI}')
    else:
        pass

def GS820config(gs820, chn=1, curr=20E-6, volt=200E-3):
    gs820.write(f'CHAN{chn}:SOUR:FUNC VOLT')
    gs820.write(f'CHAN{chn}:SOUR:RANG {volt}')
    gs820.write(f'CHAN{chn}:SENS:FUNC CURR')
    gs820.write(f'CHAN{chn}:SENS:RANG {curr}')
    gs820.write(f'CHAN{chn}:OUTP ON')
    

def GS820config2(gs820, chn=1, curr=20E-6, volt=200E-3, volt_limit=200e-3):
    gs820.write(f'CHAN{chn}:SOUR:PROT:LEV {volt_limit}')
    gs820.write(f'CHAN{chn}:SOUR:FUNC CURR')
    gs820.write(f'CHAN{chn}:SOUR:RANG {curr}')
    gs820.write(f'CHAN{chn}:SENS:FUNC VOLT')
    gs820.write(f'CHAN{chn}:SENS:RANG {volt}')
    gs820.write(f'CHAN{chn}:OUTP ON')
    
 
def GS820GetIV(gs820, chn=1, start=-20e-3, stop=20e-3, pnts = 100, both=False):
    voltages = np.linspace(start,stop,pnts)
    if both:
        voltages = np.append(voltages, np.flip(voltages))
    currents = []
    
    for voltage in voltages:
        GS820sweepVoltTo(gs820, chn=1, setV=voltage)
        # gs820.write(f'CHAN{chn}:SOUR:LEV {voltage}')
        current = float(gs820.query(f'CHAN{chn}:MEAS?'))
        dummy = gs820.query('*OPC?')
        currents.append(current)
        
    return voltages, np.array(currents)


def GS820GetVI(gs820, chn=1, start=-10e-9, stop=10e-9, pnts = 101, both=False,  avg = 2, W4=False):
    currents = np.linspace(start,stop,pnts)
    if W4:
        gs820.write(f'CHAN{chn}:SENS:REM 1')
    else:
        gs820.write(f'CHAN{chn}:SENS:REM 0')
    if both:
        currents = np.append(currents, np.flip(currents))
    voltages = []
   
    for current in currents:
        GS820sweepCurrTo(gs820, chn=1, setI=current)
        vv = 0
        for val in range(avg):
            vv = vv + float(gs820.query(f'CHAN{chn}:MEAS?'))
            time.sleep(0.1)
            dummy = gs820.query('*OPC?')
            pass
        voltage = vv/avg
        voltages.append(voltage)
        
    return currents, np.array(voltages)

def GS820_OuputsOFF(gs820):
    GS820sweepVoltTo(gs820, chn=1,  setV=0)
    GS820sweepVoltTo(gs820, chn=2,  setV=0)
    gs820.write(f'CHAN{1}:OUTP OFF')
    gs820.write(f'CHAN{2}:OUTP OFF')
    
    
def GS820_CurrOuputsOFF(gs820):
    GS820sweepCurrTo(gs820, chn=1,  setI=0)
    GS820sweepCurrTo(gs820, chn=2,  setI=0)
    gs820.write(f'CHAN{1}:OUTP OFF')
    gs820.write(f'CHAN{2}:OUTP OFF')