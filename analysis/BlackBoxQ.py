# -*- coding: utf-8 -*-
"""
Created on Thu Jun  5 16:05:13 2025

@author: user
"""

from scipy.interpolate import UnivariateSpline
import numpy as np
import matplotlib.pyplot as plt

from scipy.constants import e as elec, h



class Mode:
    def __init__(self, freq, y11, LJ = 8*1e-9, plot=True):
        '''
        Parameters
        ----------
        freq : Hz
            Frequency
        y11 : Ohm^-1
            Admittance.

        Returns
        -------
        Initialize the Ojbect. 
        Use zero_slop() method to attach the 
        additional properties

        '''
        self.freq = freq
        self.y11 = y11
        Llist = np.array([])
        Clist = np.array([])
        f0list = np.array([])
        self._EC = (elec)**2/2/h
        self.LJ = LJ
        
        zero_indices = np.where((self.y11[1:] > 0) & (self.y11[:-1] < 0))[0] + 1
        zero_crossings = self.freq[zero_indices]
        
        self.mode_count = len(zero_crossings)
        
        print('Detected zero-crossings with +ve slope: ', self.mode_count)
        
        for mode_index in zero_indices:
            fm, Cm, Lm = self.zero_slope(self.freq[mode_index-5:mode_index+5],
                                        self.y11[mode_index-5:mode_index+5],
                                        plot)
            
            f0list = np.append(f0list, fm)
            Clist = np.append(Clist, Cm)
            Llist = np.append(Llist, Lm)
        
        
        self.f0 = f0list
        self.L = Llist
        self.C = Clist
        
        self.Chi_mat = np.zeros((self.mode_count, self.mode_count))
        for idx1 in range(self.mode_count):
            self.Chi_mat[idx1,idx1] = self.Kerr_self(idx1)
            
            for idx2 in range(self.mode_count):
                self.Chi_mat[idx1,idx2] = self.Kerr_cross(idx1, idx2)
                
        print(f'{self.mode_count} mode found at:')
        print("  ".join(f"{self.format_value(val):>15}" for val in self.f0), end='\n')
        print(r'Printing chi matrix below:')
        for row in self.fancy_matrix(self.Chi_mat):
            print("  ".join(f"{val:>15}" for val in row))  # right-align for cleaner look
        
        
            
            
    def zero_slope(self, x, y, plot = True):
        '''
        Parameters
        ----------
        plot : Bool, To the data and fit results
            DESCRIPTION. The default is True.

        Returns
        -------
        List of mode frequency, capacitance, and inductance. 
        Update the attributes of Mode object

        '''
        y11_smooth = UnivariateSpline(x, y)
        y11_smooth.set_smoothing_factor(1)
        zeros = y11_smooth.roots()
        fp = zeros[0]
        slope = y11_smooth.derivative()
        slp = slope(zeros)
        sl = slp[0]
        Cp = 1/4/3.14*sl
        Lp = 1/(2*3.14*fp)**2/Cp
        
        self.f0 = fp
        self.L = Lp
        self.C = Cp
        
        if plot:
            plt.plot(x,y,'o', label = f'Cp = {Cp:.2e}')
            plt.plot(x, y11_smooth(x), '--', label = f'Lp = {Lp:.2e}')
            plt.plot(y11_smooth.roots(),[0.0],'*', markersize = 15, label=f'fp = {fp:.3e}')
            plt.legend()
            plt.show()
        return [fp, Cp, Lp]
    
    def Kerr_self(self, mode_index):
        return -1*(self.L[mode_index]/self.LJ)*(1/self.C[mode_index])*self._EC
    
    def Kerr_cross(self, mode_index1, mode_index2):
        return -2*np.sqrt(self.Kerr_self(mode_index1)*self.Kerr_self(mode_index2))
    
    
    def format_value(self, val):
        abs_val = abs(val)
        if abs_val >= 1e9:
            return f"{val / 1e9:.3f} GHz"
        elif abs_val >= 1e6:
            return f"{val / 1e6:.3f} MHz"
        elif abs_val >= 1e3:
            return f"{val / 1e3:.3f} kHz"
        else:
            return f"{val:.3f} Hz"
        
        
    def fancy_matrix(self, freq_matrix):
        formatted_matrix = [
            [self.format_value(val) for val in row]
            for row in freq_matrix
        ]

        return formatted_matrix

    
############  Example

import numpy as np
import matplotlib.pyplot as plt
from vslab.analysis.QUCSDataset import QUCSDataset


from vslab.analysis.BlackBoxQ import Mode

files = list(Path.cwd().glob('*dispersive*.dat'))
parser = QUCSDataset(files[0])
parser.parse()


freq = np.array(parser.get_independent_vars()['frequency'])/GHz
y3 = np.array(parser.get_data()['imag_Y33']['values'])

LJ=8*1e-9

m0 = Mode(freq*GHz, y3, LJ, True)
        
        
        
        
        