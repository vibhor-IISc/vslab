# Vibhor <v.singh@iisc.ac.in>, 
# Qcodes driver written during the lockdown-2
# 

import numpy as np
from time import sleep
from qcodes import VisaInstrument
from qcodes.utils import validators as vals
from qcodes.utils.helpers import create_on_off_val_mapping

from qcodes.instrument.parameter import ParameterWithSetpoints, Parameter


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


class psd(ParameterWithSetpoints):
    def get_raw(self):
        '''
        Use this method for traces
        which takes more than 4 seconds of time.
        
        Return the trace data in dBm
        
        The function polls the status register to ensure
        when trace is over. This avoid visa TimeOut error
        '''
        self.root_instrument.write('INIT:CONT OFF')
        self.root_instrument.write('INIT')
        slp = float(self.root_instrument.ask('SWE:TIME?'))*int(self.root_instrument.ask('SWE:COUN?'))
        sleep(slp + 90)
        
        if self.root_instrument.is_complete():
            _tr = self.root_instrument.ask('TRAC? TRACE1;*WAI')
        return np.array(_tr.split(',')).astype(np.float)


class psd_fast(ParameterWithSetpoints):

    def get_raw(self):
        '''
        Use where total_sweep_time is smaller than 4 seconds. 
        
        Return the trace data in dBm.
        
        For longer sweep time, use .trace() function. 
        '''
        self.root_instrument.sweep_single()
        _tr = self.root_instrument.ask('TRAC? TRACE1;*WAI')
        return np.array(_tr.split(',')).astype(np.float)


