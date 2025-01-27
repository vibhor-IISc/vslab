import logging
import struct
import sys
import warnings
from enum import Enum
from typing import TYPE_CHECKING, Any, Literal

import numpy as np
from time import sleep, perf_counter

import qcodes.validators as vals
from qcodes.instrument import (
    Instrument,
    InstrumentChannel,
    VisaInstrument,
    VisaInstrumentKWArgs,
)
from qcodes.parameters import (
    ArrayParameter,
    Parameter,
    ParameterWithSetpoints,
    ParamRawDataType,
    create_on_off_val_mapping,
)


if TYPE_CHECKING:
    from collections.abc import Sequence

    from qcodes_loop.data.data_set import DataSet
    from typing_extensions import Unpack


class YokogawaChannel(InstrumentChannel):
    """
    Update later

    """

    def __init__(
        self,
        parent: Instrument,
        name: str,
        channel: str,
        **kwargs: "Unpack[InstrumentBaseKWArgs]",
    ) -> None:
        """
        Args:
            parent: The Instrument instance to which the channel is
                to be attached.
            name: The 'colloquial' name of the channel
            channel: The name used by the Yokogawa, i.e. either
                'CH1' or 'CH2'
            **kwargs: Forwarded to base class.

        """

        if channel not in ["CH1", "CH2"]:
            raise ValueError('channel must be either "CH1" or "CH2"')

        super().__init__(parent, name, **kwargs)
        self.model = self._parent.model



        self.mode = self.add_parameter(
            "mode",
            get_cmd=f"{channel}:SOUR:FUNC?;*WAI",
            get_parser=str.strip,
            set_cmd=f"{channel}:SOUR:FUNC {}",
            val_mapping={"current": "CURR", "voltage": "VOLT"},
            docstring="Selects the type of source e.g. 'voltage' or 'current' .",
        )
        """Parameter mode"""

        self.volt = self.add_parameter(
            "volt",
            get_cmd=f"{channel}:SOUR:VOLT:LEV?;*WAI",
            get_parser=float,
            set_cmd=f"{channel}:SOUR:VOLT:LEV {{:.6f}}",
            label="Voltage",
            unit="V",
            docstring="Get/Set the voltage",
        )
        """Parameter volt"""

        self.curr = self.add_parameter(
            "curr",
            get_cmd=f"{channel}:SOUR:CURR:LEV?;*WAI",
            get_parser=float,
            set_cmd=f"{channel}:SOUR:CURR:LEV {{:.6f}}",
            label="Current",
            unit="A",
            docstring="Get/Set the current.",
        )
        """Parameter curr"""
        
        self.volt_range = self.add_parameter(
            "volt_range",
            get_cmd=f"{channel}:SOUR:VOLT:RANG?;*WAI",
            get_parser=float,
            set_cmd=f"{channel}:SOUR:VOLT:RANG {}",
            label="Voltage Range",
            unit="V",
            vals = vals.Enum(*np.array(200e-3, 2, 7, 18)),
            docstring="Get/Set the voltage range",
        )
        """Parameter volt_range"""
        
        self.curr_range = self.add_parameter(
            "curr_range",
            get_cmd=f"{channel}:SOUR:CURR:RANG?;*WAI",
            get_parser=float,
            set_cmd=f"{channel}:SOUR:CURR:RANG {}",
            label="Current Range",
            unit="A",
            vals = vals.Enum(*np.array(200e-9, 2e-6, 20e-6, 200e-6, 2e-3,20e-3,200e-3,1,3)),
            docstring="Get/Set the current range",
        )
        """Parameter curr_range"""
        
        self.measure_volt_range = self.add_parameter(
            "measure_volt_range",
            get_cmd=f"{channel}:SENS:VOLT:RANG?;*WAI",
            get_parser=float,
            set_cmd=f"{channel}:SENS:VOLT:RANG {}",
            label="Measure Voltage Range",
            unit="V",
            vals = vals.Enum(*np.array(200e-3, 2, 7, 18)),
            docstring="Get/Set the measure voltage range",
        )
        """Parameter measure volt_range"""
        
        self.measure_curr_range = self.add_parameter(
            "measure_curr_range",
            get_cmd=f"{channel}:SENS:CURR:RANG?;*WAI",
            get_parser=float,
            set_cmd=f"{channel}:SENS:CURR:RANG {}",
            label="Measure Current Range",
            unit="A",
            vals = vals.Enum(*np.array(200e-9, 2e-6, 20e-6, 200e-6, 2e-3,20e-3,200e-3,1,3)),
            docstring="Get/Set the measure current range",
        )
        """Parameter curr_range"""

        self.volt_limit = self.add_parameter(
            "volt_limit",
            get_cmd=f"{channel}:SOUR:VOLT:PROT:LEV?;*WAI",
            get_parser=float,
            set_cmd=f"{channel}:SOUR:VOLT:PROT:LEV {}",
            label="Voltage limit",
            unit="V",
            vals = vals.Numbers(min_value = 5e-3, max_value = 18),
            docstring="Get/Set the voltage limit for the current source operation",
        )
        """Parameter volt_limit"""
        
        self.curr_limit = self.add_parameter(
            "curr_limit",
            get_cmd=f"{channel}:SOUR:CURR:PROT:LEV?;*WAI",
            get_parser=float,
            set_cmd=f"{channel}:SOUR:CURR:PROT:LEV {}",
            label="Current",
            unit="A",
            # vals = vals.Enum(*np.array(200e-9, 2e-6, 20e-6, 200e-6, 2e-3,20e-3,200e-3,1,3)),
            docstring="Get/Set the current limit for the voltage source operation",
        )
        """Parameter curr_limit"""
                
        self.measure = self.add_parameter(
            "measure",
            get_cmd=f"{channel}:MEAS?;*WAI",
            get_parser=float,
            docstring="Get the measured result",
        )
        """Parameter measure"""
        
        self.wire2or4 = self.add_parameter(
            "wire2or4",
            get_cmd=f"{channel}:SENS:REM?;*WAI",
            get_parser=float,
            set_cmd=f"{channel}:SENS:REM {}",
            vals = vals.Bool(),
            val_mapping={"on": 1, "off": 0},
            docstring = "Get/Set 4wire (true or 1) or 2wire (false or 0)",
        )
        """Parameter W2 or W4"""

        self.output = self.add_parameter(
            "output",
            get_cmd=f"{channel}:SOUR:OUTP?;*WAI",
            get_parser=bool,
            set_cmd=f"{channel}.source.output={{:d}}",
            val_mapping={"on": 1, "off": 0},
            docstring="Get/Set output to  ON (1)/OFF(0)",
        )
        """Parameter output"""

        self.channel = channel
             
    def configIV(self, voltage_range = 200e-3, 
                 measure_current_range = 1e-3 ,
                 current_limit=10e-3):
        '''
        Parameters
        ----------
        voltage_range : TYPE, optional
            DESCRIPTION. The default is 200e-3.
        measure_current_range : TYPE, optional
            DESCRIPTION. The default is 1e-3.
        current_limit : TYPE, optional
            DESCRIPTION. The default is 10e-3.
        Returns
        -------
        Configure to set voltage and measure current
        '''
        self.mode('voltage')
        self.volt(0.0)
        self.volt_range(voltage_range)
        self.measure_curr_range(measure_current_range)
        self.curr_limit(current_limit)
        pass
    
    def configVI(self, current_range=1e-6, 
                 measure_voltage_range = 200e-3, 
                 voltage_limit=10e-3,
                 W4=0):
        '''
        Parameters
        ----------
        current_range : TYPE, optional
            DESCRIPTION. The default is 1e-6.
        measure_voltage_range : TYPE, optional
            DESCRIPTION. The default is 200e-3.
        voltage_limit : TYPE, optional
            DESCRIPTION. The default is 10e-3.
        W4 (4-wire): TYPE, optional
            DESCRIPTION. The default is 0 (false)
            
        Returns
        -------
        Configure to set current and measure voltage.
        Default 2W measurement.
        '''
        self.mode('current')
        self.curr(0.0)
        self.curr_range(current_range)
        self.measure_volt_range(measure_voltage_range)
        self.volt_limit(voltage_limit)
        self.wire2or4(W4)        
        pass
    
    def sweepTo(self, target_value = 0,step_factor=0.01, timeout=5):
        '''
        Parameters
        ----------
        target_value : TYPE, optional
            DESCRIPTION. The default is 0.
        step_factor : TYPE, optional
            DESCRIPTION. The default is 0.01
        timeout : TYPE, optional
            DESCRIPTION. The default is 5 seconds.
        Returns
        -------
        Sweep the channel output to target_value
        '''
        _start_time = perf_counter()

        if self.mode.get() == 'current':
            _range = self.curr_range()
            _value = self.curr()
            
            sign = np.sign(target_value - _value)
            while np.abs(self.curr() - target_value) > step_factor*_range:
                now = self.curr()
                sleep(0.03)
                self.curr(now + sign*step_factor*_range)
            if np.abs(self.curr() - target_value) <=step_factor*_range:
                self.curr(target_value)
                return 
            if perf_counter()-_start_time > timeout:
                raise TimeoutError("Failed to reach the target value")
        elif self.mode.get() == 'voltage':
            _range = self.volt_range()
            _value = self.volt()
            sign = np.sign(target_value - _value)
            while np.abs(self.volt() - target_value) > step_factor*_range:
                now = self.volt()
                sleep(0.03)
                self.volt(now + sign*step_factor*_range)
            if np.abs(self.volt() - target_value) <= step_factor*_range:
                self.volt(target_value)
                return
            if perf_counter - _start_time > timeout:
                raise TimeoutError("Failed to reach the target value")
        else:
            raise Exception("Unable to determine the mode")
        pass
    




class GS820(VisaInstrument):
    """
    This is the qcodes driver for the Yokogawa GS820 Source-Meter series.
    Add more verbose later. 

    """

    default_terminator = "\n"

    def __init__(
        self, name: str, address: str, **kwargs: "Unpack[VisaInstrumentKWArgs]"
    ) -> None:
        """
        Args:
            name: Name to use internally in QCoDeS
            address: VISA ressource address
            **kwargs: kwargs are forwarded to the base class.

        """
        super().__init__(name, address, **kwargs)


        # Add the channel to the instrument
        for ch in ["CH1", "CH2"]:
            ch_name = f"{ch}"
            channel = YokogawaChannel(self, ch_name, ch_name)
            self.add_submodule(ch_name, channel)
            pass
        
        
        
        self.add_function('reset', call_cmd='*RST;*WAI')

        self.connect_message()


    def iscomplete(self):
        _start_time = perf_counter()
        while True:
            if self.query('*OPC?')=='1':
                return True
            if perf_counter() - _start_time > 3:
                raise TimeoutError("Function did not return True within the timeout period.")
            sleep(0.01)


        
        
    




