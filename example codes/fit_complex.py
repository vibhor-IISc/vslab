#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Jun 29 22:56:07 2025

@author: vibhor
"""

from vslab.analysis.data import Data2D
from vslab.analysis.fitter_complex import FitterComplex


from glob import glob
import numpy as np
import matplotlib.pyplot as plt

files = glob('/Users/Vibhor/Downloads/daa/')


da = Data2D(files[0])

freq = 580e6 +da.X

s21_r = da.Z(2)
s21_t = da.Z(3)

s21_i = s21_r*np.cos(s21_t)
s21_q = s21_r*np.sin(s21_t)

idx = -10
s21c = s21_i[idx]+1j*s21_q[idx]

xdata = freq
yd = s21c

fitter = FitterComplex("S21side")
popt, perr = fitter.fit(xdata, yd, save=True)



