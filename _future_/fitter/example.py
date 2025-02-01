#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Feb  1 22:21:48 2025

@author: vibhor
"""

import numpy as np
import matplotlib.pyplot as plt
from lmfit import Model

# Define the Lorentzian function
def lorentzian(x, A, x0, w):
    return (A / np.pi) * (w / 2) / ((x - x0) ** 2 + (w / 2) ** 2)

# Generate synthetic noisy data
np.random.seed(42)
x = np.linspace(-10, 10, 100)
true_params = {'A': 10, 'x0': 0, 'w': 2}
y_true = lorentzian(x, **true_params)
y_noisy = y_true + 0.05 * np.random.normal(size=len(x))  # Adding noise

# Create lmfit Model
lorentz_model = Model(lorentzian)

# Create parameters with initial guesses
params = lorentz_model.make_params(A=8, x0=1, w=3)  # Initial guesses

# Fit the model to data
result = lorentz_model.fit(y_noisy, params, x=x)

# Print fitting results
print(result.fit_report())

# Plot results
plt.figure(figsize=(8, 5))
plt.scatter(x, y_noisy, label="Noisy Data", color="gray", s=10)
plt.plot(x, y_true, label="True Lorentzian", linestyle="dashed", color="red")
plt.plot(x, result.best_fit, label="Fitted Lorentzian", color="blue")
plt.legend()
plt.xlabel("X")
plt.ylabel("Intensity")
plt.title("Lorentzian Fit with lmfit")
plt.show()

