#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Feb  1 22:15:06 2025

@author: vibhor
"""

import numpy as np
import matplotlib.pyplot as plt
from lmfit import Model
from scipy.signal import find_peaks

class Fitter:
    """A general fitting class using lmfit 
    with multiple models and automatic initial 
    guesses."""

    def __init__(self, model_type="lorentzian"):
        """Initialize the Fitter with a specified model type."""
        self.models = {
            "lorentzian": self.lorentzian,
            "exponential": self.exponential,
            "S21": self.S21,
        }

        if model_type not in self.models:
            raise ValueError(f"Unsupported model type '{model_type}'. Available models: {list(self.models.keys())}")

        self.model_type = model_type
        self.model = Model(self.models[model_type])
        self.result = None  # Store the fit result
        
        
        
    @staticmethod
    def S21(x, x0, k, amp):
        '''
        Parameters
        ----------
        x : frequency
        x0 : resonant frequency
        k : linewidth
        amp : amplitude
        
        Returns
        -------
        np.abs(amp*(1/(1+1j*2*(x-x0)/k)))
        '''
        return np.abs(amp*(1/(1+1j*2*(x-x0)/k)))

---> Need correction below.     
    @staticmethod
    def S21Sidecoupled(x, x0, k, ke, amp):
        return np.abs(amp*(1- 0.5*ke/(1+1j*2*(x-x0)/k)))

    

    @staticmethod
    def lorentzian(x, A, x0, w):
        """Lorentzian function."""
        return (A / np.pi) * (w / 2) / ((x - x0) ** 2 + (w / 2) ** 2)

    @staticmethod
    def exponential(x, A, tau, C):
        """Exponential decay function."""
        return A * np.exp(-x / tau) + C

    @staticmethod
    def linear(x, m, b):
        """Linear function."""
        return m * x + b

    def initial_guess(self, x, y):
        """Estimate initial parameters based on x and y data."""
        if self.model_type == "lorentzian":
            peak_idx = np.argmax(y)
            x0 = x[peak_idx]  # Peak position
            A = np.trapezoid(y, x)  # Rough area under curve
            half_max = np.max(y) / 2
            peaks, _ = find_peaks(y, height=half_max)
            if len(peaks) > 1:
                w = abs(x[peaks[-1]] - x[peaks[0]])  # Approximate FWHM
            else:
                w = np.ptp(x) / 5  # Default width if FWHM not well defined
            return {"A": A, "x0": x0, "w": w}

        elif self.model_type == "exponential":
            A = np.max(y)
            C = np.min(y)
            tau = (x[-1] - x[0]) / 5  # Rough decay rate
            return {"A": A, "tau": tau, "C": C}

        elif self.model_type == "linear":
            coeffs = np.polyfit(x, y, 1)
            return {"m": coeffs[0], "b": coeffs[1]}

        elif self.model_type == "quadratic":
            coeffs = np.polyfit(x, y, 2)
            return {"a": coeffs[0], "b": coeffs[1], "c": coeffs[2]}

        else:
            raise ValueError(f"No initial guess method for model '{self.model_type}'.")

    def fit(self, x, y, **kwargs):
        """Fit the selected model to the data. 
        Uses initial_guess if parameters are 
        not provided."""
        if not kwargs:
            kwargs = self.initial_guess(x, y)
            print(f"Using estimated initial parameters: {kwargs}")

        params = self.model.make_params(**kwargs)  # Create parameters with initial values
        self.result = self.model.fit(y, params, x=x)
        return self.result  # Return the fit result

    def saveplot(self, filename="fit_plot.png"):
        """Save the fit plot to the specified file."""
        if self.result is None:
            raise RuntimeError("No fit result available. Run .fit() first.")
        
        ax = self.result.plot_fit()  # Generate the fit plot
        fig = ax.figure  # Get the figure from Axes
        fig.savefig(filename, dpi=300, bbox_inches="tight")
        print(f"Plot saved to {filename}")

    def best_fit_params(self):
        """Return the best fit parameters and their standard errors."""
        if self.result is None:
            raise RuntimeError("No fit result available. Run .fit() first.")
        
        # Extract parameters and their uncertainties (stderr)
        best_params = {}
        for param_name, param in self.result.params.items():
            best_params[param_name] = {
                "value": param.value,
                "stderr": param.stderr if param.stderr is not None else float('nan')
            }
        return best_params

# Example Usage
if __name__ == "__main__":
    np.random.seed(42)
    x = np.linspace(0, 10, 100)

    # Example 1: Lorentzian Fit
    print("\nLorentzian Fit:")
    y_lorentz = Fitter.lorentzian(x, A=10, x0=5, w=1) + 0.05 * np.random.normal(size=len(x))
    fitter = Fitter("lorentzian")
    result = fitter.fit(x, y_lorentz)  # Automatically estimates parameters
    print(result.fit_report())
    fitter.saveplot("lorentzian_fit.png")

    # # Get best fit parameters and their stderr
    # best_params = fitter.best_fit_params()
    # print("\nBest fit parameters and their stderr:")
    # for param_name, param_info in best_params.items():
    #     print(f"{param_name}: value = {param_info['value']}, stderr = {param_info['stderr']}")

    # # Example 2: Exponential Fit
    # print("\nExponential Fit:")
    # y_exp = Fitter.exponential(x, A=5, tau=2, C=1) + 0.05 * np.random.normal(size=len(x))
    # fitter = Fitter("exponential")
    # result = fitter.fit(x, y_exp)  # Automatically estimates parameters
    # print(result.fit_report())
    # fitter.saveplot("exponential_fit.png")

    # # Get best fit parameters and their stderr
    # best_params = fitter.best_fit_params()
    # print("\nBest fit parameters and their stderr:")
    # for param_name, param_info in best_params.items():
    #     print(f"{param_name}: value = {param_info['value']}, stderr = {param_info['stderr']}")
