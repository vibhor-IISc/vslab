# -*- coding: utf-8 -*-

"""
This is script to run a power sweep using znb20 VNA model.

@author: mk

"""


from vslab.constants import *
from vslab.fileio import *

import numpy as np
from qcodes import Measurement, Parameter
from time import sleep
from tqdm import tqdm

close_all_instruments()

# from qcodes.instrument_drivers.rohde_schwarz.ZNB1 import ZNB

# vna = ZNB('vna', ZNB_ADDRESS)

from vslab.instrument_drivers.ZNB_VNA import ZNB_VNA

vna = ZNB_VNA('vna', ZNB_ADDRESS)

exp_name = 'S11_'  # input("Enter exp name: ")
start_power = 0
stop_power = 0
power_points = 1

span_freq = 250*MHz
center_freq = 4.541*GHz

start_freq = center_freq - span_freq/2
stop_freq = center_freq + span_freq/2

num_points = 1001
Avg = 1

############ VNA Setup

# vna.reset()
vna.start_frequency(start_freq)
vna.stop_frequency(stop_freq)
vna.sweep_points(num_points)
vna.power(start_power)
vna.bandwidth(500000)
vna.rf_on()



power_list = np.linspace(start_power, stop_power, power_points)
meta_out = [power_points, start_power, stop_power, 'power']

freqlist = np.linspace(start_freq, stop_freq, num_points)
meta_in = [num_points, start_freq, stop_freq, 'freq']

begin_save(exp_name)
once = True

for powe in tqdm(power_list):
    pw_dummy = np.linspace(powe, powe, num_points)
    s21 = vna.trace()
    freq_list = np.linspace(start_freq, stop_freq,num_points)
    r = np.abs(s21)
    th = np.angle(s21)
    x = r*np.cos(th)
    y = r*np.sin(th)
    
    data = np.array(list(zip(pw_dummy, freq_list,r, th, x, y)))
    
    loop_write(data, exp_name)
    
    # sleep(30)
        
    if once:
        meta_quick(meta_in,meta_out,2)
        mcopy(__file__)
        once = False


# vna.rf_off()
    

from vslab.analysis.fitter import Fitter

ydata = r
xdata = freq_list

fitter = Fitter("S11")
result = fitter.fit(xdata, ydata)  # Automatically estimates parameters
# print(result.fit_report())
fitter.saveplot("test_S11.png")

print(result.best_values['k']/1e6)
print(result.best_values['ke']/1e6)
print(result.best_values['k']/1e6 - result.best_values['ke']/1e6)



