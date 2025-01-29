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
    # ParameterWithSetpoints,
    # ParamRawDataType,
    create_on_off_val_mapping,
)


# if TYPE_CHECKING:
#     from collections.abc import Sequence

#     from qcodes_loop.data.data_set import DataSet
#     from typing_extensions import Unpack


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

        if channel not in ["CHAN1", "CHAN2"]:
            raise ValueError('channel must be either "CHAN1" or "CHAN2"')

        super().__init__(parent, name, **kwargs)

        self.channel = channel

        self.source_mode = self.add_parameter("source_mode",
                          get_cmd=f"{channel}:SOUR:FUNC?;*WAI",
                          get_parser=str.strip,
                          set_cmd=f"{channel}:SOUR:FUNC {{}}",
                          val_mapping={"current": "CURR", "voltage": "VOLT"},
                          docstring="Selects the type of SOURCE e.g. 'voltage' or 'current'.",
                          )
        
        self.sense_mode = self.add_parameter("sense_mode",
                          get_cmd=f"{channel}:SENS:FUNC?;*WAI",
                          get_parser=str.strip,
                          set_cmd=f"{channel}:SENS:FUNC {{}}",
                          val_mapping={"current": "CURR", "voltage": "VOLT"},
                          docstring="Selects the type of SENSE e.g. 'voltage' or 'current'.",
                          )

        self.source_volt = self.add_parameter("source_volt",
                           get_cmd=f"{channel}:SOUR:VOLT:LEV?;*WAI",
                           get_parser=float,
                           set_cmd=f"{channel}:SOUR:VOLT:LEV {{:.6f}}",
                           label="Voltage",
                           unit="V",
                           docstring="Get/Set the source voltage",
                           )

        self.source_curr = self.add_parameter("source_curr",
                    get_cmd=f"{channel}:SOUR:CURR:LEV?;*WAI",
                    get_parser=float,
                    set_cmd=f"{channel}:SOUR:CURR:LEV {{:.6f}}",
                    label="Current",
                    unit="A",
                    docstring="Get/Set the source current.",
                    )
        
        self.source_volt_range = self.add_parameter("source_volt_range",
                        get_cmd=f"{channel}:SOUR:VOLT:RANG?;*WAI",
                        get_parser=float,
                        set_cmd=f"{channel}:SOUR:VOLT:RANG {{}}",
                        label="Voltage Range",
                        unit="V",
                        vals = vals.Enum(*np.array([200e-3, 2, 7, 18])),
                        docstring="Get/Set the source voltage range",
                        )
        
        self.source_curr_range = self.add_parameter("source_curr_range",
                        get_cmd=f"{channel}:SOUR:CURR:RANG?;*WAI",
                        get_parser=float,
                        set_cmd=f"{channel}:SOUR:CURR:RANG {{}}",
                        label="Current Range",
                        unit="A",
                        vals = vals.Enum(*np.array([200e-9, 2e-6, 20e-6, 200e-6, 2e-3,20e-3,200e-3,1,3])),
                        docstring="Get/Set the source current range",
                        )
        
        self.sense_volt_range = self.add_parameter("sense_volt_range",
                                get_cmd=f"{channel}:SENS:VOLT:RANG?;*WAI",
                                get_parser=float,
                                set_cmd=f"{channel}:SENS:VOLT:RANG {{}}",
                                label="Measure Voltage Range",
                                unit="V",
                                vals = vals.Enum(*np.array([200e-3, 2, 7, 18])),
                                docstring="Get/Set the sense voltage range",
                                )
        
        self.sense_curr_range = self.add_parameter("sense_curr_range",
                                get_cmd=f"{channel}:SENS:CURR:RANG?;*WAI",
                                get_parser=float,
                                set_cmd=f"{channel}:SENS:CURR:RANG {{}}",
                                label="Measure Current Range",
                                unit="A",
                                vals = vals.Enum(*np.array([200e-9, 2e-6, 20e-6, 200e-6, 2e-3,20e-3,200e-3,1,3])),
                                docstring="Get/Set the sense current range",
                                )

        self.volt_limit = self.add_parameter("volt_limit",
                            get_cmd=f"{channel}:SOUR:VOLT:PROT:LEV?;*WAI",
                            get_parser=float,
                            set_cmd=f"{channel}:SOUR:VOLT:PROT:LEV {{}}",
                            label="Voltage limit",
                            unit="V",
                            vals = vals.Numbers(min_value = 5e-3, max_value = 18),
                            docstring="Get/Set the voltage limit for the current source operation",
                            )
        
        self.curr_limit = self.add_parameter("curr_limit",
                            get_cmd=f"{channel}:SOUR:CURR:PROT:LEV?;*WAI",
                            get_parser=float,
                            set_cmd=f"{channel}:SOUR:CURR:PROT:LEV {{}}",
                            label="Current",
                            unit="A",
                            vals = vals.Enum(*np.array(200e-9, 2e-6, 20e-6, 200e-6, 2e-3,20e-3,200e-3,1,3)),
                            docstring="Get/Set the current limit for the voltage source operation",
                            )

                
        self.measure = self.add_parameter("measure",
                            get_cmd=f"{channel}:MEAS?;*WAI",
                            get_parser=float,
                            docstring="Get the measured result",
                            )
        
        self.wire2or4 = self.add_parameter("wire2or4",
                            get_cmd=f"{channel}:SENS:REM?;*WAI",
                            get_parser=float,
                            set_cmd=f"{channel}:SENS:REM {{}}",
                            vals = vals.Bool(),
                            val_mapping={"on": 1, "off": 0},
                            docstring = "Get/Set 4wire (true or 1) or 2wire (false or 0)",
                            )

        self.output = self.add_parameter("output",
                            get_cmd=f"{channel}:SOUR:OUTP?;*WAI",
                            get_parser=bool,
                            set_cmd=f"{channel}.source.output={{:d}}",
                            val_mapping={"on": 1, "off": 0},
                            docstring="Get/Set output to  ON (1)/OFF(0)",
                            )
        

    def configIV(self, source_voltage_range = 200e-3, 
                 sense_current_range = 1e-3 ,
                 current_limit=10e-3):
        '''
        Parameters
        ----------
        source_voltage_range : TYPE, optional
            DESCRIPTION. The default is 200e-3.
        sense_current_range : TYPE, optional
            DESCRIPTION. The default is 1e-3.
        current_limit : TYPE, optional
            DESCRIPTION. The default is 10e-3.
        Returns
        -------
        Configure to set voltage and measure current
        '''
        self.source_mode('voltage')
        self.source_volt(0.0)
        self.source_volt_range(source_voltage_range)
        self.sense_curr_range(sense_current_range)
        self.curr_limit(current_limit)
        pass
    
    def configVI(self, source_current_range=1e-6, 
                 sense_voltage_range = 200e-3, 
                 voltage_limit=10e-3,
                 W4=0):
        '''
        Parameters
        ----------
        source_current_range : TYPE, optional
            DESCRIPTION. The default is 1e-6.
        sense_voltage_range : TYPE, optional
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
        self.source_mode('current')
        self.source_curr(0.0)
        self.source_curr_range(source_current_range)
        self.sense_volt_range(sense_voltage_range)
        self.volt_limit(voltage_limit)
        self.wire2or4(W4)        
        pass

    def setTo(self, value):
        '''
        Parameters
        ----------
        value : TYPE
            set value of the source.
        Returns
        -------
        None.
        '''
        if self.source_mode.get() == 'current' and self.source_curr_range.get() >= np.abs(value):
            self.source_curr(value)
        if self.source_mode.get() == 'voltage' and self.source_volt_range.get() >= np.abs(value):
            self.source_volt(value)
        else:
            raise Exception('Failed! Could not determine the source type.')

    def source_range_auto_toggle(self):
        '''
        Toggle the source range between Auto and Manual
        Returns
        -------
        None.
        '''
        if self.source_mode.get() == 'current':
            self.write(f'{self.channel}:SOUR:CURR:RANG:AUTO')
        if self.source_mode.get() == 'voltage':
            self.write(f'{self.channel}:SOUR:VOLT:RANG:AUTO')
        else:
            raise Exception('Failed! Could not determine the source type.')

    def sense_range_auto_toggle(self):
        '''
        Toggle the sense range between Auto and Manual
        Returns
        -------
        None.
        '''
        if self.sense_mode.get() == 'current':
            self.write(f'{self.channel}:SENS:CURR:RANG:AUTO')
        if self.sense_mode.get() == 'voltage':
            self.write(f'{self.channel}:SENS:VOLT:RANG:AUTO')
        else:
            raise Exception('Failed! Could not determine the source type.')


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
        Sweep the channel output to target_value within 4 seconds.
        DO NOT USE WITH AUTO RANGE.
        '''
        _start_time = perf_counter()

        if self.source_mode.get() == 'current':
            _range = self.souce_curr_range()
            _value = self.source_curr()
            
            sign = np.sign(target_value - _value)
            while np.abs(self.source_curr() - target_value) > step_factor*_range:
                now = self.source_curr()
                sleep(0.03)
                self.source_curr(now + sign*step_factor*_range)
            if np.abs(self.source_curr() - target_value) <=step_factor*_range:
                self.source_curr(target_value)
                return 
            if perf_counter()-_start_time > timeout:
                raise TimeoutError("Failed to reach the target value")
        elif self.source_mode.get() == 'voltage':
            _range = self.source_volt_range()
            _value = self.source_volt()
            sign = np.sign(target_value - _value)
            while np.abs(self.source_volt() - target_value) > step_factor*_range:
                now = self.source_volt()
                sleep(0.03)
                self.source_volt(now + sign*step_factor*_range)
            if np.abs(self.source_volt() - target_value) <= step_factor*_range:
                self.source_volt(target_value)
                return
            if perf_counter - _start_time > timeout:
                raise TimeoutError("Failed to reach the target value")
        else:
            raise Exception("Unable to determine the mode")
    


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
        for ch in ["CHAN1", "CHAN2"]:
            ch_name = f"{ch}"
            channel = YokogawaChannel(self, ch_name, ch_name)
            self.add_submodule(ch_name, channel)
        
        
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


        
        
    




