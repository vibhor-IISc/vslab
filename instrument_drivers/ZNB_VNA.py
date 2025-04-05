# Vibhor <v.singh@iisc.ac.in>, 
# Qcodes driver written during the lockdown-2

# This is a beta version of ZNB VNA driver
# SA template will be used
# We could also explroe VNA template. 
# Since most msmts are going to be S21 msmt, I would
# simply use the SA template. 
# This upgrade we can leave for future. 


import numpy as np
from time import sleep
from typing import Any, Optional, Tuple

from qcodes import VisaInstrument
from qcodes.utils import validators as vals
from qcodes.utils.helpers import create_on_off_val_mapping

from qcodes.instrument.parameter import ParameterWithSetpoints, Parameter, MultiParameter


class GenerateSetPoints(Parameter):
    """
    A parameter that generates a setpoint array from start, stop and num points
    parameters.
    """
    def __init__(self, startparam, stopparam, numpointsparam, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._startparam = startparam
        self._stopparam = stopparam
        self._numpointsparam = numpointsparam

    def get_raw(self):
        return np.linspace(self._startparam(), self._stopparam(),
                              self._numpointsparam())


class S21trace(ParameterWithSetpoints):
    def get_raw(self):
        '''
        Use this method for traces

        '''
        self.root_instrument.write('INIT:CONT OFF')
        self.root_instrument.write('INIT1')
        # In future for timeouts a sleep function can be added below
        # sleep(1)
        
        if self.root_instrument.is_complete():
            _tr = self.root_instrument.ask('TRAC? CH1DATA;*WAI')
            _xy = np.array(_tr.split(',')).astype(float)
        return _xy[0::2]+1j*_xy[1::2]


class S21trace_fast(ParameterWithSetpoints):
    def get_raw(self):
        '''
        Use this method for traces with sweep time smaller than 4 seconds

        '''
        self.root_instrument.sweep_single_fast()
        _tr = self.root_instrument.ask('TRAC? CH1DATA;*WAI')
        _xy = np.array(_tr.split(',')).astype(float)
        return _xy[0::2]+1j*_xy[1::2]


# class IQArray(MultiParameter):
#     def __init__(self, name, start, stop, npts, instrument='ZNB_VNA',*args, **kwargs):
#         super().__init__(name, names=('I', 'Q'), labels = ('mag', 'phase'),
#             setpoint_units=(("Hz",), ("Hz",)), shapes = ((npts,), (npts,)), *args, **kwargs)
#         # self.set_sweep(start, stop, npts)
        
#     def get_raw(self):
#         '''
#         Use this method for traces

#         '''
#         self.root_instrument.write('INIT:CONT OFF')
#         self.root_instrument.write('INIT1')
#         # In future for timeouts a sleep function can be added below
#         # sleep(1)
        
#         if self.root_instrument.is_complete():
#             _tr = self.root_instrument.ask('TRAC? CH1DATA;*WAI')
#             _xy = np.array(_tr.split(',')).astype(float)
#         return _xy[0::2], _xy[1::2]

    # def set_sweep(self, start: float, stop: float, npts: int) -> None:
    #     # Needed to update config of the software parameter on sweep change
    #     # frequency setpoints tuple as needs to be hashable for look up.
    #     f = tuple(np.linspace(int(start), int(stop), num=npts))
    #     self.setpoints = ((f,), (f,))
    #     self.shapes = ((npts,), (npts,))




class ZNB_VNA(VisaInstrument):
    """
    This is the QCoDeS python driver for Rohde and Schwartz ZNB_VNA.

    """


    def __init__(self, name       : str,
                       address    : str,
                       terminator : str="\n",
                       **kwargs):
        """
        QCoDeS driver for the signal analyzer R&S ZNB VNA.
        Args:
        name (str): Name of the instrument.
        address (str): Address of the instrument.
        terminator (str, optional, by default "\n"): Terminator character of
            the string reply.
        """


        super().__init__(name       = name,
                         address    = address,
                         terminator = terminator,
                         **kwargs)


        self.add_function('reset', call_cmd='*RST;*WAI')

        
        self.add_parameter(name       = 'center_frequency',
                           unit       = 'Hz',
                           get_parser = float,
                           set_cmd    = ':SENS:FREQ:CENT {}Hz;*WAI',
                           get_cmd    = ':SENS:FREQ:CENT?;*WAI',
                           docstring  = 'Center frequency',
                           vals       = vals.Numbers(100e3, 19.9e9)
                           )

        self.add_parameter(name       = 'span',
                           unit       = 'Hz',
                           get_parser = float,
                           set_cmd    = ':SENS:FREQ:SPAN {}Hz;*WAI',
                           get_cmd    = ':SENS:FREQ:SPAN?;*WAI',
                           docstring  = 'Span',
                           vals       = vals.Numbers(1, 19.9e9)
                           )

        self.add_parameter(name       = 'start_frequency',
                           unit       = 'Hz',
                           get_parser = float,
                           set_cmd    = ':SENS:FREQ:STAR {}Hz;*WAI',
                           get_cmd    = ':SENS:FREQ:STAR?;*WAI',
                           docstring  = 'Start frequency',
                           vals       = vals.Numbers(100e3, 19.9e9)
                           )

        self.add_parameter(name       = 'stop_frequency',
                           unit       = 'Hz',
                           get_parser = float,
                           set_cmd    = ':SENS:FREQ:STOP {}Hz;*WAI',
                           get_cmd    = ':SENS:FREQ:STOP?;*WAI',
                           docstring  = 'Stop frequency',
                           vals       = vals.Numbers(100e3, 20e9)
                           )

        self.add_parameter(name       = 'power',
                           unit       = 'dBm',
                           get_parser = float,
                           set_cmd    = 'SOUR:POW {};*WAI',
                           get_cmd    = 'SOUR:POW?;*WAI',
                           docstring  = 'Source power',
                           vals       = vals.Numbers(-60, 12)
                           )

        self.add_parameter(name       = 'bandwidth',
                           unit       = 'Hz',
                           get_parser = float,
                           set_cmd    = 'BAND {}Hz;*WAI',
                           get_cmd    = 'BAND?;*WAI',
                           docstring  = 'resolution bandwidth',
                           vals       = vals.Enum(*np.append(10 ** 6,np.kron([1, 1.5, 2, 3, 5, 7], 10 ** np.arange(6))))
                            )

        self.add_parameter(name       = 'sweep_points',
                           unit       = '',
                           get_parser = int,
                           set_cmd    = 'SWE:POIN {};*WAI',
                           get_cmd    = 'SWE:POIN?;*WAI',
                           docstring  = 'Number of sweep points',
                           vals = vals.Ints(min_value = 1, max_value = 12001)
                           )

        self.add_parameter(name       = 'average_count',
                           unit       = '',
                           get_parser = int,
                           set_cmd    = 'AVER:COUN {};*WAI',
                           get_cmd    = 'AVER:COUN?;*WAI',
                           docstring  = 'Number of averages',
                           )

        
        self.add_parameter(name       = 'average_enable',
                           unit       = None,
                           set_cmd    = 'AVER {};*WAI',
                           vals = vals.Bool(),
                           val_mapping = create_on_off_val_mapping(on_val= "ON", off_val= "OFF"),
                           docstring  = 'Toggle Averaging of traces'
                           )

        self.add_parameter(name       = 'freq_axis',
                           unit       = 'Hz',
                           label      = 'Freq axis',
                           parameter_class = GenerateSetPoints,
                           startparam      = self.start_frequency,
                           stopparam       = self.stop_frequency,
                           numpointsparam  = self.sweep_points,
                           vals       = vals.Arrays(shape = (self.sweep_points,)),
                           docstring  = 'Return x-axis in a psd measurement'
                           )

        self.add_parameter(name       = 'trace',
                           unit       = 'dBm',
                           label      = 'power',
                           setpoints  = (self.freq_axis,),
                           parameter_class = S21trace,
                           vals       = vals.Arrays(shape = (self.sweep_points,), valid_types=(np.complex128,)),
                           docstring  = 'Return S21 msmt.'
                           )

        # self.add_parameter(name       = 'traceIQ',
        #                    start      = self.start_frequency,
        #                    stop       = self.stop_frequency,
        #                    npts       = 201,
        #                    parameter_class = IQArray,
        #                    )

        self.add_parameter(name       = 'trace_fast',
                           unit       = 'dBm',
                           label      = 'power',
                           setpoints  = (self.freq_axis,),
                           parameter_class = S21trace_fast,
                           vals       = vals.Arrays(shape = (self.sweep_points,), valid_types=(np.complex128,)),
                           docstring  = 'Return S21 msmt. Do not use for msmt exceeding 4 seconds'
                           )

        self.add_parameter(name       = 'external_reference',
                           unit       = None,
                           set_cmd    = 'ROSC:SOUR {};*WAI',
                           get_cmd    = 'ROSC:SOUR?;*WAI',
                           vals = vals.Bool(),
                           val_mapping = create_on_off_val_mapping(on_val= "EXT", off_val= "INT"),
                           docstring  = 'Toggle between external/internal 10 MHz'
                           )

        
        self.add_function('sweep_cont', call_cmd = 'INIT:CONT ON;*WAI')
        self.add_function('rf_on', call_cmd = 'OUTP ON;*WAI')
        self.add_function('rf_off', call_cmd = 'OUTP OFF;*WAI')

        # self.add_function('autoscale', call_cmd = 'DISP:TRAC:Y:AUTO ONCE') # Should be followed by an INIT
        
        self.connect_message()
        
        
        
    def sweep_single(self):
        '''  Perform single sweep IMM without *OPC?, 
        '''
        self.write('INIT:CONT OFF')
        self.write('INIT1')
        pass

    def sweep_single_fast(self):
        '''  Perform single sweep IMM with *OPC?, 
        '''
        self.write('INIT:CONT OFF')
        self.write('INIT1:IMM')
        self.ask('*OPC?') 
        pass
    
    def is_complete(self):
        '''
        Returns True ONLY when instrument is Ready.
        To prevent VISA Timeout Error.
        It blocks further calls from terminal except Keyboard Interupt.
        '''
        self.write('*ESE 1')
        try:
            while not bool(int(self.ask('*OPC; *ESR?'))):
                sleep(1)
            return True
        except KeyboardInterrupt:
            print('Keyboard intrupption has occured.')


    def fetch_ch1_data(self, wait=1):
        self.write('INIT1;*WAI')
        sleep(wait)
        if self.is_complete:
            _tr = self.ask('TRAC? CH1DATA;*WAI')
            _xy = np.array(_tr.split(',')).astype(float)
            return _xy[0::2]+1j*_xy[1::2]
        else:
            pass

    def fetch_ch2_data(self, wait=1):
        self.write('INIT2;*WAI')
        sleep(wait)
        if self.is_complete:
            _tr = self.ask('TRAC? CH2DATA;*WAI')
            _xy = np.array(_tr.split(',')).astype(float)
            return _xy[0::2]+1j*_xy[1::2]
        else:
            pass




