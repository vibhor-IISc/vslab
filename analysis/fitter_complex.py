import numpy as np
import os
import pickle
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from scipy.signal import find_peaks
from vslab.analysis.fitter import Fitter

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
                       "S21sideF": [self.S21sideF, self.S21sideFc],
                       "S21sideCable": [self.S21sideCable, self.S21sideCablec],
                       "S21sideCableF": [self.S21sideCableF, self.S21sideCableFc],
                       "S11cable": [self.S11, self.S11c]
                       }
        
        if model_type not in self.models:
            raise ValueError(f"Unsupported model type '{model_type}'.")
        
        self.model_type = model_type.
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
        init_phase = np.exp(-1j*theta)
        val = amp*(1 - 0.5*ke*np.exp(1j*phi)/(k/2 + 1j*(x-x0)))
        return init_phase*val

    @staticmethod
    def S21side(x, x0, ke, k, amp, phi, theta):
        init_phase = np.exp(-1j*theta)
        val = amp*(1 - 0.5*ke*np.exp(1j*phi)/(k/2 + 1j*(x-x0)))
        
        val = init_phase*val # replacing
        return np.concatenate([val.real, val.imag])

    @staticmethod
    def S21sideFc(x, x0, ke, ki, amp, phi, tau):
        init_phase = np.exp(-1j*2*np.pi*x*tau)
        k = ke*np.cos(phi) + ki
        val = amp*(1 - 0.5*ke*np.exp(1j*phi)/(k/2 + 1j*(x-x0)))
        return init_phase*val

    @staticmethod
    def S21sideF(x, x0, ke, ki, amp, phi, tau):
        init_phase = np.exp(-1j*2*np.pi*x*tau)
        k = ke*np.cos(phi) + ki
        val = amp*(1 - 0.5*ke*np.exp(1j*phi)/(k/2 + 1j*(x-x0)))
        val = init_phase*val # replacing
        return np.concatenate([val.real, val.imag])

    
    @staticmethod
    def S21sideCablec(x, x0, ke, k, amp, phi, theta, tau):
        cable_phase = np.exp(1j*(theta - 2*np.pi*x*tau))
        val = amp*(1 - 0.5*ke*np.exp(1j*phi)/(k/2 + 1j*(x-x0)))
        return cable_phase*val

    @staticmethod
    def S21sideCable(x, x0, ke, k, amp, phi, theta, tau):
        cable_phase = np.exp(1j*(theta - 2*np.pi*x*tau))
        val = amp*(1 - 0.5*ke*np.exp(1j*phi)/(k/2 + 1j*(x-x0)))
        
        val = cable_phase*val # replacing
        return np.concatenate([val.real, val.imag])

    @staticmethod
    def S21sideCableFc(x, x0, ke, ki, amp, phi, theta, tau):
        cable_phase = np.exp(1j*(theta - 2*np.pi*x*tau))
        k = ke*np.cos(phi) + ki
        val = amp*(1 - 0.5*ke*np.exp(1j*phi)/(k/2 + 1j*(x-x0)))
        return cable_phase*val

    @staticmethod
    def S21sideCableF(x, x0, ke, ki, amp, phi, theta, tau):
        cable_phase = np.exp(1j*(theta - 2*np.pi*x*tau))
        k = ke*np.cos(phi) + ki
        val = amp*(1 - 0.5*ke*np.exp(1j*phi)/(k/2 + 1j*(x-x0)))
        
        val = cable_phase*val # replacing
        return np.concatenate([val.real, val.imag])
    
    @staticmethod
    def S11c(x, x0, ke, k, amp):
        val = amp*(1 - (2*ke/k)/(1+1j*2*(x-x0)/k))
        return val
    
    @staticmethod
    def S11(x, x0, ke, k, amp):
        val = amp*(1 - (2*ke/k)/(1+1j*2*(x-x0)/k))
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
            y = np.abs(y)
            half_max = np.max(y) / 2
            peaks, _ = find_peaks(y, height=half_max)
            if len(peaks) > 1:
                return abs(x[peaks[-1]] - x[peaks[0]])
            else:
                return np.ptp(x) / 5
        
        def fwhm3(x, y):
            y = -1*np.abs(y)
            half_max = -1*np.max(y) / 2
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
            k = fwhm3(x, -np.abs(y))
            ke = k * abs(1 - np.min(np.abs(y)) / amp)
            phi = 0.19
            theta = np.angle(y[0])
            return [x0, ke, k, amp, phi, theta]


        elif self.model_type == 'S21sideF':
            amp = np.max(np.abs(y))
            x0 = x[np.argmin(np.abs(y))]
            k = fwhm3(x, -np.abs(y))
            ke = k * abs(1 - np.min(np.abs(y)) / amp)
            phi = 0.19
            ki = k - ke*np.cos(phi)
            tau = (-1/2/np.pi)*np.mean(np.gradient(np.unwrap(np.angle(y)), x))
            return [x0, ke, ki, amp, phi, tau]


        elif self.model_type == 'S21sideCable':
            amp = np.max(np.abs(y))
            x0 = x[np.argmin(np.abs(y))]
            
            _md = Fitter('S21sideComplex')
            _ = _md.fit(x, np.abs(y), save=False)
            
            # k = fwhm3(x, -np.abs(y))
            k = _md.best_fit_params()['k']
            # ke = k * abs(1 - np.min(np.abs(y)) / amp)
            ke = _md.best_fit_params()['ke']

            phi = 0.19
            theta = np.angle(y[0])
            tau = (-1/2/np.pi)*np.mean(np.gradient(np.unwrap(np.angle(y)), x))
            return [x0, ke, k, amp, phi, theta, tau]

        elif self.model_type == 'S21sideCableF':
            amp = np.max(np.abs(y))
            x0 = x[np.argmin(np.abs(y))]
            
            _md = Fitter('S21sideComplex')
            _ = _md.fit(x, np.abs(y), save=False)
            
            # k = fwhm3(x, -np.abs(y))
            k = _md.best_fit_params()['k']
            # ke = k * abs(1 - np.min(np.abs(y)) / amp)
            ke = _md.best_fit_params()['ke']
            phi = 0.19
            ki = k - ke*np.cos(phi)
            theta = np.angle(y[0])
            tau = (-1/2/np.pi)*np.mean(np.gradient(np.unwrap(np.angle(y)), x)[:10])
            return [x0, ke, ki, amp, phi, theta, tau]
        
        elif self.model_type == 'S11':
            y= np.abs(y)
            amp = np.max(y)
            x0 = x[np.argmin(y)]
            k = fwhm(x, -y)
            ke = 0.2*k
            return [x0, ke, k, amp]


    # --- Fit ---
    def fit(self, x, y, 
            save=False, 
            dir_name = None,
            file_index = 0,
            auto_guess=True,
            guess_val = None):
        '''

        Parameters
        ----------
        x : indep_var 
        y : dep Complex data
        save : True/False
            The default is False.
        dir_name : Directory name
            DESCRIPTION. The default is None.
        file_index : INT, used as a counter.
        auto_guess : True/False
            DESCRIPTION. The default is True.
        guess : list of guess values for fitting
        
        You may use:
        
        list(guess_dict.values())  to prepare the list

        Returns
        -------
        popt, p_err
        
        '''
        if auto_guess:
            p0 = self.initial_guess(x, y)
        else:
            pass
            p0 = guess_val
        yall = np.concat([y.real, y.imag])
        self.popt, self.pcov = curve_fit(self.model_func, x, yall, p0=p0)
        self.perr = np.sqrt(np.diag(self.pcov))
        
        if save:
            # Save figure
            self.save_plot(x, y, dir_name=dir_name, file_index=file_index)
            # Save best parameters to a dict
            self.save_param(dir_name=dir_name, file_index=file_index)

            
        else:
            pass
        return self.popt, self.perr

    def save_plot(self, x, y, dir_name, file_index=0):
        '''
        y data MUST be in I + 1j*Q format

        '''
        if self.popt is None:
            raise RuntimeError("Fit not yet performed.")
        
        # Create directory if it doesn't exist
        directory = dir_name
        if directory and not os.path.exists(directory):
            os.makedirs(directory)

        yfit = self.model_eval(x, *self.popt)
        
        
        plt.figure(figsize=(8,6.5))

        plt.subplot(2, 2, 1)
        plt.plot(x, y.real, 'o', color = 'orange', label='Real')
        plt.plot(x, yfit.real, '-', color = 'black')
        plt.locator_params(nbins=5)
        plt.legend()

        plt.subplot(2, 2, 2)
        plt.plot(x, y.imag, 'o', color = 'lightgreen', label='Imag')
        plt.plot(x, yfit.imag, '-', color = 'black')
        plt.locator_params(nbins=5)
        plt.legend()

        plt.subplot(2, 2, 3)
        plt.plot(x, np.abs(y), 'o', color = 'cornflowerblue', label = 'mag')
        plt.plot(x, np.abs(yfit), '-', color = 'black')
        plt.locator_params(nbins=5)
        plt.legend()

        plt.subplot(2, 2, 4)
        plt.plot(y.real, y.imag, 'o', color='gray', label = 'polar')
        plt.plot(yfit.real, yfit.imag, '-', color = 'black')
        plt.locator_params(nbins=5)
        plt.gca().set_aspect('equal')
        plt.legend()

        plt.tight_layout()
        filename = dir_name+'fit_'+str(file_index).zfill(4)+'.png'
        plt.savefig(filename, dpi=300)
        print(f"Saved plot to {filename}")



    def best_fit_params(self):
        if self.popt is None:
            raise RuntimeError("Fit not yet performed.")
        param_names = self.model_func.__code__.co_varnames[1:self.model_func.__code__.co_argcount]
        return dict(zip(param_names, self.popt))
        # return {name: (val, err) for name, val, err in zip(param_names, self.popt, self.perr)}
    
    def best_fit_params_error(self):
        if self.popt is None:
            raise RuntimeError("Fit not yet performed.")
        param_names = self.model_func.__code__.co_varnames[1:self.model_func.__code__.co_argcount]
        return dict(zip(param_names, self.perr))
        # return {name: (val, err) for name, val, err in zip(param_names, self.popt, self.perr)}    
    
    def save_param(self, dir_name = None, file_index=0):
        '''
        Save the best fit parameters
        to a file in a compressed python dict.
        
        # USE the follwing for re-loading 
        
        with open(file, 'rb') as f:
            results = pickle.load(f)
        
        '''
        if self.popt is None:
            raise RuntimeError("Fit not yet performed.")
        
        # Create directory if it doesn't exist
        directory = dir_name
        if directory and not os.path.exists(directory):
            os.makedirs(directory)
        
        filename = dir_name+'res_'+str(file_index).zfill(4)+'.npz'
        with open(filename, 'wb') as f:
            comb = {}
            comb['value'] = self.best_fit_params()
            comb['error'] = self.best_fit_params_error()
            pickle.dump(comb, f)
            
        print(f"Saved data to {filename}")
        pass



    def plot_full(x,y):
        plt.figure(figsize=(8,6.5))
    
        plt.subplot(2, 2, 1)
        plt.plot(x, y.real, '-r.', label='Real')
        plt.plot(x, y.imag, '-b.', label='Imag')
        plt.legend()
    
        plt.subplot(2, 2, 2)
        plt.plot(x, np.angle(y), '-r.', label='angle')
        plt.legend()
    
        plt.subplot(2, 2, 3)
        plt.plot(x, np.abs(y), 'o')
    
        plt.subplot(2, 2, 4)
        plt.plot(y.real, y.imag, '--o')
    
        plt.tight_layout()
        plt.show()
        pass


##############
# EXAMPLE

# from vslab.analysis.fitter_complex import FitterComplex
# from vslab.analysis.data import Data2D

# import matplotlib.pyplot as plt
# import numpy as np
# import pickle

# path = '/Users/vibhor/Downloads/100919_reso_ring_multimode_-30dBm attenuator_2.8_18/'
# da = Data2D(path)

# fr = da.X + 11.427500*1e9
# pw = da.Y

# r= da.Z(2)
# t = da.Z(3)

# s21 = r*np.cos(t) + 1j*r*np.sin(t)

# ft = FitterComplex('S21sideCable')
# ydata = s21[23]
# xdata = fr

# popt, perr = ft.fit(xdata, ydata, save=True, dir_name=da.directory+'/fits/')

