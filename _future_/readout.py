# -*- coding: utf-8 -*-
"""
Created on Sun Jun 27 12:28:40 2021

@author: normaluser
"""

from typing import Any

from vslab.constants import *
from vslab.rack import *
import zhinst.qcodes as zi

import numpy as np
from time import sleep, time

from qcodes.instrument_drivers.stanford_research.SG396 import SRS_SG396
from zhinst.qcodes import UHFLI



class readout(UHFLI):
    def __init__(self, address: str, host,
                 reset: bool = False, **kwargs: Any):
        super().__init__(address, host, **kwargs)


    def test(self):
        '''
        This reurns the frequeny of the signal ge.
        '''
        return "Hello"
        pass

    def sideband(self, value: str):
    	self.sideband = value

    def frequency(self, value):
        self.frequency = value

    def mix_freq(self):
        self.mix_freq = 56.25*MHz
    
    def mlist(self):
        IF = self.mix_freq
        if self.sideband == 'left':
            LO_freq = self.frequency + IF
        elif self.sideband == 'right':
            LO_freq = self.frequency - IF
        else:
            print('Unclear sideband')
        return [LO_freq-IF, LO_freq, LO_freq+IF]
    
    # def _uhf_initial_setup():
    # # SET UHF to external 10 MHz
    # uhf.system.extclk(1)
    # # setting all oscillators to common frequency
    # uhf.oscs.oscs0.freq(IF)
    # uhf.oscs.oscs1.freq(IF)
    # uhf.oscs.oscs2.freq(IF)
    # uhf.oscs.oscs3.freq(IF)
    # uhf.oscs.oscs4.freq(IF)
    # uhf.oscs.oscs5.freq(IF)
    # uhf.oscs.oscs6.freq(IF)
    # uhf.oscs.oscs7.freq(IF)
    
    # # Linking Demods to Osc
    # uhf.demods.demods0.oscselect(0)
    # uhf.demods.demods1.oscselect(1)
    # uhf.demods.demods2.oscselect(2)
    # uhf.demods.demods3.oscselect(3)
    # uhf.demods.demods4.oscselect(4)
    # uhf.demods.demods5.oscselect(5)
    # uhf.demods.demods6.oscselect(6)
    # # special command for SSB
    # # to set 8th Demod to 4th Osc
    # uhf.demods.demods7.oscselect(3)
    # pass





# class super1(SRS_SG396):
#     def __init__(self, name: str, address: str,
#                  reset: bool = False, **kwargs: Any):
#         super().__init__(name, address, **kwargs)


#     def my_freq(self):
#         '''
#         This reurns the frequeny of the signal ge.
#         '''
#         return self.frequency()
#         pass
