# -*- coding: utf-8 -*-
"""
Created on Thu May 22 16:35:21 2025

@author: user
"""


import matplotlib.pyplot as plt
import numpy as np
from glob import glob


key = 7
paths = glob(rf'E:\Downloads\20250523\*{key}*\*\res*_{key}*.dat')


plt.clf()


for file in paths:
    pw, ki, kierr = np.loadtxt(file, unpack=True)
    plt.errorbar(np.flip(pw), np.abs(ki), kierr, 
                 linestyle='none',
                 marker = 's',
                 markersize=6,
                 ecolor='gray',
                 capsize=3,
                 elinewidth=1)

plt.xlabel('power [dBm]')
plt.ylabel('ki [kHz]')
plt.grid()
plt.tight_layout()

