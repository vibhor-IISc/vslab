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


class super1(SRS_SG396):
    def __init__(self, name: str, address: str,
                 reset: bool = False, **kwargs: Any):
        super().__init__(name, address, **kwargs)


    def my_freq(self):
        '''
        This reurns the frequeny of the signal ge.
        '''
        return self.frequency()
        pass
