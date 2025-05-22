#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Feb  1 22:15:06 2025

@author: vibhor
"""

import numpy as np
import os
import matplotlib.pyplot as plt
from lmfit import Model
from scipy.signal import find_peaks


class Fitter:
    """A general fitting class using lmfit 
    with multiple models and automatic initial 
    guesses.
    
    """
    
# _init_ must be placed after all the static methods
    
    @staticmethod
    def _guess_fwhm(x,y):
        half_max = np.max(y) / 2.0

        #find when function crosses line half_max (when sign of diff flips)        
        d = np.sign(half_max - np.array(y[0:-1])) - np.sign(half_max - np.array(y[1:]))

        #find the left and right most indexes
        left_idx = np.where(d > 0)[0][0]
        right_idx = np.where(d < 0)[0][-1]
        return np.abs(x[right_idx] - x[left_idx]) #return the difference (full width)
    
    @staticmethod
    def _guess_fwhm2(x,y):
        half_max = np.max(y) / 2.0
        peaks, _ = find_peaks(y, height=half_max)
        if len(peaks) > 1:
            k = abs(x[peaks[-1]] - x[peaks[0]])  # Approximate FWHM
        else:
            k = np.ptp(x) / 5  # Default width if FWHM not well defined
        return np.abs(k)
        
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
    
    @staticmethod
    def S11(x, x0, ke, k, amp):
        '''
        Parameters
        ----------
        x : frequency
        x0 : resonant frequency
        ke : external/internal coupling
        k : linewidth
        amp : amplitude (baseline)
        
        Returns
        -------
        np.abs(amp*(1 - (2*ke/k) * (1 + 1j*2*(x-x0)/k)**-1))
        '''
        return np.abs(amp*(1 - (2*ke/k) * (1 + 1j*2*(x-x0)/k)**-1))
    
    @staticmethod
    def S11complex(x, x0, ke, k, amp, phi):
        '''
        Parameters
        ----------
        x : frequency
        x0 : resonant frequency
        ke : external/internal coupling
        k : linewidth
        amp : amplitude (baseline)
        phi : phase factor
        
        Returns
        -------
        np.abs(amp*(1 - (2*ke*np.exp(1j*phi)/k) * (1 + 1j*2*(x-x0)/k)**-1))
        '''
        return np.abs(amp*(1 - (2*ke*np.exp(1j*phi)/k) * (1 + 1j*2*(x-x0)/k)**-1))
    
    @staticmethod
    def S21side(x, x0, ke, ki, amp):
        '''
        Parameters
        ----------
        x : frequency
        x0 : resonant frequency
        ke : external coupling
        ki : internal linewidth
        amp : amplitude (baseline)
        
        Returns
        -------
        np.abs(amp*(1 - (ke/k) * (1 + 1j*2*(x-x0)/k)**-1))
        '''
        k = ke + ki
        return np.abs(amp*(1 - (ke/k) * (1 + 1j*2*(x-x0)/k)**-1))


    @staticmethod
    def S21sideComplex(x, x0, ke, ki, amp, phi):
        '''
        Parameters
        ----------
        x : frequency
        x0 : resonant frequency
        ke : external coupling
        ki : internal linewidth
        amp : amplitude (baseline)
        phi : A complex phase shift
        
        Returns
        -------
        np.abs(amp*(1 - (ke*np.exp(1j*phi)/k) * (1 + 1j*2*(x-x0)/k)**-1))
        '''
        k = ke*np.cos(phi) + ki
        return np.abs(amp*(1 - (ke*np.exp(1j*phi)/k) * (1 + 1j*2*(x-x0)/k)**-1))

    @staticmethod
    def S21sideDCM(x, x0, Qe, Q, amp, phi):
        '''
        Parameters
        ----------
        x : frequency
        x0 : resonant frequency
        Qe : external coupling
        Q : total linewidth
        amp : amplitude (baseline)
        phi : A complex phase shift
        
        Returns
        -------
        return np.abs(amp*(1 - (Q/Qe*np.exp(-1j*phi)) / (1 + 1j*2*Q*(x-x0)/x0)))
        '''
        return np.abs(amp*(1 - (Q/Qe*np.exp(-1j*phi)) / (1 + 1j*2*Q*(x-x0)/x0)))

    @staticmethod
    def lorentzian(x, A, x0, w):
        """Lorentzian function."""
        return (A / np.pi) * (w / 2) / ((x - x0) ** 2 + (w / 2) ** 2)
    
    @staticmethod
    def quadratic(x, a, b, c):
        '''
        Parameters
        ----------
        x : indp var
        a : Coeff x**2
        b : Coeff x**1
        c : Coeff x**0

        Returns
        -------
        a*x**2 + b*x +c
        '''
        return a*x**2 + b*x +c

    @staticmethod
    def exponential(x, A, tau, C):
        """Exponential decay function."""
        return A * np.exp(-x / tau) + C

    @staticmethod
    def linear(x, m, b):
        """Linear function."""
        return m * x + b
    
# All static methods must be before _init_    
    
    def __init__(self, model_type="lorentzian"):
        """Initialize the Fitter with a specified model type.
        Available models are:
            S21, S11, S21side, S21sideComplex
            linear, quadratic,
            exponential, lorentzian
        """
        self.models = {
            "S21": self.S21,
            "S11": self.S11,
            "S11complex": self.S11complex,
            "S21side": self.S21side,
            "S21sideComplex": self.S21sideComplex,
            "S21sideDCM": self.S21sideDCM,
            "linear": self.linear,
            "quadratic": self.quadratic,
            "lorentzian": self.lorentzian,
            "exponential": self.exponential,
        }

        if model_type not in self.models:
            raise ValueError(f"Unsupported model type '{model_type}'. Available models: {list(self.models.keys())}")

        self.model_type = model_type
        self.model = Model(self.models[model_type])
        self.result = None  # Store the fit result




    def initial_guess(self, x, y):
        """Estimate initial parameters based on x and y data."""
        
        
        if self.model_type == 'S21':
            amp = np.max(y)
            x0 = x[np.argmax(y)]
            k = self._guess_fwhm(x,y)
            return {"amp":amp, "x0":x0, "k":k}
        
        elif self.model_type == 'S11':
            amp = np.max(y)
            x0 = x[np.argmin(y)]
            k = self._guess_fwhm2(x, -y)
            ke = (k/2)*np.abs(1-np.min(y)/amp)            
            return {"x0":x0, "ke":ke, "k":k, "amp":amp}
        
        elif self.model_type == 'S11complex':
            amp = np.max(y)
            x0 = x[np.argmin(y)]
            k = self._guess_fwhm2(x, -y)
            ke = (k/2)*np.abs(1-np.min(y)/amp)
            phi = np.pi*0.3            
            return {"x0":x0, "ke":ke, "k":k, "amp":amp, "phi":phi}
        
        elif self.model_type == 'S21side':
            amp = np.max(y)
            x0 = x[np.argmin(y)]
            k = self._guess_fwhm2(x, -y)
            ke = k*np.abs(1-np.min(y)/amp)
            ki = np.abs(k-ke)            
            return {"x0":x0, "ke":ke, "ki":ki, "amp":amp}

        elif self.model_type == 'S21sideComplex':
            amp = np.max(y)
            x0 = x[np.argmin(y)]
            k = self._guess_fwhm2(x, -y)
            ke = k*np.abs(1-np.min(y)/amp)
            ki = np.abs(k-ke)
            phi = 0.19            
            return {"x0":x0, "ke":ke, "ki":ki, "amp":amp, "phi":phi}

        elif self.model_type == 'S21sideDCM':
            amp = np.max(y)
            x0 = x[np.argmin(y)]
            k = self._guess_fwhm2(x, -y)
            ke = k*np.abs(1-np.min(y)/amp)
            Q = x0/k
            Qe = x0/ke
            phi = 0.19            
            return {"x0":x0, "Qe":Qe, "Q":Q, "amp":amp, "phi":phi}

        elif self.model_type == "linear":
            coeffs = np.polyfit(x, y, 1)
            return {"m": coeffs[0], "b": coeffs[1]}

        elif self.model_type == "quadratic":
            coeffs = np.polyfit(x, y, 2)
            return {"a": coeffs[0], "b": coeffs[1], "c": coeffs[2]}
        
        elif self.model_type == "exponential":
            A = np.max(y)
            C = np.min(y)
            tau = (x[-1] - x[0]) / 5  # Rough decay rate
            return {"A": A, "tau": tau, "C": C}
        
        elif self.model_type == "lorentzian":
            peak_idx = np.argmax(y)
            x0 = x[peak_idx]  # Peak position
            A = np.trapezoid(y, x)  # Rough area under curve
            w = self._guess_fwhm(x, y)
            return {"A": A, "x0": x0, "w": w}

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
        
        # Create the directory if it doesn't exist
        directory = os.path.dirname(filename)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
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
# 
# if __name__ == "__main__":
#     np.random.seed(42)
#     x = np.linspace(0, 10, 100)

#     # Example 1: Lorentzian Fit

#     ydata = Fitter.lorentzian(x, A=10, x0=5, w=1) + 0.05 * np.random.normal(size=len(x))
#     fitter = Fitter("lorentzian")
#     result = fitter.fit(x, ydata)  # Automatically estimates parameters
#     print(result.fit_report())
#     fitter.saveplot("test_lorentzian_fit.png")
#     # plt.clf()
    
    
    # # # Example 2: S21 fit

    # ydata = Fitter.S21(x, x0=5, amp=5, k = 1) + 0.05 * np.random.normal(size=len(x))
    # fitter = Fitter("S21")
    # result = fitter.fit(x, ydata)  # Automatically estimates parameters
    # print(result.fit_report())
    # fitter.saveplot("test_S21.png")
    # plt.clf()
    
    # # Example 3: S11 fit

    # ydata = Fitter.S11(x, x0=5, amp=3, ke = 0.4, k = 1) + 0.05 * np.random.normal(size=len(x))
    # fitter = Fitter("S11")
    # result = fitter.fit(x, ydata)  # Automatically estimates parameters
    # print(result.fit_report())
    # fitter.saveplot("test_S11.png")
    # plt.clf()
    
    # # Example 4: S21side fit

    # ydata = Fitter.S21side(x, x0=5, amp=4, ke = 0.4, k = 1) + 0.05 * np.random.normal(size=len(x))
    # fitter = Fitter("S21side")
    # result = fitter.fit(x, ydata)  # Automatically estimates parameters
    # print(result.fit_report())
    # fitter.saveplot("test_S21side.png")
    # plt.clf()
    
    
    # # Example 4: linear fit

    # ydata = Fitter.linear(x, m=1, b = 10) + 0.05 * np.random.normal(size=len(x))
    # fitter = Fitter("linear")
    # result = fitter.fit(x, ydata)  # Automatically estimates parameters
    # print(result.fit_report())
    # fitter.saveplot("test_linear_fit.png")
    # plt.clf()
    
    # # Example 5: quadratic fit

    # ydata = Fitter.quadratic(x, a=1, b = 10, c=3) + 0.05 * np.random.normal(size=len(x))
    # fitter = Fitter("quadratic")
    # result = fitter.fit(x, ydata)  # Automatically estimates parameters
    # print(result.fit_report())
    # fitter.saveplot("test_quadratic_fit.png")
    # plt.clf()
    
    
    # # Example 6: Exponential Fit

    # ydata = Fitter.exponential(x, A=5, tau=2, C=1) + 0.05 * np.random.normal(size=len(x))
    # fitter = Fitter("exponential")
    # result = fitter.fit(x, ydata)  # Automatically estimates parameters
    # print(result.fit_report())
    # fitter.saveplot("test_exponential_fit.png")
    # plt.clf()
    
    
    # Get best fit parameters and their stderr
    # best_params = fitter.best_fit_params()
    # print("\nBest fit parameters and their stderr:")
    # for param_name, param_info in best_params.items():
    #     print(f"{param_name}: value = {param_info['value']}, stderr = {param_info['stderr']}")

