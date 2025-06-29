import numpy as np
import os
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from scipy.signal import find_peaks


class FitterComplex:
    '''
    To handle fitting of both the quadratures
    WHILE UPDATING, BE MINDFUL -- 
    1) rotation sense when entering model equation
    2) model_func and model_eval are NEARLY IDENTICAL WITH 
    MINOR BUT IMPORTANT CHANGE.
    --> It ends with 'c'
    
    '''
    def __init__(self, model_type="S21"):
        self.models = {"S21": [self.S21, self.S21c],
                       "S21side": [self.S21side, self.S21sidec],
                       "S21sideCable": [self.S21sideCable, self.S21sideCablec],
                       }
        
        if model_type not in self.models:
            raise ValueError(f"Unsupported model type '{model_type}'.")
        
        self.model_type = model_type
        self.model_func = self.models[model_type][0]
        self.model_eval = self.models[model_type][1]
        self.popt = None
        self.pcov = None
        self.perr = None

    # --- Model Functions ---
    # -- NOTE ALL functions are duplicated "with suffix c" to 
    # to handle "model_func" and "model_eval" values
    # till I figure a neater way to handle this.
    # 
    @staticmethod
    def S21c(x, x0, k, amp):
        val = amp*(1/(1+1j*2*(x-x0)/k))
        return val
    
    @staticmethod
    def S21(x, x0, k, amp):
        val = amp*(1/(1+1j*2*(x-x0)/k))
        return np.concatenate([val.real, val.imag])


    @staticmethod
    def S21sidec(x, x0, ke, k, amp, phi, theta):
        init_phase = np.exp(1j*theta)
        val = amp*(1 - 0.5*ke*np.exp(1j*phi)/(k/2 - 1j*(x-x0)))
        return init_phase*val

    @staticmethod
    def S21side(x, x0, ke, k, amp, phi, theta):
        init_phase = np.exp(1j*theta)
        val = amp*(1 - 0.5*ke*np.exp(1j*phi)/(k/2 - 1j*(x-x0)))
        
        val = init_phase*val # replacing
        return np.concatenate([val.real, val.imag])
    
    @staticmethod
    def S21sideCablec(x, x0, ke, k, amp, phi, theta, tau):
        cable_phase = np.exp(1j*(theta + 2*np.pi*x*tau))
        val = amp*(1 - 0.5*ke*np.exp(1j*phi)/(k/2 - 1j*(x-x0)))
        return cable_phase*val

    @staticmethod
    def S21sideCable(x, x0, ke, k, amp, phi, theta, tau):
        cable_phase = np.exp(1j*(theta + 2*np.pi*x*tau))
        val = amp*(1 - 0.5*ke*np.exp(1j*phi)/(k/2 - 1j*(x-x0)))
        
        val = cable_phase*val # replacing
        return np.concatenate([val.real, val.imag])
    

    # --- Initial Guess ---
    # --- CAUTION -> y is in I+1j*Q format
    def initial_guess(self, x, y):
        '''
        ydata ASSUMED BE IN I + ij*Q format

        '''
        def fwhm(x, y):
            y= np.abs(y)
            half_max = np.max(y) / 2
            d = np.sign(half_max - np.array(y[:-1])) - np.sign(half_max - np.array(y[1:]))
            left = np.where(d > 0)[0][0]
            right = np.where(d < 0)[0][-1]
            return abs(x[right] - x[left])

        def fwhm2(x, y):
            y= np.abs(y)
            y = np.abs(y)
            half_max = np.max(y) / 2
            peaks, _ = find_peaks(y, height=half_max)
            if len(peaks) > 1:
                return abs(x[peaks[-1]] - x[peaks[0]])
            else:
                return np.ptp(x) / 5

        if self.model_type == 'S21':
            y= np.abs(y)
            amp = np.max(y)
            x0 = x[np.argmax(y)]
            k = fwhm(x, y)
            return [x0, k, amp]
        
        elif self.model_type == 'S21side':
            amp = np.max(np.abs(y))
            x0 = x[np.argmin(np.abs(y))]
            k = fwhm2(x, -np.abs(y))
            ke = k * abs(1 - np.min(np.abs(y)) / amp)
            phi = 0.19
            theta = np.angle(y[0])
            return [x0, ke, k, amp, phi, theta]
        
        elif self.model_type == 'S21sideCable':
            amp = np.max(np.abs(y))
            x0 = x[np.argmin(np.abs(y))]
            k = fwhm2(x, -np.abs(y))
            ke = k * abs(1 - np.min(np.abs(y)) / amp)
            phi = 0.19
            theta = np.angle(y[0])
            tau = 1e-9 # FUTURE -- update based on frequency period of I or Q
            return [x0, ke, k, amp, phi, theta, tau]


    # --- Fit ---
    def fit(self, x, y, save=False, file_index = 0, filename = 'fit'):
        p0 = self.initial_guess(x, y)
        yall = np.concat([y.real, y.imag])
        self.popt, self.pcov = curve_fit(self.model_func, x, yall, p0=p0)
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
        '''
        y data MUST be in I + 1j*Q format

        '''
        if self.popt is None:
            raise RuntimeError("Fit not yet performed.")
        
        # Create directory if it doesn't exist
        directory = os.path.dirname(filename)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)

        yfit = self.model_eval(x, *self.popt)
        
        
        plt.figure(figsize=(8,6.5))

        plt.subplot(2, 2, 1)
        plt.plot(x, y.real, 'o', label='Real')
        plt.plot(x, yfit.real, '-')
        plt.legend()

        plt.subplot(2, 2, 2)
        plt.plot(x, y.imag, 'o', label='Imag')
        plt.plot(x, yfit.imag, '-')
        plt.legend()

        plt.subplot(2, 2, 3)
        plt.plot(x, np.abs(y), 'o')
        plt.plot(x, np.abs(yfit), '-')

        plt.subplot(2, 2, 4)
        plt.plot(y.real, y.imag, 'o')
        plt.plot(yfit.real, yfit.imag, '-')
        plt.gca().set_aspect('equal')

        plt.tight_layout()
        plt.show()
        
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





##############
# EXAMPLE

# xdata = np.linspace(0, 10, 201)
# yd = FitterComplex.S21c(xdata, x0=5, k=1.5, amp=1)

# fitter = FitterComplex("S21")
# popt, perr = fitter.fit(xdata, yd, save=True)



