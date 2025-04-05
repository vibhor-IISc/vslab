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

    def _is_complete(self):
        '''
        Returns True ONLY when instrument is Ready.
        To prevent VISA Timeout Error.
        '''
        self.root_instrument.write('*ESE 1')
        # self.write('*ESE 1')
        try:
            while not bool(int(self.root_instrument.ask('*OPC; *ESR?'))):
                sleep(1)
            return True
        except KeyboardInterrupt:
            print('Keyboard intrupption caught.')

    def get_raw(self):
        '''
        Use this method for time-consuming traces
        which takes more than 4 seconds of time.
        
        Return the trace data in dBm
        
        
        The function polls the status register to ensure
        when trace is over. This avoid visa TimeOut error
        '''
        self.root_instrument.write('INIT:CONT OFF;*WAI')
        self.root_instrument.write('INIT')
        if self._is_complete():
            _tr = self.root_instrument.ask('TRAC? TRACE1;*WAI')
        return np.array(_tr.split(',')).astype(np.float)


class psd_fast(ParameterWithSetpoints):

    def get_raw(self):
        '''
        Use where total_sweep_time is smaller than 4 seconds. 
        
        Return the trace data in dBm.
        
        For longer sweep time, use get_trace() function. 
        '''
        self.root_instrument.sweep_single()
        _tr = self.root_instrument.ask('TRAC? TRACE1;*WAI')
        return np.array(_tr.split(',')).astype(np.float)


