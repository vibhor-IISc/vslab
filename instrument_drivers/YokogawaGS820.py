import numpy as np
import time
from time import perf_counter

import qcodes.validators as vals
from qcodes.instrument import (
    Instrument,
    InstrumentChannel,
    VisaInstrument,
)
from qcodes.parameters import (
    ArrayParameter,
    Parameter,
    create_on_off_val_mapping,
)


class YokogawaChannel(InstrumentChannel):
    """
    Update later

    """

    def __init__(
        self,
        parent: Instrument,
        name: str,
        channel: str,
        **kwargs,
    ):
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

        self.add_parameter("source_mode",
                          get_cmd=f"{channel}:SOUR:FUNC?;*WAI",
                          get_parser=str.strip,
                          set_cmd=f"{channel}:SOUR:FUNC {{}}",
                          val_mapping={"current": "CURR", "voltage": "VOLT"},
                          docstring="Selects the type of SOURCE e.g. 'voltage' or 'current'.",
                          )
        
        self.add_parameter("sense_mode",
                          get_cmd=f"{channel}:SENS:FUNC?;*WAI",
                          get_parser=str.strip,
                          set_cmd=f"{channel}:SENS:FUNC {{}}",
                          val_mapping={"current": "CURR", "voltage": "VOLT"},
                          docstring="Selects the type of SENSE e.g. 'voltage' or 'current'.",
                          )

        self.add_parameter("source_volt",
                           get_cmd=f"{channel}:SOUR:VOLT:LEV?;*WAI",
                           get_parser=float,
                           set_cmd=f"{channel}:SOUR:VOLT:LEV {{:.6f}}",
                           label="Voltage",
                           unit="V",
                           docstring="Get/Set the source voltage",
                           )

        self.add_parameter("source_curr",
                    get_cmd=f"{channel}:SOUR:CURR:LEV?;*WAI",
                    get_parser=float,
                    set_cmd=f"{channel}:SOUR:CURR:LEV {{:.6f}}",
                    label="Current",
                    unit="A",
                    docstring="Get/Set the source current.",
                    )
        
        self.add_parameter("source_volt_range",
                        get_cmd=f"{channel}:SOUR:VOLT:RANG?;*WAI",
                        get_parser=float,
                        set_cmd=f"{channel}:SOUR:VOLT:RANG {{}}",
                        label="Voltage Range",
                        unit="V",
                        vals = vals.Enum(*np.array([200e-3, 2, 7, 18])),
                        docstring="Get/Set the source voltage range",
                        )
        
        self.add_parameter("source_curr_range",
                        get_cmd=f"{channel}:SOUR:CURR:RANG?;*WAI",
                        get_parser=float,
                        set_cmd=f"{channel}:SOUR:CURR:RANG {{}}",
                        label="Current Range",
                        unit="A",
                        vals = vals.Enum(*np.array([200e-9, 2e-6, 20e-6, 200e-6, 2e-3,20e-3,200e-3,1,3])),
                        docstring="Get/Set the source current range",
                        )
        
        self.add_parameter("sense_volt_range",
                                get_cmd=f"{channel}:SENS:VOLT:RANG?;*WAI",
                                get_parser=float,
                                set_cmd=f"{channel}:SENS:VOLT:RANG {{}}",
                                label="Measure Voltage Range",
                                unit="V",
                                vals = vals.Enum(*np.array([200e-3, 2, 7, 18])),
                                docstring="Get/Set the sense voltage range",
                                )
        
        self.add_parameter("sense_curr_range",
                                get_cmd=f"{channel}:SENS:CURR:RANG?;*WAI",
                                get_parser=float,
                                set_cmd=f"{channel}:SENS:CURR:RANG {{}}",
                                label="Measure Current Range",
                                unit="A",
                                vals = vals.Enum(*np.array([200e-9, 2e-6, 20e-6, 200e-6, 2e-3,20e-3,200e-3,1,3])),
                                docstring="Get/Set the sense current range",
                                )

        self.add_parameter("volt_limit",
                            get_cmd=f"{channel}:SOUR:VOLT:PROT:LEV?;*WAI",
                            get_parser=float,
                            set_cmd=f"{channel}:SOUR:VOLT:PROT:LEV {{}}",
                            label="Voltage limit",
                            unit="V",
                            vals = vals.Numbers(min_value = 5e-3, max_value = 18),
                            docstring="Get/Set the voltage limit for the current source operation",
                            )
        
        self.add_parameter("curr_limit",
                            get_cmd=f"{channel}:SOUR:CURR:PROT:LEV?;*WAI",
                            get_parser=float,
                            set_cmd=f"{channel}:SOUR:CURR:PROT:LEV {{}}",
                            label="Current",
                            unit="A",
                            vals = vals.Numbers(min_value = 10*1e-9 , max_value=500*1e-3),
                            docstring="Get/Set the current limit for the voltage source operation. Validators may have issues.",
                            )

                
        self.add_parameter("measure",
                            get_cmd=f"{channel}:MEAS?;*WAI",
                            get_parser=float,
                            docstring="Get the measured result",
                            )
        
        self.add_parameter("wire2or4",
                            get_cmd=f"{channel}:SENS:REM?;*WAI",
                            get_parser=str,
                            set_cmd=f"{channel}:SENS:REM {{}}",
                            vals = vals.Bool(),
                            val_mapping={"on": 1, "off": 0},
                            docstring = "Use 'on' for 4wire and 'off' for 2 wire",
                            )

        self.add_parameter("output",
                            get_cmd=f"{channel}:OUTP?;*WAI",
                            get_parser=str,
                            set_cmd=f"{channel}:OUTP {{}}",
                            val_mapping={"on": '1' , "off": '1'},
                            docstring="Get/Set output to  ON (1)/OFF(0)",
                            )
        
    def configIV(self, source_voltage_range = 200e-3, 
                 sense_current_range = 20e-3 ,
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
        self.sense_mode('current')
        self.sense_curr_range(sense_current_range)
        self.curr_limit(current_limit)
        pass
    
    def configVI(self, source_current_range=2e-6, 
                 sense_voltage_range = 200e-3, 
                 voltage_limit=10e-3,
                 W4='off'):
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
        self.sense_mode('voltage')
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
        if self.source_mode.get() == 'current':
            self.source_curr(value)
            return
        if self.source_mode.get() == 'voltage':
            self.source_volt(value)
            return
        else:
            raise Exception('Failed! Could not determine the source type.')

    def source_range_auto(self, val):
        '''
        Source range between Auto and Manual
        Inputs ('OFF', 0, 'ON', 1)
        Returns
        -------
        None.
        '''
        if self.source_mode.get() == 'current':
            self.write(f'{self.channel}:SOUR:CURR:RANG:AUTO {val}')
            return
        if self.source_mode.get() == 'voltage':
            self.write(f'{self.channel}:SOUR:VOLT:RANG:AUTO {val}')
            return
        else:
            raise Exception('Failed! Could not determine the source type.')

    def sense_range_auto(self, val):
        '''
        Sense range between Auto and Manual
        Inputs ('OFF', 0, 'ON', 1)
        Returns
        -------
        None.
        '''
        if self.sense_mode.get() == 'current':
            self.write(f'{self.channel}:SENS:CURR:RANG:AUTO {val}')
            return
        if self.sense_mode.get() == 'voltage':
            self.write(f'{self.channel}:SENS:VOLT:RANG:AUTO {val}')
            return
        else:
            raise Exception('Failed! Could not determine the source type.')


    def sweepTo(self, target_value = 0,step_factor=0.01, timeout=5, sleep=0.03):
        '''
        Parameters
        ----------
        target_value : TYPE, optional
            DESCRIPTION. The default is 0.
        step_factor : TYPE, optional
            DESCRIPTION. The default is 0.01
        timeout : TYPE, optional
            DESCRIPTION. The default is 5 seconds.
        sleep : float
            Sleep time in seconds.
        Returns
        -------
        Sweep the channel output to target_value within 4 seconds.
        DO NOT USE WITH AUTO RANGE.
        '''
        _start_time = perf_counter()

        if self.source_mode.get() == 'current':
            _range = self.source_curr_range()
            _value = self.source_curr()
            
            sign = np.sign(target_value - _value)
            while np.abs(self.source_curr() - target_value) > step_factor*_range:
                now = self.source_curr()
                time.sleep(sleep)
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
                time.sleep(sleep)
                self.source_volt(now + sign*step_factor*_range)
            if np.abs(self.source_volt() - target_value) <= step_factor*_range:
                self.source_volt(target_value)
                return
            if perf_counter - _start_time > timeout:
                raise TimeoutError("Failed to reach the target value")
        else:
            raise Exception("Unable to determine the mode")

    
    def sweep(self, start, stop, pnts, avg=1, both=False, sleep=0.01, W4=False):
        '''
        Parameters
        ----------
        start : float
            Start value of the sweep parameter.
        stop : float
            Stop value of the sweep parameter.
        pnts : Int
            Number of points.
        avg : Int, optional
            Number of average. The default is 1.
        both : Bool, optional
            Sweep direction. The default is False.
        sleep : float, optional
            Delay (in seconds) between set and get. The default is 0.01 ms.
        W4 : Bool, optional
            True for 4wire, False for 2Wire. The default is False.
        Returns
        -------
        set_value_array, measured_array
            DESCRIPTION.
        '''
        xvals = np.linspace(start,stop,pnts)
        if W4:
            self.wire2or4('on')
        else:
            self.wire2or4('off')
        if both:
            xvals = np.append(xvals, np.flip(xvals))
        yvals = []
       
        for x in xvals:
            self.sweepTo(x)
            y = 0
            for val in range(avg):
                time.sleep(sleep)
                y = y+self.measure()
            yvals.append(y/avg)
        return xvals, np.array(yvals)
    
class GS820(VisaInstrument):
    """
    This is the qcodes driver for the Yokogawa GS820 Source-Meter series.
    Create channels as:
        ch1 = gs.CHAN1
        ch2 = gs.CHAN2
        
    Chennels have channel specific commands
    Common cmd would remain with the instrument.
    e.g. 
    gs.reset()
    
    """
    
    default_terminator = "\n"
    
    def __init__(
        self, name: str, address: str,  terminator="\n", **kwargs
    ) -> None:
        """
        Args:
            name: Name to use internally in QCoDeS
            address: VISA ressource address
            **kwargs: kwargs are forwarded to the base class.

        """
        super().__init__(name, address,  terminator="\n", **kwargs)


        # Add the channel to the instrument
        for ch in ["CHAN1", "CHAN2"]:
            channel = YokogawaChannel(self, ch, ch)
            self.add_submodule(ch, channel)
        
        self.connect_message()
        
        self.add_function('reset', call_cmd='*RST;*WAI')

    def iscomplete(self):
        _start_time = perf_counter()
        while True:
            if self.query('*OPC?')=='1':
                return True
            if perf_counter() - _start_time > 3:
                raise TimeoutError("Function did not return True within the timeout period.")
            time.sleep(0.01)


################################################################

# EXAMPLE
######        
# # -*- coding: utf-8 -*-
# """
# Created on Mon Jan 27 10:42:32 2025

# @author: user
# """

# from vslab._future_.YokogawaGS820 import GS820

# gs = GS820('gs', address='TCPIP0::192.168.1.18::INSTR')

# ch1 = gs.CHAN1
# ch2 = gs.CHAN2

# print(ch1.source_mode())
# ch1.source_mode('current')
# print(ch1.sense_mode())
# print(ch1.source_volt())
# print(ch1.source_curr())


# print(ch1.source_curr_range())
# print(ch1.sense_volt_range())

# ch1.sense_volt_range(2)

# print(ch1.volt_limit())

# ch1.output('on')
# # Tested with loop. Found no time out issue. 
# print(ch1.measure())

# # check the multi set commands in loop to see if deadlock occurs
# # AT some time

# # Possibly, it is working. The server does not show the red light indicator
# ch1.output('on')

# ch1.setTo(15e-3)

# ch1.source_range_auto('OFF')
# ch1.sweepTo(0)

# ch1.configVI()

    