class GenerateMarkerArray(Parameter):
    '''
    A parameter that generates the array for the marker frequencies
    '''
    def __init__(self, mlist, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._mlist = mlist

    def get_raw(self):
        return self.root_instrument._markers_X()


class MarkerRead(ParameterWithSetpoints):
    ''' A class to handle the marker read values as parameters'''

    def get_raw(self):
        '''
        Return the corresponding Y values in dBm for an input list
        of frequencies (Hz)
        '''
        return self.root_instrument._markers_Y()


class FSV13_2(VisaInstrument):
    """
    This is the QCoDeS python driver for Rohde and Schwartz FSV13 signal analyzer.

    """


    def __init__(self, name       : str,
                       address    : str,
                       terminator : str="\n",
                       **kwargs):
        """
        QCoDeS driver for the signal analyzer R&S FSV13.
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
                           set_cmd    = ':SENS:FREQ:CENT {}Hz',
                           get_cmd    = ':SENS:FREQ:CENT?',
                           docstring  = 'Center frequency',
                           vals       = vals.Numbers(10, 13e9)
                           )

        self.add_parameter(name       = 'span',
                           unit       = 'Hz',
                           get_parser = float,
                           set_cmd    = ':SENS:FREQ:SPAN {}Hz',
                           get_cmd    = ':SENS:FREQ:SPAN?',
                           docstring  = 'Span',
                           vals       = vals.Numbers(0, 10e9)
                           )

        self.add_parameter(name       = 'start_frequency',
                           unit       = 'Hz',
                           get_parser = float,
                           set_cmd    = ':SENS:FREQ:STAR {}Hz',
                           get_cmd    = ':SENS:FREQ:STAR?',
                           docstring  = 'Start frequency',
                           vals       = vals.Numbers(10, 13e9)
                           )

        self.add_parameter(name       = 'stop_frequency',
                           unit       = 'Hz',
                           get_parser = float,
                           set_cmd    = ':SENS:FREQ:STOP {}Hz',
                           get_cmd    = ':SENS:FREQ:STOP?',
                           docstring  = 'Stop frequency',
                           vals       = vals.Numbers(10, 13e9)
                           )

        self.add_parameter(name       = 'bandwidth',
                           unit       = 'Hz',
                           get_parser = float,
                           set_cmd    = 'BAND {}Hz',
                           get_cmd    = 'BAND?',
                           docstring  = 'resolution bandwidth',
                           vals       = vals.Enum(*np.append(10**7, np.kron([1, 2, 3, 5], 10 ** np.arange(6))))
                           )

        self.add_parameter(name       = 'video_bandwidth',
                           unit       = 'Hz',
                           get_parser = float,
                           set_cmd    = 'BAND:VID {}Hz',
                           get_cmd    = 'BAND:VID?',
                           docstring  = 'post-detection filter (VBW)'
                           )

        self.add_parameter(name       = 'sweep_points',
                           unit       = '',
                           get_parser = int,
                           set_cmd    = 'SWE:POIN {}',
                           get_cmd    = 'SWE:POIN?',
                           docstring  = 'Number of sweep points',
                           vals = vals.Ints(min_value = 101, max_value = 32001)
                           )

        self.add_parameter(name       = 'sweep_count',
                           unit       = '',
                           get_parser = int,
                           set_cmd    = 'SWE:COUN {}',
                           get_cmd    = 'SWE:COUN?',
                           docstring  = 'Number of sweep counts',
                           vals = vals.Ints(min_value = 0, max_value = 32767)
                           )

        self.add_parameter(name       = 'sweep_time',
                           unit       = 's',
                           get_parser = float,
                           set_cmd    = 'SWE:TIME {}s',
                           get_cmd    = 'SWE:TIME?',
                           docstring  = 'Sweep time in seconds',
                           )

        self.add_parameter(name       = 'reference_level',
                           unit       = 'dBm',
                           get_parser = int,
                           set_cmd    = 'DISP:TRAC:Y:RLEV {}dBm',
                           get_cmd    = 'DISP:TRAC:Y:RLEV?',
                           docstring  = 'Reference Level in dBm',
                           vals = vals.Ints(min_value = -100, max_value = 30)
                           )
        
        self.add_parameter(name       = 'sweep_average',
                           unit       = None,
                           set_cmd    = 'DISP:TRAC:MODE {}',
                           get_cmd    = 'DISP:TRAC:MODE?',
                           vals = vals.Bool(),
                           val_mapping = create_on_off_val_mapping(on_val= "AVER", off_val= "WRIT"),
                           docstring  = 'Toggle between Average and Clear/Write modes'
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
                           parameter_class = psd,
                           vals       = vals.Arrays(shape = (self.sweep_points,)),
                           docstring  = 'Return PSD msmt. Try "trace_fast" for sweeptime < 4s traces.'
                           )

        self.add_parameter(name       = 'trace_fast',
                           unit       = 'dBm',
                           label      = 'power',
                           setpoints  = (self.freq_axis,),
                           parameter_class = psd_fast,
                           vals       = vals.Arrays(shape = (self.sweep_points,)),
                           docstring  = 'Return PSD msmt. Use for for fast traces'
                           )

        self.add_parameter(name       = 'markers_read_X',
                           unit       = 'Hz',
                           label      = 'Freq axis',
                           parameter_class = GenerateMarkerArray,
                           mlist      = self._markers_X,
                           vals       = vals.Arrays(shape = (self._markers_count,)),
                           docstring  = 'return the x-value Array of enabled markers'
                           )

        self.add_parameter(name       = 'markers_read_Y',
                           unit       = 'dBm',
                           label      = 'power',
                           setpoints  = (self.markers_read_X,),
                           parameter_class = MarkerRead,
                           vals       = vals.Arrays(shape = (self._markers_count,)),
                           docstring  = 'return y-value Array of enabled markers-'
                           )

        
    
        self.add_function('external_reference', call_cmd='ROSC:SOUR EXT')
        self.add_function('sweep_cont', call_cmd = 'INIT:CONT ON')
        self.add_function('markers_off', call_cmd = 'CALC:MARK:AOFF')
        self.add_function('marker_place_at_max', call_cmd = 'CALC:MARK1:MAX')
        
        
        self.connect_message()
        
        
        
    def sweep_single(self):
        '''  Perform single sweep IMM with *WAI, 
        use _ = trace() to Trigger longer than 4 seconds sweeps
        to avoid VISA timeout error.
        '''
        self.write('INIT:CONT OFF')
        self.write('INIT;*WAI')
    
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


    def _marker_check_on(self, mbit):
        ''' Check if nth-marker is enabled/disabled.
        return bool
        '''
        return bool(int(self.ask(f'CALC:MARK{int(mbit)}?')))

    def _marker_get_x(self, mbit):
        ''' return x-value of a marker at position mbit'''
        return float(self.ask('CALC:MARK'+str(int(mbit))+':X?'))

    def _marker_set_x(self, freqq, mbit=1):
        ''' set mbit marker frequency at freqq'''
        return self.write('CALC:MARK'+str(int(mbit))+f':X {freqq}')


    def _marker_get_y(self, mbit):
        ''' return y-value of a marker at position mbit'''
        return float(self.ask('CALC:MARK'+str(int(mbit))+':Y?'))

    def _markers_count(self):
        ''' Count the number of enabled markers'''
        _count = 0
        for val in np.arange(10):
            if self._marker_check_on(val+1):
                _count = _count+1
            else:
                pass
        return _count

    def markers_add_at(self, mlist):
        for idx, m in enumerate(mlist):
            if self._marker_get_x(idx+1) != m:
                self._marker_set_x(m, idx+1)
            else:
                pass
        pass


    def _markers_X(self):
      _ls = []
      for idx, m in enumerate(np.arange(10)):
        if self._marker_check_on(idx+1):
          _x = self._marker_get_x(idx+1)
          _ls = np.append(_ls, _x)
        else:
          pass
      return _ls


    def _markers_Y(self):
      _ls = []
      for idx, m in enumerate(np.arange(10)):
        if self._marker_check_on(idx+1):
          _y = self._marker_get_y(idx+1)
          _ls = np.append(_ls, _y)
        else:
          pass
      return _ls

    def save_settings(self, fname):
        self.write(f"MMEM:STOR:STAT 1,'{fname}'")

    def load_settings(self, fname):
        self.write(f"MMEM:LOAD:STAT 1,'C:\\R_S\\Instr\\user\\{fname}'")

