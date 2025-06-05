# Vibhor <v.singh@iisc.ac.in>, 
# Qcodes driver written during the lockdown-2
# 

from time import sleep
from numpy import arange, array
from typing import Any
from qcodes import VisaInstrument, validators as vals
from qcodes.utils.helpers import create_on_off_val_mapping


class APSYN420(VisaInstrument):
    """
    This is the code for APSYN420 RF Signal Generator from ANAPICO
    Status: beta version
    Includes the essential commands from the manual
    
    Non-Comprehensive
    """
    def __init__(self, name: str, address: str,
                 reset: bool = False, **kwargs: Any):
        super().__init__(name, address, terminator='\n', **kwargs)
    # signal synthesis commands
        
        self.add_function('reset', call_cmd='*RST')
        
        self.add_parameter(name='frequency',
                           label='Frequency',
                           unit='Hz',
                           get_cmd='FREQ?',
                           set_cmd='FREQ {:.9f}',
                           get_parser=float,
                           vals=vals.Numbers(min_value=10e6,
                                             max_value=20e9))
        self.add_parameter(name='phase',
                           label='Carrier phase',
                           unit='deg',
                           get_cmd='PHAS?',
                           set_cmd='PHAS {:.1f}',
                           get_parser=float,
                           vals=vals.Numbers(min_value=-360, max_value=360))
        
        self.add_parameter(name='enable_RF',
                           label='RF output',
                           get_cmd=':OUTP?',
                           set_cmd='OUTP {}',
                           val_mapping={'OFF': 0,
                                        'ON': 1})
        
        self.add_parameter(name='pulse_mod_enable',
                           label='Pulse Modulation',
                           get_cmd=':PULM:STAT?',
                           set_cmd=':PULM:STAT {}',
                           val_mapping={'OFF': 0,
                                        'ON': 1})
        
        self.add_parameter(name='pulse_mod_source',
                           label='Pulse Mod Source',
                           get_cmd=':PULM:SOUR?',
                           set_cmd=':PULM:SOUR {}',
                           vals = vals.Enum(*array(['INT', 'EXT'])),
                           docstring = 'Pulse mod source to INT, EXT')
        
        self.add_parameter(name='ext_ref_out_enable',
                           label='Enable external ref output',
                           get_cmd=':ROSC:OUTP?',
                           set_cmd=':ROSC:OUTP {};*WAI',
                           vals = vals.Bool(),
                           docstring = 'BOOL: Enable/disable the ref_out')
        
        self.add_parameter(name='ext_ref_freq',
                           label='External Ref Input frequency',
                           get_cmd=':ROSC:EXT:FREQ?',
                           set_cmd=':ROSC:EXT:FREQ {};*WAI',
                           vals = vals.Enum(*array([10e6, 100e6])),
                           docstring = 'ONLY 10 MHz or 100 MHz allowed')
        
        self.add_parameter(name='ext_ref_source',
                           label='External Ref source -- INT, EXT',
                           get_cmd=':ROSC:SOUR?',
                           set_cmd=':ROSC:SOUR {};*WAI',
                           vals = vals.Enum(*array(['INT', 'EXT'])),
                           docstring = 'set ext clk source as INT or EXT')
        
        self.add_parameter(name='ext_ref_is_lock',
                           label='is ext_ref locked',
                           get_cmd=':ROSC:LOCK?',
                           get_parser = bool,
                           set_cmd = None,
                           docstring = 'check if Ref is locked')
                                        
        self.connect_message()


    def ext_ref(self, val):
        '''
        Enable locking by ext ref of 10 MHz
        True for EXT, False for INT.
        '''
        if val:
            self.ext_ref_out_enable(True)
            self.ext_ref_freq(10e6)
            self.ext_ref_source('EXT')
            for _ in arange(10):
                sleep(1)
                if self.ext_ref_is_lock():
                    print('successfully locked')
                    break
                else:
                    print('unlock...')
        else:
            self.ext_ref_source('INT')
            sleep(1)
            print('clock ref has been set to internal')
        pass
    
    def setup_pulse_mod_ext_on(self):
        '''
        Sets Pulse modulation to external and leaves it ON
        '''
        self.pulse_mod_source('EXT')
        self.pulse_mod_enable('ON')
        pass
    
    def setup_pulse_mod_off(self):
        '''
        Sets Pulse modulation to internal and leaves it OFF
        '''
        self.pulse_mod_source('INT')
        self.pulse_mod_enable('OFF')
        pass

    def power(self, pw):
        '''
        Dumy function to make it compatible with other sources
        Power is fixed at +23 dBm. 
        '''
        print('Power fixed at +23 dBm')
        pass

    def status(self, b):
        '''
        Dumy function to make it compatible with other sources
        Power is fixed at +23 dBm. 
        '''
        if b:
            self.enable_RF('ON')
        else:
            self.enable_RF('OFF')
        pass
    
