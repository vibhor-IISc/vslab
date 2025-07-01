# -*- coding: utf-8 -*-
"""
Created on Mon Jun 30 14:44:50 2025

@author: user
"""

import h5py
import numpy as np

with h5py.File("example_2dx10.h5", "w") as f:
    f["da2D"] = np.random.rand(100, 10)