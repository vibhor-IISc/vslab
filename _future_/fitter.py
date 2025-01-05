#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Jan  5 23:58:48 2025

@author: vibhor
"""

import numpy as np
import lmfit as lm
import matplotlib.pyplot as plt
import inspect

def approx_FWHM(X, Y):
    half_max = np.max(Y) / 2.0
    d = np.sign(half_max - np.array(Y[:-1])) - np.sign(half_max - np.array(Y[1:]))
    left_idx = np.where(d > 0)[0][0]
    right_idx = np.where(d < 0)[0][-1]
    return X[right_idx] - X[left_idx]

def normalized_complex_root_lorentzian(f, f0, kappa):
    return (kappa / 2) / (kappa / 2 - 1j * (f - f0))

def lorentzian(f, f0, kappa, norm):
    return np.abs(normalized_complex_root_lorentzian(f, f0, kappa) * norm) ** 2

def exponential(t, tau, norm):
    return norm * np.exp(-t / tau)

FUNCTION_GROUPS = {
    "lorentzian": [lorentzian,
                   normalized_complex_root_lorentzian],
    "exponential": [exponential],
}

def get_function_params(func):
    return list(inspect.signature(func).parameters.keys())[1:]

class Fitter:
    def __init__(self, func, complex_fit=False):
        if func not in [f for group in FUNCTION_GROUPS.values() for f in group]:
            raise ValueError("Provided function is not recognized.")
        self.func = func
        self.params = [{"name": p, "value": None, "min": None, "max": None} for p in get_function_params(func)]
        self.complex_fit = complex_fit
        self.method = 'leastsq'
        self.results = None

    def _initialize_params(self, xdata, ydata):
        y = np.abs(ydata)
        if self.func in FUNCTION_GROUPS["lorentzian"]:
            offset = np.mean(y[-int(0.1 * len(y)):])
            norm = np.max(y) - offset
            f0 = xdata[np.argmax(y)]
            kappa = approx_FWHM(xdata, y - offset)
            return {"f0": f0, "kappa": kappa, "norm": norm}
        elif self.func in FUNCTION_GROUPS["exponential"]:
            norm = np.max(y)
            tau = np.abs(xdata[-1] - xdata[0]) / 3
            return {"tau": tau, "norm": norm}
        return {}

    def fit(self, xdata, ydata, use_previous=False, **kwargs):
        init_params = self._initialize_params(xdata, ydata)

        lmfit_params = lm.Parameters()
        for param in self.params:
            name = param["name"]
            value = kwargs.get(name, init_params.get(name, 0))
            param["value"] = value
            lmfit_params.add(name, value=value, min=param.get("min"), max=param.get("max"))

        if self.complex_fit:
            ydata = np.concatenate([np.real(ydata), np.imag(ydata)])

            def residual(params):
                p = [params[name].value for name in lmfit_params.keys()]
                fit_values = self.func(xdata, *p)
                return np.concatenate([np.real(fit_values), np.imag(fit_values)]) - ydata

        else:
            def residual(params):
                p = [params[name].value for name in lmfit_params.keys()]
                fit_values = np.abs(self.func(xdata, *p))
                return fit_values - np.abs(ydata)

        self.results = lm.minimize(residual, lmfit_params, method=self.method)
        for param in self.params:
            param["value"] = self.results.params[param["name"].value]

        return self.results

    def plot(self):
        if self.results is None:
            raise RuntimeError("No fit results to plot. Call fit() first.")

        param_values = [p["value"] for p in self.params]
        fit_data = self.func(self.results.userkws["xdata"], *param_values)

        plt.plot(self.results.userkws["xdata"], self.results.userkws["ydata"], 'bo', label="Data")
        plt.plot(self.results.userkws["xdata"], fit_data, 'r-', label="Fit")
        plt.legend()
        plt.show()

    def save_plot(self, filename):
        plt.savefig(filename)

    def save_fit_results(self, filename, include_header=True):
        with open(filename, 'w') as file:
            if include_header:
                file.write("\t".join([p["name"] for p in self.params]) + "\n")
            file.write("\t".join([str(p["value"]) for p in self.params]) + "\n")
