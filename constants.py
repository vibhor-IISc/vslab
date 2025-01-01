import numpy as np

GHz = 1.e9
MHz = 1.e6
kHz = 1.e3
mV = 1e-3

ns = 1e-9
us = 1e-6
ms = 1e-3

pi = np.pi

dBm2V = lambda x:np.sqrt(50*1e-3*10**(x/10))

import os
from shutil import copy, copy2
from glob import glob
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime
from pathlib import Path
import qcodes as qc
from qcodes import initialise_or_create_database_at
from qcodes import load_or_create_experiment


###########################################
###########################################


## Addresses of different instruments
# Our convention
# 10-series for VNAs and SA
# 20-series is for microwave signal generator
# 30-series is for AWGs


from qcodes.instrument.base import Instrument

def close_all_instruments():
    Instrument.close_all()

SEQUENCER_ADDRESS = r'C:\Users\normaluser\Documents\Zurich Instruments\LabOne\WebServer\awg\src'
ZNB_ADDRESS = "TCPIP0::192.168.1.3::inst0::INSTR"
ZNB6_ADDRESS = "TCPIP0::192.168.1.52::inst0::INSTR"
HDAWG_ADDRESS ="dev8351"  # IP Address for AWG1 = 192.168.1.31
UHF_ADDRESS ="dev2232"
FSV_ADDRESS = "TCPIP0::192.168.1.8::inst0::INSTR"
ZVL_ADDRESS = "TCPIP0::192.168.1.9::inst0::INSTR"
SG1_ADDRESS = "TCPIP0::192.168.1.21::inst0::INSTR"
SG2_ADDRESS = "TCPIP0::192.168.1.22::inst0::INSTR"
APSYN_ADDRESS = "TCPIP0::192.168.1.7::inst0::INSTR"
SMF_ADDRESS = "TCPIP0::192.168.1.4::inst0::INSTR"
RTE_ADDRESS = 'TCPIP0::192.168.1.6::inst0::INSTR'
GS820_ADDRESS = 'TCPIP0::192.168.1.19::inst0::INSTR'
SGS_ADDRESS = "TCPIP0::192.168.0.100::inst0::INSTR"  #"TCPIP0::169.254.2.20::inst0::INSTR"