class GenerateMarkerPoint(Parameter):
    '''
    A parameter that generates the list for the marker frequencies
    '''
    def __init__(self, mlist, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._mlist = mlist

    def get_raw(self):
        return mlist


class markervalues(ParameterWithSetpoints):
    def _get_marker_y(self, marker=1):
      return float(self.ask('CALC:MARK'+str(marker)+':Y?'))


    def get_raw(self):
        '''
        Return the corresponding Y values in dBm for an input list
        of frequencies (Hz)
        '''
        self._markers_place_at(mlist)
        _Y = []
        for idx, m in enumerate(mlist):
            _mY = self._get_marker_y(idx+1)
            _Y = np.append(_Y, _mY)
        return _Y




class FSV13(VisaInstrument):
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
                           set_cmd    = ':SENS:FREQ:CENT {}Hz;*WAI',
                           get_cmd    = ':SENS:FREQ:CENT?;*WAI',
                           docstring  = 'Center frequency',
                           vals       = vals.Numbers(10, 13e9)
                           )

        self.add_parameter(name       = 'span',
                           unit       = 'Hz',
                           get_parser = float,
                           set_cmd    = ':SENS:FREQ:SPAN {}Hz;*WAI',
                           get_cmd    = ':SENS:FREQ:SPAN?;*WAI',
                           docstring  = 'Span',
                           vals       = vals.Numbers(0, 10e9)
                           )

        self.add_parameter(name       = 'start_frequency',
                           unit       = 'Hz',
                           get_parser = float,
                           set_cmd    = ':SENS:FREQ:STAR {}Hz;*WAI',
                           get_cmd    = ':SENS:FREQ:STAR?;*WAI',
                           docstring  = 'Start frequency',
                           vals       = vals.Numbers(10, 13e9)
                           )

        self.add_parameter(name       = 'stop_frequency',
                           unit       = 'Hz',
                           get_parser = float,
                           set_cmd    = ':SENS:FREQ:STOP {}Hz;*WAI',
                           get_cmd    = ':SENS:FREQ:STOP?;*WAI',
                           docstring  = 'Stop frequency',
                           vals       = vals.Numbers(10, 13e9)
                           )

        self.add_parameter(name       = 'bandwidth',
                           unit       = 'Hz',
                           get_parser = float,
                           set_cmd    = 'BAND {}Hz;*WAI',
                           get_cmd    = 'BAND?;*WAI',
                           docstring  = 'resolution bandwidth',
                           vals       = vals.Enum(*np.append(10**7, np.kron([1, 2, 3, 5], 10 ** np.arange(6))))
                           )

        self.add_parameter(name       = 'video_bandwidth',
                           unit       = 'Hz',
                           get_parser = float,
                           set_cmd    = 'BAND:VID {}Hz;*WAI',
                           get_cmd    = 'BAND:VID?;*WAI',
                           docstring  = 'post-detection filter (VBW)'
                           )

        self.add_parameter(name       = 'sweep_points',
                           unit       = '',
                           get_parser = int,
                           set_cmd    = 'SWE:POIN {};*WAI',
                           get_cmd    = 'SWE:POIN?;*WAI',
                           docstring  = 'Number of sweep points',
                           vals = vals.Ints(min_value = 101, max_value = 32001)
                           )

        self.add_parameter(name       = 'sweep_count',
                           unit       = '',
                           get_parser = int,
                           set_cmd    = 'SWE:COUN {};*WAI',
                           get_cmd    = 'SWE:COUN?;*WAI',
                           docstring  = 'Number of sweep counts',
                           vals = vals.Ints(min_value = 0, max_value = 32767)
                           )

        self.add_parameter(name       = 'sweep_time',
                           unit       = 's',
                           get_parser = float,
                           set_cmd    = 'SWE:TIME {}s;*WAI',
                           get_cmd    = 'SWE:TIME?;*WAI',
                           docstring  = 'Sweep time in seconds',
                           )

        self.add_parameter(name       = 'reference_level',
                           unit       = 'dBm',
                           get_parser = int,
                           set_cmd    = 'DISP:TRAC:Y:RLEV {}dBm;*WAI',
                           get_cmd    = 'DISP:TRAC:Y:RLEV?;*WAI',
                           docstring  = 'Reference Level in dBm',
                           vals = vals.Ints(min_value = -100, max_value = 30)
                           )
        
        self.add_parameter(name       = 'sweep_average',
                           unit       = None,
                           set_cmd    = 'DISP:TRAC:MODE {};*WAI',
                           get_cmd    = 'DISP:TRAC:MODE?;*WAI',
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
                           docstring  = 'return power measurement: can be used always. Try "trace_fast" for sweeptime < 4s traces.'
                           )

        self.add_parameter(name       = 'trace_fast',
                           unit       = 'dBm',
                           label      = 'power',
                           setpoints  = (self.freq_axis,),
                           parameter_class = psd_fast,
                           vals       = vals.Arrays(shape = (self.sweep_points,)),
                           docstring  = 'return power measurement: use for for fast traces'
                           )


        
    
        self.add_function('external_reference', call_cmd='ROSC:SOUR EXT;*WAI')
        self.add_function('sweep_cont', call_cmd = 'INIT:CONT ON;*WAI')
        self.add_function('markers_off', call_cmd = 'CALC:MARK:AOFF')
        self.add_function('marker_place_at_max', call_cmd = 'CALC:MARK1:MAX')
        
        
        self.connect_message()
        
        
        
    def sweep_single(self):
        '''
        Perform single sweep IMM with *WAI, 
        use _ = get_trace() to Trigger longer than 4 seconds sweeps
        to avoid VISA timeout error.
        
        '''
        self.write('INIT:CONT OFF;*WAI')
        self.write('INIT;*WAI')
    
    def is_complete(self):
        '''
        Returns True ONLY when instrument is Ready.
        To prevent VISA Timeout Error.
        '''
        self.write('*ESE 1')
        try:
            while not bool(int(self.ask('*OPC; *ESR?'))):
                sleep(1)
            return True
        except KeyboardInterrupt:
            print('Keyboard intrupption has occured.')


    def _marker_check_on(self, mbit):
        ''' Return bool if the marker "n" is on/off.
        '''
        return bool(int(sa.ask(f'CALC:MARK{int(mbit)}?')))


    def _markers_read_X(self):
    '''   return the X values of ALREADY placed markers.
    MAX_markers = 10'''
        _ls = []
        for idx, m in np.arange(10):
            if self._marker_check_on(idx+1):
                _x = float(self.ask('CALC:MARK'+str(int(idx+1))+':X?'))
                _ls = np.append(_ls, _x)
            else:
                pass

        return _ls


    def _markers_read_Y(self):
    '''   return the Y values of ALREADY placed markers.
    MAX_markers = 10'''
        _ls = []
        for idx, m in np.arange(10):
            if self._marker_check_on(idx+1):
                _y = float(self.ask('CALC:MARK'+str(int(idx+1))+':Y?'))
                _ls = np.append(_ls, _y)
            else:
                pass

        return _ls
