from typing import Any
from time import time, sleep
from qcodes import VisaInstrument, validators as vals


class SRS_SG396(VisaInstrument):
    """
    This is the code for SG396 RF Signal Generator
    Status: beta version
    Includes the essential commands from the manual
    """
    def __init__(self, name: str, address: str,
                 reset: bool = False, **kwargs: Any):
        super().__init__(name, address, terminator='\n', **kwargs)
    # signal synthesis commands
        
        self.add_function('reset', call_cmd='*RST;ENBR 0')
        
        self.add_parameter(name='frequency',
                           label='Frequency',
                           unit='Hz',
                           get_cmd='FREQ?',
                           set_cmd='FREQ {:.6f}',
                           get_parser=float,
                           vals=vals.Numbers(min_value=9.5e5,
                                             max_value=6.075e9))
        self.add_parameter(name='phase',
                           label='Carrier phase',
                           unit='deg',
                           get_cmd='PHAS?',
                           set_cmd='PHAS {:.1f}',
                           get_parser=float,
                           vals=vals.Numbers(min_value=-360, max_value=360))
        self.add_parameter(name='amplitude_LF',
                           label='Power of BNC output',
                           unit='dBm',
                           get_cmd='AMPL?',
                           set_cmd='AMPL {:.2f}',
                           get_parser=float,
                           vals=vals.Numbers(min_value=-47, max_value=13))
        self.add_parameter(name='amplitude_RF',
                           label='Power of type-N RF output',
                           unit='dBm',
                           get_cmd='AMPR?',
                           set_cmd='AMPR {:.2f}',
                           get_parser=float,
                           vals=vals.Numbers(min_value=-110, max_value=16.5))

        self.add_parameter(name='power',
                           label='Power of type-N RF output',
                           unit='dBm',
                           get_cmd='AMPR?',
                           set_cmd='AMPR {:.2f}',
                           get_parser=float,
                           vals=vals.Numbers(min_value=-110, max_value=16.5))

        self.add_parameter(name='amplitude_HF',
                           label='Power of RF doubler output',
                           unit='dBm',
                           get_cmd='AMPH?',
                           set_cmd='AMPH {:.2f}',
                           get_parser=float,
                           vals=vals.Numbers(min_value=-10, max_value=13))
        self.add_parameter(name='amplitude_clock',
                           label='Rear clock output',
                           unit='Vpp',
                           get_cmd='AMPC?',
                           set_cmd='AMPC {:.2f}',
                           get_parser=float,
                           vals=vals.Numbers(min_value=0.4, max_value=1.00))
        self.add_parameter(name='noise_mode',
                           label='RF PLL loop filter mode',
                           get_cmd='NOIS?',
                           set_cmd='NOIS {}',
                           val_mapping={'Mode 1': 0,
                                        'Mode 2': 1})
        self.add_parameter(name='enable_RF',
                           label='Type-N RF output',
                           get_cmd='ENBR?',
                           set_cmd='ENBR {}',
                           val_mapping={'OFF': 0,
                                        'ON': 1})
       

        # "output_RF" parameter is a duplicate of "enable_RF"

        # Reason to give another label: 
        #   1. output_RF("OFF") sounds more meaningful than enable_RF("OFF" when there is no output signal, and
        #      the same argument for output_RF("ON") and enable_RF("ON")

        # Reason to duplicate instead of changing forever: 
        #   2. Not to break the scripts based on earlier parameter naming. 

        self.add_parameter(name='output_RF',
                           label='Type-N RF output',
                           get_cmd='ENBR?',
                           set_cmd='ENBR {}',
                           val_mapping={'OFF': 0,
                                        'ON': 1})

        self.add_parameter(name='enable_LF',
                           label='BNC output',
                           get_cmd='ENBL?',
                           set_cmd='ENBL {}',
                           val_mapping={'OFF': 0,
                                        'ON': 1})

     
        # "output_LF" parameter is a duplicate of "enable_LF"

        # Reason to give another label: 
        #   1. output_LF("OFF") sounds more meaningful than enable_LF("OFF" when there is no output signal, and
        #      the same argument for output_LF("ON") and enable_LF("ON")

        # Reason to duplicate instead of changing forever: 
        #   2. Not to break the scripts based on earlier parameter naming. 

        self.add_parameter(name='output_LF',
                           label='BNC output',
                           get_cmd='ENBL?',
                           set_cmd='ENBL {}',
                           val_mapping={'OFF': 0,
                                        'ON': 1})


        self.add_parameter(name='enable_HF',
                           label='RF doubler output',
                           get_cmd='ENBH?',
                           set_cmd='ENBH {}',
                           val_mapping={'OFF': 0,
                                        'ON': 1})

        # "output_HF" parameter is a duplicate of "enable_HF"

        # Reason to give another label: 
        #   1. output_HF("OFF") sounds more meaningful than enable_HF("OFF" when there is no output signal, and
        #      the same argument for output_HF("ON") and enable_HF("ON")

        # Reason to duplicate instead of changing forever: 
        #   2. Not to break the scripts based on earlier parameter naming.

        self.add_parameter(name='output_HF',
                           label='RF doubler output',
                           get_cmd='ENBH?',
                           set_cmd='ENBH {}',
                           val_mapping={'OFF': 0,
                                        'ON': 1})
        self.add_parameter(name='status',
                           label='Type-N RF output status',
                           get_cmd='ENBR?',
                           set_cmd='ENBR {}',
                           val_mapping={False: 0,
                                        True: 1})

        self.add_parameter(name='enable_clock',
                           label='Rear clock output',
                           get_cmd='ENBC?',
                           set_cmd='ENBC {}',
                           val_mapping={'OFF': 0,
                                        'ON': 1})
        self.add_parameter(name='offset_clock',
                           label='Rear clock offset voltage',
                           unit='V',
                           get_cmd='OFSC?',
                           set_cmd='OFSC {}',
                           get_parser=float,
                           vals=vals.Numbers(min_value=-2, max_value=2))
        self.add_parameter(name='offset_rearDC',
                           label='Rear DC offset voltage',
                           unit='V',
                           get_cmd='OFSD?',
                           set_cmd='OFSD {}',
                           get_parser=float,
                           vals=vals.Numbers(min_value=-10, max_value=10))
        self.add_parameter(name='offset_bnc',
                           label='Low frequency BNC output',
                           unit='V',
                           get_cmd='OFSL?',
                           set_cmd='OFSL {}',
                           get_parser=float,
                           vals=vals.Numbers(min_value=-1.5, max_value=1.5))
    # Modulation commands
        self.add_parameter(name='modulation_coupling',
                           label='External modulation input coupling',
                           get_cmd='COUP?',
                           set_cmd='COUP {}',
                           val_mapping={'AC': 0,
                                        'DC': 1})
        self.add_parameter(name='FM_deviation',
                           label='Frequency modulation deviation',
                           unit='Hz',
                           get_cmd='FDEV?',
                           set_cmd='FDEV {:.1f}',
                           get_parser=float,
                           vals=vals.Numbers(min_value=0.1, max_value=5e5))
        self.add_parameter(name='modulation_function',
                           label='Modulation function for AM/FM/PhiM',
                           get_cmd='MFNC?',
                           set_cmd='MFNC {}',
                           val_mapping={'Sine': 0,
                                        'Ramp': 1,
                                        'Triangle': 2,
                                        'Square': 3,
                                        'Phase noise': 4,
                                        'External': 5})
        self.add_parameter(name='enable_modulation',
                           get_cmd='MODL?',
                           set_cmd='MODL {}',
                           val_mapping={'OFF': 0,
                                        'ON': 1})

        self.add_parameter(name='sweep_modulation_rate',
                           label='Modulation rate for frequency sweep',
                           get_cmd='SRAT?',
                           set_cmd='SRAT {:.6f}',
                           get_parser=float,
                           vals=vals.Numbers(min_value=1e-6, max_value=120))

        self.add_parameter(name='sweep_modulation_deviation',
                           label='Modulation deviation for frequency sweep',
                           get_cmd='SDEV?',
                           set_cmd='SDEV {:.6f}',
                           get_parser=float,
                           # 
                           vals=vals.Numbers(min_value=1e-1, max_value=6.15e9))

        self.add_parameter(name = 'pulse_modulation_function',
                           get_cmd = 'PFNC?',
                           set_cmd = 'PFNC {}',
                           val_mapping = {'Square': 3,
                                          'Noise': 4,
                                          'External': 5,
                                          'UserWaveform':11}
                           )
        
        self.add_parameter(name = 'IQ_modulation_function',
                           get_cmd = 'QFNC?',
                           set_cmd = 'QFNC {}',
                           val_mapping = {'Sin': 0,
                                          'Ramp': 1,
                                          'Triangle': 2,
                                          'Square': 3,
                                          'PhaseNoise': 4,
                                          'External': 5,
                                          'SineCosine': 6,
                                          'CosineSince': 7,
                                          'IQNoise': 8,
                                          'PRBSsymbols': 9,
                                          'Pattern': 10,
                                          'UserWaveform': 11}
                           )
        
        self.add_parameter(name='modulation_type',
                           label='Current modulation type',
                           get_cmd='TYPE?',
                           set_cmd='TYPE {}',
                           val_mapping={'AM': 0,
                                        'FM': 1,
                                        'Phi': 2,
                                        'Sweep': 3,
                                        'Pulse': 4,
                                        'Blank': 5,
                                        'IQ': 6,
                                        'QAM' : 7,
                                        'CPM' : 8,
                                        'VSB' : 9})

                                        
        self.connect_message()
        
    def setup_pulse_mod_ext(self):
        self.enable_modulation('ON')
        self.modulation_type('Pulse')
        self.pulse_modulation_function('External')
        pass
    
    def setup_IQ_mod_ext(self):
        self.enable_modulation('ON')
        self.modulation_type('IQ')
        self.IQ_modulation_function('External')
        pass

    # The reason of using smalls for 'lf/rf' instead of CAPS "LF/RF" -- 
    # enable_RF/LF("0/1") already exists in the driver parameters and the small letters 
    # was choosen to avoid any clash in the commands

    def disable_lf(self):
        self.output_LF('OFF')
        pass
        
    # The reason of using smalls for 'lf/rf' instead of CAPS "LF/RF" -- 
    # enable_RF/LF("0/1") already exists in the driver parameters and the small letters 
    # was choosen to avoid any clash in the commands

    def enable_lf(self):
        self.output_LF('ON')
        pass

    # The reason of using smalls for 'lf/rf' instead of CAPS "LF/RF" -- 
    # enable_RF/LF("0/1") already exists in the driver parameters and the small letters 
    # was choosen to avoid any clash in the commands

    def disable_rf(self):
        self.output_RF('OFF')
        pass

    # The reason of using smalls for 'lf/rf' instead of CAPS "LF/RF" -- 
    # enable_RF/LF("0/1") already exists in the driver parameters and the small letters 
    # was choosen to avoid any clash in the commands

    def enable_rf(self):
        self.output_RF('ON')
        pass

    def disable_MOD(self):
        self.enable_modulation('OFF')
        pass

    def enable_MOD(self):
        self.enable_modulation('ON')
        pass

    def frequency_sweep(self, start, end, sweeps_per_second, power):

        """ Performs the frequency sweep. 

        The parameters that should be defined for the sweep are: center frequency and the freq-deviation, 
        using which the start_freq and the stop_freq is defined, as follows. 

        start_freq = center_freq - freq_deviation
        stop_freq = center_freq + freq_deviation

        The default system sweeps works as below: 
        center_freq --> stop_freq --> center_freq --> start_freq --> center_freq
        
        HOWEVER, the requirement is only to sweep from frequency A (start) to frequency B (stop)

        To implement that, in the funciton frequency_sweep, the "required period of the sweep = total_period_of_sweep/4"

        parameters: 
        start =  starting frequency (centre_freq)
        end = stop frequency (stop_freq = center_freq + freq_deviation)
        sweeps_per_second = defines the sweep rate
        power = input power of the signal 

        Returns: None 

        Note: The sweep is continuous and not discrete. 
        """

        # change the max allowed power
        if power >= -30:
            print('Power is too high. Try with lesser power')
            return None

        # disable all the output signals and modulation
        self.disable_lf()
        self.disable_rf()
        self.disable_MOD()

        # set starting frequency of the sweep
        start_freq = self.frequency(start)

        if end<start:
            print('"End" freq should be higher than the "start" freq')
            return None

        # calculate the deviation frequency based on the starting and ending frequency
        deviation_freq = (end - start)

        # set modulation type to Sweep and modulation function to be ramp
        # look at the instrument manual to know more about all the accepted modulation fucntions
        self.modulation_type('Sweep')
        self.modulation_function('Ramp')
        self.sweep_modulation_rate(sweeps_per_second)
        self.sweep_modulation_deviation(deviation_freq)
        self.amplitude_RF(power)

        
        time_start = time()

        # Enable modulaiton
        self.enable_MOD()
        # Enable RF signal
        self.enable_rf()

        while time()-time_start<= float(1/(4*sweeps_per_second)):
            self.enable_MOD()
            self.enable_rf()
        self.disable_MOD()
        self.disable_rf ()

        pass







    # def run_auto_calibration(self):
    #     self.


            
            
            
            
            
            
            
            
