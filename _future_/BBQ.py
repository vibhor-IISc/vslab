# -*- coding: utf-8 -*-
"""
Created on Thu Jun  5 16:05:13 2025

@author: user
"""

from scipy.interpolate import UnivariateSpline
import numpy as np
import matplotlib.pyplot as plt

from scipy.constants import e as elec, h

LJ = 8*1e-9
CJ = 5*1e-15
EC = (elec)**2/2/CJ/h

class Mode:
    def __init__(self, freq, y11):
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
        self.L = None
        self.C = None
        self.f0 = None
        
    def zero_slope(self, plot = True):
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
        x = self.freq
        y = self.y11
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
    
    def Kerr_self(self):
        return -1*(self.L/LJ)*(CJ/self.C)*EC
    
    
    def Kerr_cross(self, mode):
        return -2*np.sqrt(self.Kerr_self()*mode.Kerr_self())
    
    
    def detect_zero_crossings(self):
        '''
        Returns
        -------
        None.
        
        For future UPDATE:
            It should be able to scan all the data and find the 
            indices of all zero crossing with positive slope. 

        '''
        pass

        
        
        
        
        
        