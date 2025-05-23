# -*- coding: utf-8 -*-
"""
Created on Thu May 22 16:35:21 2025

@author: user
"""

from vslab.analysis.data import Data2D
from vslab.analysis.fitter import Fitter
from vslab.constants import *
from vslab.fileio import loop_write2
import matplotlib.pyplot as plt
import numpy as np
from glob import glob

paths = glob(r'E:\Downloads\20250523\*.8*\*\res*_8*.dat')


fig =plt.figure(figsize=(4,7))

for file in paths:
    pw, ki = np.loadtxt(file, unpack=True)
    plt.plot(np.flip(pw), np.abs(ki)/1e3,
             '-o', label = file.split('\\')[-1][9:-4])

plt.xlabel('power [dBm]')
plt.ylabel('ki [kHz]')
# plt.ylim(0, 1e6)
plt.yscale('log')
plt.grid()
plt.tight_layout()
plt.legend()
