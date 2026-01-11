# -*- coding: utf-8 -*-
"""
Created on Wed Dec 31 16:28:48 2025

@author: normaluser
"""


from vslab.rack import *
from vslab.constants import *
from vslab.Readout_Control_vs_hd_v2 import Readout, Control

from zhinst.toolkit import Session

readout_frequency =  6.056*GHz#    readout freq

session = Session('localhost')
rd = Readout(UHF_ADDRESS, 'localhost', session=session)
rd.frequency = readout_frequency
rd.sideband = 'left'
rd.optimize_all()

rd.time_constant_and_order(300e-9, 1)

rd.osc_amp(0.08)
# data = rd.S21_sweep(
#     start_fc=7.39e9, 
#     stop_fc=7.40e9, 
#     npts=100, 
#     filter_order=1, 
#     reverse = False 
# )

# rd.osc_amp(0.5)
# rd.readout_mode_pulse()

# rd.input_range(50e-3)
# rd.pregain(10)
# rd.time_constant_and_order(50e-9, 1)
# rd.config_aux_for_scope(1500)


# cn = Control(HDAWG_ADDRESS, 'localhost')
# cn.frequency = control_frequency
# cn.sideband = 'right'
# cn.optimize_all()