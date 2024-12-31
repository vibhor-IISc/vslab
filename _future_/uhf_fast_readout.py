# -*- coding: utf-8 -*-
"""
Created on Sun Jun 27 12:28:40 2021

@author: normaluser
"""

from vslab.constants import *
from vslab.rack import *
import numpy as np
from time import sleep, time

tc = 1e-3
# # Input Range  of 0.1V (-7 dBm) is choosen for the safe operation of the
# # external mixer. In case of LOCK-In overload, remove one amplifier in the
# # measurement chain
# Function for fast readout

def setup_uhf_fast_read(uhf, mix_freq = 77*1e6, tc = 100*1e-9, n_rows = 1, avg = 10, duration = 5*1e-6, npts=100):
    '''
    Prepare UHF to perform fast time-domain
    measurements.
    mix_freq = 111 MHz
    tc = 30 ns
    n_rows = default: 1; use > 1 for single shots
    avg = (defines the number of averages)
    ::  default:10; use=1 for single shots
    
    default lockin input range 100 mV

    '''
    # set external clock
    uhf.system.extclk(1)
    
    # input settings
    uhf.sigins.sigins0.range(100*1e-3)
    uhf.sigins.sigins0.imp50(1)
    uhf.sigins.sigins0.scaling(1)
    uhf.oscs.oscs0.freq(mix_freq)
    
    # Settings demods
    uhf.demods.demods0.order(1)
    uhf.demods.demods0.timeconstant(tc)
    uhf.demods.demods0.trigger(32) # TrigIn3 HIGH
    uhf.demods.demods0.rate(14*MHz)
    uhf.demods.demods0.enable(1)
    
    # DAQ settings
    uhf.daq.signals_clear()
    uhf.daq.type('hardware')
    uhf.daq.trigger(trigger_source = 'demod0', trigger_type ='trigin3')
    uhf.daq.edge('rising')
    uhf.daq.holdoff_time(0.0)
    uhf.daq.delay(0.0)
    
    ## DAQ grid settings
    uhf.daq.grid_mode('linear')
    uhf.daq.grid_cols(npts)
    uhf.daq.grid_rows(n_rows)
    uhf.daq.duration(duration)
    uhf.daq.grid_repetitions(avg)
    # Check in the manual -- This may not be the RIGHT thing to do
    # uhf.daq.grid_rowrepetition(1)
    uhf.daq.grid_direction('forward')
    pass