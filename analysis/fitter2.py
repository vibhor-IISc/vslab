import numpy as np
import os
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from scipy.signal import find_peaks


class Fitter:
    def __init__(self, model_type="lorentzian"):
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
            raise ValueError(f"Unsupported model type '{model_type}'.")
        
        self.model_type = model_type
        self.model_func = self.models[model_type]
        self.popt = None
        self.pcov = None
        self.perr = None

    # --- Model Functions ---
    @staticmethod
    def S21(x, x0, k, amp):
        return np.abs(amp*(1/(1+1j*2*(x-x0)/k)))

    @staticmethod
    def S11(x, x0, ke, k, amp):
        return np.abs(amp*(1 - (2*ke/k) * (1 + 1j*2*(x-x0)/k)**-1))

    @staticmethod
    def S11complex(x, x0, ke, k, amp, phi):
        return np.abs(amp*(1 - (2*ke*np.exp(1j*phi)/k) * (1 + 1j*2*(x-x0)/k)**-1))

    @staticmethod
    def S21side(x, x0, ke, ki, amp):
        k = ke + ki
        return np.abs(amp*(1 - (ke/k) * (1 + 1j*2*(x-x0)/k)**-1))

    @staticmethod
    def S21sideComplex(x, x0, ke, k, amp, phi):
        return np.abs(amp*(1 - 0.5*ke*np.exp(1j*phi)/(k/2 - 1j*(x-x0))))

    @staticmethod
    def S21sideDCM(x, x0, Qe, Q, amp, phi):
        return np.abs(amp*(1 - (Q/Qe*np.exp(-1j*phi)) / (1 + 1j*2*Q*(x-x0)/x0)))

    @staticmethod
    def lorentzian(x, A, x0, w):
        return (A / np.pi) * (w / 2) / ((x - x0) ** 2 + (w / 2) ** 2)

    @staticmethod
    def quadratic(x, a, b, c):
        return a*x**2 + b*x + c

    @staticmethod
    def exponential(x, A, tau, C):
        return A * np.exp(-x / tau) + C

    @staticmethod
    def linear(x, m, b):
        return m * x + b

    # --- Initial Guess ---
    def initial_guess(self, x, y):
        def fwhm(x, y):
            half_max = np.max(y) / 2
            d = np.sign(half_max - np.array(y[:-1])) - np.sign(half_max - np.array(y[1:]))
            left = np.where(d > 0)[0][0]
            right = np.where(d < 0)[0][-1]
            return abs(x[right] - x[left])

        def fwhm2(x, y):
            half_max = np.max(y) / 2
            peaks, _ = find_peaks(y, height=half_max)
            if len(peaks) > 1:
                return abs(x[peaks[-1]] - x[peaks[0]])
            else:
                return np.ptp(x) / 5

        if self.model_type == 'S21':
            amp = np.max(y)
            x0 = x[np.argmax(y)]
            k = fwhm(x, y)
            return [x0, k, amp]

        elif self.model_type == 'S11':
            amp = np.max(y)
            x0 = x[np.argmin(y)]
            k = fwhm2(x, -y)
            ke = (k / 2) * abs(1 - np.min(y) / amp)
            return [x0, ke, k, amp]

        elif self.model_type == 'S11complex':
            amp = np.max(y)
            x0 = x[np.argmin(y)]
            k = fwhm2(x, -y)
            ke = (k / 2) * abs(1 - np.min(y) / amp)
            phi = np.pi * 0.3
            return [x0, ke, k, amp, phi]

        elif self.model_type == 'S21side':
            amp = np.max(y)
            x0 = x[np.argmin(y)]
            k = fwhm2(x, -y)
            ke = k * abs(1 - np.min(y) / amp)
            ki = abs(k - ke)
            return [x0, ke, ki, amp]

        elif self.model_type == 'S21sideComplex':
            amp = np.max(y)
            x0 = x[np.argmin(y)]
            k = fwhm2(x, -y)
            ke = k * abs(1 - np.min(y) / amp)
            phi = 0.19
            return [x0, ke, k, amp, phi]

        elif self.model_type == 'S21sideDCM':
            amp = np.max(y)
            x0 = x[np.argmin(y)]
            k = fwhm2(x, -y)
            Q = x0 / k
            ke = k * abs(1 - np.min(y) / amp)
            Qe = x0 / ke
            phi = 0.19
            return [x0, Qe, Q, amp, phi]

        elif self.model_type == "linear":
            coeffs = np.polyfit(x, y, 1)
            return coeffs.tolist()

        elif self.model_type == "quadratic":
            coeffs = np.polyfit(x, y, 2)
            return coeffs.tolist()

        elif self.model_type == "exponential":
            return [np.max(y), (x[-1] - x[0]) / 5, np.min(y)]

        elif self.model_type == "lorentzian":
            A = np.trapezoid(y, x)
            x0 = x[np.argmax(y)]
            w = fwhm(x, y)
            return [A, x0, w]

    # --- Fit ---
    def fit(self, x, y, save=False, file_index = 0, filename = 'fit'):
        p0 = self.initial_guess(x, y)
        self.popt, self.pcov = curve_fit(self.model_func, x, y, p0=p0)
        self.perr = np.sqrt(np.diag(self.pcov))
        
        if save:
            # Save figure
            self.save_plot(x, y, filename=filename+str(file_index).zfill(3)+'.png')
            # Save best parameters to a dict
            self.save_param(filename+str(file_index).zfill(3)+'.npz')
            
        else:
            pass
        return self.popt, self.perr

    def save_plot(self, x, y, filename="fit_plot.png"):
        if self.popt is None:
            raise RuntimeError("Fit not yet performed.")
        
        # Create directory if it doesn't exist
        directory = os.path.dirname(filename)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)

        yfit = self.model_func(x, *self.popt)

        plt.figure()
        plt.plot(x, y, 'o', label='Data')
        plt.plot(x, yfit, '-', label='Fit')
        plt.legend()
        plt.savefig(filename, dpi=300)
        print(f"Saved plot to {filename}")

    def best_fit_params(self):
        if self.popt is None:
            raise RuntimeError("Fit not yet performed.")
        param_names = self.model_func.__code__.co_varnames[1:self.model_func.__code__.co_argcount]
        # return dict(zip(param_names, self.popt, self.perr))
        return {name: (val, err) for name, val, err in zip(param_names, self.popt, self.perr)}
    
    def save_param(self, filename = 'params.npz'):
        '''
        Save the best fit parameters
        to a file in a compressed python dict.
        
        # USE the follwing for re-loading 
        # res = dict(np.load("params.npz").items())


        '''
        if self.popt is None:
            raise RuntimeError("Fit not yet performed.")
        
        # Create directory if it doesn't exist
        directory = os.path.dirname(filename)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)
        
        best_vals = self.best_fit_params()
        np.savez(filename, **best_vals)
        print(f"Saved data to {filename}")
        pass

        

def post_process(files, save=False, filename):
    all_res = []    
    for file in files:
         best_dict = dict(np.load(file).items())
         keys = best_dict.keys()
         best_vals = np.array([best_dict[key] for key in keys]).flatten()
         all_res.append(best_vals)
    
    all_res = np.array(all_res)
    
    final_dict = {}
    for idx, key in enumerate(keys):
        final_dict[key] = all_res[:,idx]
        final_dict['err_'+key] = all_res[:,idx+1]
        
    if save:
        np.savez(fillename+'_final.npz', **final_dict)
        print(f"Saved data to {filename+'_final.npz'}")
        
    return final_dict
    

##############
# EXAMPLE

# xdata = np.linspace(0, 10, 200)
# ydata = Fitter.lorentzian(xdata, A=5, x0=5, w=1.5) + 0.1*np.random.normal(size=len(xdata))

# fitter = Fitter("S21")
# popt, perr = fitter.fit(xdata, ydata)

