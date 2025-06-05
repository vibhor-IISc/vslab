# -*- coding: utf-8 -*-
"""
Created on Sun Jun 27 12:28:40 2021

@author: Vibhor
"""


import numpy as np
from time import sleep, time
from os.path import isfile
from typing import Any
import progressbar


from vslab.constants import *
# from vslab.rack import *
from vslab.awg_strings import AWG_Strings

close_all_instruments()

#from qcodes.instrument_drivers.stanford_research.SG396 import SRS_SG396
from qcodes.instrument_drivers.rohde_schwarz.SGS100A import RohdeSchwarz_SGS100A
# from qcodes.instrument_drivers.rohde_schwarz.FSV13_2 import FSV13_2
from vslab.instrument_drivers.ZVL_SA import ZVL_SA
from vslab.instrument_drivers.APSYN420 import APSYN420
LO = APSYN420('aps', APSYN_ADDRESS)

# LO = SRS_SG396('LO', address = SG1_ADDRESS)
#LO = RohdeSchwarz_SGS100A('LO', 'TCPIP0::169.254.2.20::inst0::INSTR')

sa = ZVL_SA('sa', address = ZVL_ADDRESS)
# sg = SRS_SG396('sg', address = SG2_ADDRESS)


# sa = FSV13_2('sa', address = FSV_ADDRESS)

from zhinst.qcodes import UHFLI
from zhinst.utils import create_api_session, api_server_version_check
(daq_uhf, device_uhf, _) = create_api_session(UHF_ADDRESS, 6)
api_server_version_check(daq_uhf)

awg_uhf = daq_uhf.awgModule()
awg_uhf.set("device", device_uhf)
awg_uhf.execute()

sweeper = daq_uhf.sweep()
sweeper.set("device", device_uhf)

daq_uhf.sync()
daq = daq_uhf.dataAcquisitionModule()



readout_seqc_trig_on = AWG_Strings.readout_pulse_with_trig
readout_seqc_trig_off = AWG_Strings.readout_pulse_without_trig


class Readout(UHFLI):
    def __init__(self, address: str, host,
                 reset: bool = False, **kwargs: Any):
        super().__init__(address, host, **kwargs)

        self.frequency = 6.0*GHz
        self.sideband = 'left'
        self.mix_freq = 56.25*MHz
        self.awg_sin_amp = 0.1

        # daq_uhf.setInt(f'/{device_uhf}/system/preset/load', 1)
        
        daq_uhf.setInt(f"/{device_uhf}/system/extclk", 1)

        daq_uhf.setInt(f'/{device_uhf}/demods/0/enable', 0); 
        daq_uhf.setInt(f'/{device_uhf}/demods/4/enable', 0);
        daq_uhf.setInt(f'/{device_uhf}/sigins/0/ac', 1)
        daq_uhf.setInt(f'/{device_uhf}/sigins/0/imp50', 1)

    
    def LO_freq(self):
        if self.sideband == 'left':
            LO_freq = self.frequency + self.mix_freq
        elif self.sideband == 'right':
            LO_freq = self.frequency - self.mix_freq
        else:
            print('Unclear sideband')
        return LO_freq
    
    def mlist(self):
        return [self.LO_freq()-self.mix_freq, self.LO_freq(), self.LO_freq()+self.mix_freq]
    
    def _uhf_initial_setup(self):
        IF = self.mix_freq
        # SET UHF to external 10 MHzs
        self.system.extclk(1)
        # setting all oscillators to common frequency
        self.oscs.oscs0.freq(IF)
        self.oscs.oscs1.freq(IF)
        self.oscs.oscs2.freq(IF)
        self.oscs.oscs3.freq(IF)
        self.oscs.oscs4.freq(IF)
        self.oscs.oscs5.freq(IF)
        self.oscs.oscs6.freq(IF)
        self.oscs.oscs7.freq(IF)
        # Linking Demods to Osc
        self.demods.demods0.oscselect(0)
        self.demods.demods1.oscselect(1)
        self.demods.demods2.oscselect(2)
        self.demods.demods3.oscselect(3)
        self.demods.demods4.oscselect(4)
        self.demods.demods5.oscselect(5)
        self.demods.demods6.oscselect(6)
        # special command for SSB
        # to set 8th Demod to 4th Osc
        self.demods.demods7.oscselect(3)
        pass


    def modulation_phase_shift(self, phase):
        self.demods.demods7.phaseshift(phase)
        pass

    def sin1_amplitudes1(opt_q):
        daq_uhf.setDouble("/dev2232/sigouts/0/amplitudes/3",opt_q)
        # q_ch.amplitudes7(opt_q)
        pass
    
    def _LO_setup(self):
        # check if 10 MHz is needed.
        LO.frequency(self.LO_freq())
        LO.power(13.5)
        LO.status(True)
        pass

    def signal_generator_enable(self):
        sg.enable_RF('ON')

    def signal_generator_disable(self):
        sg.enable_RF('OFF')

##########  Potential issue in sideband_diff

    def _sideband_diff(self):
        sa.sweep_single()
        left, _ , right = sa.markers_read_Y()
        if self.sideband=='left':
            dif = left-right
        elif self.sideband=='right':
            dif = right-left
        else:
            raise Exception("Use sideband = left or right")
        return dif

    def _get_power(self):
        sa.sweep_single()
        return sa.markers_read_Y()[0]
    
    def _sa_setup(self, setup):
        if setup == 1:
            sa.center_frequency(self.LO_freq())
            sa.span(200*kHz)
            sa.bandwidth(10*kHz)
            sa.sweep_points(201)
            sa.reference_level(-10)
            sleep(1)
            sa.markers_off()
            sa.sweep_single()
            sa.markers_add_at([self.LO_freq()])
            pass
        elif setup == 2:
            sa.center_frequency(self.LO_freq())
            sa.span(2*self.mix_freq+5e6)
            sa.bandwidth(30*kHz)
            sa.sweep_points(4001)
            sa.sweep_count(1)
            sa.reference_level(-10)
            sa.markers_off()
            sa.sweep_single()
            sa.markers_add_at(self.mlist())
            pass
    
    
    def _uhf_awg_upload_compile_execute(self, src_string):
        awg_uhf.set("compiler/sourcestring", src_string)
        while awg_uhf.getInt("compiler/status") == -1:
            sleep(0.1)
        if awg_uhf.getInt("compiler/status") == 1:
            raise Exception(awg_uhf.getString("compiler/statusstring"))
        if awg_uhf.getInt("compiler/status") == 0:
            pass
        if awg_uhf.getInt("compiler/status") == 2:
            print("Compilation successful with warnings, will upload the program to the instrument.")
            print("Compiler warning: ", awg_uhf.getString("compiler/statusstring"))
    
        # Wait for the waveform upload to finish
        sleep(0.2)
        i = 0
        while (awg_uhf.getDouble("progress") < 1.0) and (awg_uhf.getInt("elf/status") != 1):
            # print(f"{i} progress: {awg_uhf.getDouble('progress'):.2f}")
            sleep(0.5)
            i += 1
        # print(f"{i} progress: {awg_uhf.getDouble('progress'):.2f}")
        if awg_uhf.getInt("elf/status") == 0:
            #print("Upload to the instrument successful.")
            pass
        if awg_uhf.getInt("elf/status") == 1:
            raise Exception("Upload to the instrument failed.")
        
        daq_uhf.setInt(f"/{device_uhf}/awgs/0/single", 1)
        daq_uhf.setInt(f"/{device_uhf}/awgs/0/enable", 1)
        daq_uhf.sync()
        pass
    
   
    def _awg_uhf_setup(self, setup):
        if daq_uhf.getInt(f"/{device_uhf}/awgs/0/enable")==1:
                daq_uhf.setInt(f"/{device_uhf}/awgs/0/enable", 0)
                pass
        if setup == 1:
            '''
            LO minimization
            '''
            daq_uhf.setInt(f"/{device_uhf}/sigins/0/ac", 1)
            daq_uhf.setInt(f"/{device_uhf}/sigouts/0/imp50", 1)
            daq_uhf.setInt(f"/{device_uhf}/sigouts/1/imp50", 1)

            daq_uhf.setDouble(f"/{device_uhf}/sigouts/0/offset", 0.0)
            daq_uhf.setDouble(f"/{device_uhf}/sigouts/1/offset", 0.0)

            # i_ch.enables3(0)
            daq_uhf.setInt(f"/{device_uhf}/sigouts/0/enables/3", 0)
            # q_ch.enables7(0)
            daq_uhf.setInt(f"/{device_uhf}/sigouts/1/enables/7", 0)

            daq_uhf.setInt(f"/{device_uhf}/sigouts/1/on", 1)
            daq_uhf.setInt(f"/{device_uhf}/sigouts/0/on", 1)

            pass
    
        elif setup == 2:
            ''' Phase optimization
            '''
            daq_uhf.setDouble(f"/{device_uhf}/sigouts/0/amplitudes/3", self.awg_sin_amp)
            # daq_uhf.setDouble("/dev2232/awgs/0/outputs/0/amplitude",0.1)
            # i_ch.amplitudes3(awg_sin_amp)
            daq_uhf.setDouble(f"/{device_uhf}/sigouts/1/amplitudes/7", self.awg_sin_amp)
            # daq_uhf.setDouble("/dev2232/awgs/0/outputs/1/amplitude",0.1)
            # q_ch.amplitudes7(awg_sin_amp)
            
            daq_uhf.setInt(f"/{device_uhf}/sigins/0/ac", 1)
            daq_uhf.setInt(f"/{device_uhf}/sigouts/0/imp50", 1)
            daq_uhf.setInt(f"/{device_uhf}/sigouts/1/imp50", 1)

            daq_uhf.setInt(f"/{device_uhf}/sigouts/0/enables/3", 1)
            # i_ch.enables3(1)
            daq_uhf.setInt(f"/{device_uhf}/sigouts/1/enables/7", 1)

            daq_uhf.setInt(f"/{device_uhf}/sigouts/1/on", 1)
            daq_uhf.setInt(f"/{device_uhf}/sigouts/0/on", 1)
            
            # q_ch.enables7(1)
            # _awg_prep_code(np.pi/2)
            pass
        
        elif setup == 3:
            ''' amplitude optimization
            '''
            daq_uhf.setDouble(f"/{device_uhf}/sigouts/0/amplitudes/3", self.awg_sin_amp)
            # daq_uhf.setDouble("/dev2232/awgs/0/outputs/0/amplitude",awg_sin_amp)
            # i_ch.amplitudes3(awg_sin_amp)
            daq_uhf.setDouble(f"/{device_uhf}/sigouts/1/amplitudes/7", self.awg_sin_amp)
            # daq_uhf.setDouble("/dev2232/awgs/0/outputs/1/amplitude",awg_sin_amp)
            # q_ch.amplitudes7(awg_sin_amp)
            # i_ch.on(1)
            # q_ch.on(1)
            daq_uhf.setInt(f"/{device_uhf}/sigins/0/ac", 1)

            daq_uhf.setInt(f"/{device_uhf}/sigouts/0/imp50", 1)
            daq_uhf.setInt(f"/{device_uhf}/sigouts/1/imp50", 1)

            daq_uhf.setInt(f"/{device_uhf}/sigouts/0/on", 1)
            daq_uhf.setInt(f"/{device_uhf}/sigouts/1/on", 1)
            pass
        else:
            pass
        
    
    def _dc_sweep(self, i_arr, q_arr, plot = False):
        progress_bar = progressbar.ProgressBar(maxval=len(i_arr), \
            widgets=['\rOptimizing DC Offsets: ', progressbar.Bar('.', '', ''), ' ', progressbar.Percentage(), ' (', progressbar.ETA(), ') '])
        progress_bar.start()
        pow_arr = []
        for index, i in enumerate(i_arr):
            # i_ch.offset(i)
            daq_uhf.setDouble(f"/{device_uhf}/sigouts/0/offset", i)
            pow_arr.append([])
            progress_bar.update(index+1)
            for q in q_arr:
                # q_ch.offset(q)
                daq_uhf.setDouble(f"/{device_uhf}/sigouts/1/offset", q)
                pow_arr[-1].append(self._get_power())
        progress_bar.finish()
        pow_arr = np.array(pow_arr)
        indices = np.where(pow_arr == pow_arr.min())
        # i_ch.offset(i_arr[indices[0][0]])
        daq_uhf.setDouble(f"/{device_uhf}/sigouts/0/offset", i_arr[indices[0][0]])
        # q_ch.offset(q_arr[indices[1][0]])
        daq_uhf.setDouble(f"/{device_uhf}/sigouts/1/offset", q_arr[indices[1][0]])
                          
        if plot:
            plt.imshow(pow_arr, aspect='auto', extent=[q_arr[0]*1e3, q_arr[-1]*1e3, i_arr[-1]*1e3, i_arr[-0]*1e3])
            plt.colorbar()
            plt.ylabel('I values (mV)')
            plt.xlabel('Q values (mV)')
            plt.show(block = False)
            # plt.savefig()
        return i_arr[indices[0][0]],q_arr[indices[1][0]]


    def optimize_dc(self, plot = False):
        # ADD a save to file
        self._sa_setup(1)
        self._LO_setup()
        self._awg_uhf_setup(1)

        file_path = r'C:\Users\normaluser\miniconda3\envs\qcodes\Lib\site-packages\vslab\Readout_IQ.txt'
        if isfile(file_path):
            with open(file_path, "r") as file:
                lastline = file.readlines()[-1].split('\t')
                lastline = list(map(float, lastline))
            file.close()
            i_guess = opt_i = float(lastline[0])
            q_guess = opt_q = float(lastline[1])

        else:
            i_guess = opt_i = 3*1e-3
            q_guess = opt_q = -10.5*1e-3


        # Coarse sweep
        #
        # Fine sweep
        i_arr = np.linspace(opt_i-70e-3, opt_i+100e-3, 21)
        q_arr = np.linspace(opt_q-70e-3, opt_q+50e-3, 21)
        opt_i, opt_q = self._dc_sweep(i_arr, q_arr, plot)
        # print(f'fine i = {opt_i} and q = {opt_q}')
        # Finer sweep
        i_arr = np.linspace(opt_i-10.*1e-3, opt_i+10.*1e-3, 51)
        q_arr = np.linspace(opt_q-10.*1e-3, opt_q+10.*1e-3, 51)
        opt_i, opt_q = self._dc_sweep(i_arr, q_arr, plot)
        # print(f'finer i = {opt_i} and q = {opt_q}')
        sa.sweep_cont()
        # i_ch.offset(opt_i)
        daq_uhf.setDouble(f"/{device_uhf}/sigouts/0/offset", opt_i)
        # q_ch.offset(opt_q)
        daq_uhf.setDouble(f"/{device_uhf}/sigouts/1/offset", opt_q)

        save = True
        if save:
            with open(file_path, "a") as iqfile:
                iqfile.write('\n'+str(opt_i)+'\t'+str(opt_q))
        iqfile.close()

        return opt_i, opt_q
        
    def _optimize_ph(self, ph_arr, plot = False):
        diffs = []
        progress_bar = progressbar.ProgressBar(maxval=len(ph_arr), \
            widgets=['\rOptimizing Phase ', progressbar.Bar('.', '', ''), ' ', progressbar.Percentage(), ' (', progressbar.ETA(), ') '])
        progress_bar.start()
        for index, phase in enumerate(ph_arr):
            self.modulation_phase_shift(phase)
            sa.sweep_single()
            diffs.append(self._sideband_diff())
            progress_bar.update(index+1)
        progress_bar.finish()
        diffs = np.array(diffs)

        ph_opt = ph_arr[np.argmax(diffs)]

        print('For optimize phase:\ndiffs =', diffs, '\nph_opt =', ph_opt) #remove this later

        self.modulation_phase_shift(ph_opt)
        if plot:
            plt.plot(ph_arr, diffs, '-ro')
            plt.title('Phase calibration result')
            plt.xlabel('Phase difference (degree)')
            plt.ylabel('Sideband Difference (dB)')
            plt.show()
        return ph_opt
    
    def optimize_phase(self, plot=False):
        self._sa_setup(2)
        self._awg_uhf_setup(2)
        if self.sideband == 'left':
            ph_arr = np.linspace(-150, -70, 41)
        elif self.sideband == 'right':
            ph_arr = np.linspace(150, 100, 41)
        else:
            raise Exception('Use sideband = left or right')
        # Coarse sweep
        opt_ph = self._optimize_ph(ph_arr, plot)
        # Fine sweep
        ph_arr = np.linspace(opt_ph - 2., opt_ph + 2., 41)
        opt_ph = self._optimize_ph(ph_arr, plot)
        # Finer sweep
        ph_arr = np.linspace(opt_ph - 0.1, opt_ph + 0.1, 21)
        opt_ph = self._optimize_ph(ph_arr, plot)
        self.modulation_phase_shift(opt_ph)

        sa.sweep_cont()
        
        # Writing to a file
        file_path = r'C:\Users\normaluser\miniconda3\envs\qcodes\Lib\site-packages\vslab\Readout_phase.txt'
        save = True
        if save:
            with open(file_path, "a") as ph_file:
                ph_file.write('\n'+str(opt_ph))
        ph_file.close()
        
        return opt_ph
    
    def _optimize_amp(self, q_arr, plot=False):
        diffs = []
        import progressbar
        progress_bar = progressbar.ProgressBar(maxval=len(q_arr), \
            widgets=['\rOptimizing Amplitude', progressbar.Bar('.', '', ''), ' ', progressbar.Percentage(), ' (', progressbar.ETA(), ') '])
        progress_bar.start()
        for index, q in enumerate(q_arr):
            # sin1_amplitudes1(q)
            daq_uhf.setDouble(f"/{device_uhf}/sigouts/0/amplitudes/3",q)
            diffs.append(self._sideband_diff())
            progress_bar.update(index+1)
        progress_bar.finish()
    
        diffs = np.array(diffs)
        if plot:
            plt.plot(q_arr, diffs, '-ro')
            plt.title('Ampltude calibration result')
            plt.xlabel('Amplitude imbalance')
            plt.ylabel('Sideband Difference (dB)')
            plt.show()
        opt_q = q_arr[np.argmax(diffs)]
        return opt_q

    def optimize_amplitude(self, plot=False):
        self._sa_setup(2)
        self._awg_uhf_setup(3)
        q_arr = np.linspace(self.awg_sin_amp-0.05, self.awg_sin_amp+0.05,41)
        opt_q = self._optimize_amp(q_arr, plot)
        
        # sin1_amplitudes1(opt_q)
        daq_uhf.setDouble(f"/{device_uhf}/sigouts/0/amplitudes/3",opt_q)
        
        # Fine sweep
        q_arr = np.linspace(opt_q-0.01, opt_q+0.01, 41)
        opt_q = self._optimize_amp(q_arr, plot)
        # sin1_amplitudes1(opt_q)
        daq_uhf.setDouble(f"/{device_uhf}/sigouts/0/amplitudes/3",opt_q)
        
        # Finer sweep
        q_arr = np.linspace(opt_q-0.005, opt_q+0.005, 41)
        opt_q = self._optimize_amp(q_arr, plot)
        # sin1_amplitudes1(opt_q)
        daq_uhf.setDouble(f"/{device_uhf}/sigouts/0/amplitudes/3",opt_q)
        sa.sweep_cont()
        return opt_q
    
    def optimize_all(self, plot= not False):
        self._uhf_initial_setup()        
        self.optimize_dc(plot)
        ph_op = self.optimize_phase(plot)
        self.optimize_amplitude(plot)
        daq_uhf.sync()
        return ph_op

    def post_calibration_ready(self):
        amp1 = daq_uhf.getDouble(f"/{device_uhf}/sigouts/0/amplitudes/3")
        amp1 = daq_uhf.getDouble(f"/{device_uhf}/sigouts/1/amplitudes/7")


    def readout_mode_cw(self, tc = 300e-3):
        daq_uhf.setInt(f"/{device_uhf}/awgs/0/enable", 0)
        daq_uhf.setInt(f"/{device_uhf}/sigouts/0/enables/3", 1)
        daq_uhf.setInt(f"/{device_uhf}/sigouts/1/enables/7", 1)
        daq_uhf.setInt(f"/{device_uhf}/demods/0/enable", 1)
        daq_uhf.setInt(f"/{device_uhf}/demods/0/rate", 13)

        self.time_constant_and_order(tc, order=1)

    
    def readout_mode_pulse(self, trig = True, tc = 300e-9, aux_gain = 200):
        # Disabling the Data transfer

        daq_uhf.setInt(f"/{device_uhf}/demods/0/enable", 0)
        mod_amp_1 = daq_uhf.getDouble(f"/{device_uhf}/sigouts/0/amplitudes/3")
        mod_amp_2 = daq_uhf.getDouble(f"/{device_uhf}/sigouts/1/amplitudes/7")

        daq_uhf.setDouble(f"/{device_uhf}/awgs/0/outputs/0/amplitude", mod_amp_1)
        daq_uhf.setDouble(f"/{device_uhf}/awgs/0/outputs/1/amplitude", mod_amp_2)
        
        daq_uhf.setInt(f"/{device_uhf}/awgs/0/outputs/0/mode", 1)
        daq_uhf.setInt(f"/{device_uhf}/awgs/0/outputs/1/mode", 1)
        
        # Writing the READOUT AWG code

        awg_running = daq_uhf.getInt(f"/{device_uhf}/awgs/0/enable")
        if awg_running:
            daq_uhf.setInt(f"/{device_uhf}/awgs/0/enable", 0)
            if (trig==True):
                self._uhf_awg_upload_compile_execute(readout_seqc_trig_on)
            else:
                self._uhf_awg_upload_compile_execute(readout_seqc_trig_off)

            daq_uhf.setInt(f"/{device_uhf}/awgs/0/enable", 1)
        else:
            daq_uhf.setInt(f"/{device_uhf}/awgs/0/enable", 1)
            pass

        # Setting up the DIGITAL Triggers for listening-to-HDAWG
        daq_uhf.setInt(f"/{device_uhf}/triggers/out/0/source", 32)
        daq_uhf.setInt(f"/{device_uhf}/triggers/out/0/drive", 0)

        # Setting up the DIGITAL Triggers for oscilloscope
        daq_uhf.setInt(f"/{device_uhf}/triggers/out/1/source", 33)
        daq_uhf.setInt(f"/{device_uhf}/triggers/out/1/drive", 1)

        daq_uhf.setInt(f"/{device_uhf}/awgs/0/auxtriggers/0/channel", 0)
        daq_uhf.setInt(f"/{device_uhf}/awgs/0/auxtriggers/0/slope", 1)

        # setting the level of Input trigger level to 50 mV

        daq_uhf.setDouble(f"/{device_uhf}/triggers/in/0/level", 0.05)

        self.time_constant_and_order(tc, order=1)
        self.input_range(50e-3)
        self.pregain(100)
        self.config_aux_for_scope(aux_gain)

        pass

    def osc_amp(self, value):
        mod_amp_1 = daq_uhf.getDouble(f"/{device_uhf}/sigouts/0/amplitudes/3")
        mod_amp_2 = daq_uhf.getDouble(f"/{device_uhf}/sigouts/1/amplitudes/7")
        ratio_iq = mod_amp_1 / mod_amp_2
        daq_uhf.setDouble(f"/{device_uhf}/sigouts/0/amplitudes/3", value*ratio_iq)
        daq_uhf.setDouble(f"/{device_uhf}/sigouts/1/amplitudes/7", value)
        
        # Updating the AWG modulation amplitudes 
        daq_uhf.setDouble(f"/{device_uhf}/awgs/0/outputs/0/amplitude", value*ratio_iq)
        daq_uhf.setDouble(f"/{device_uhf}/awgs/0/outputs/1/amplitude", value)



        pass
    
    def osc_freq(self, value):
        daq_uhf.setDouble(f"/{device_uhf}/oscs/3/freq", value)
        # daq_uhf.setDouble(f"/{device_uhf}/oscs/7/freq", value)
        pass

    def input_range(self, value=0.1):
        daq_uhf.setDouble(f"/{device_uhf}/sigins/0/range", value)

    def time_constant_and_order(self, value=300e-9, order=1):
        daq_uhf.setDouble(f"/{device_uhf}/demods/0/timeconstant", value)
        daq_uhf.setDouble(f"/{device_uhf}/demods/0/order", order)
        pass

    def config_aux_for_scope(self, gain=2000):
        # setting Demod X to channel -2
        daq_uhf.setInt(f'/{device_uhf}/auxouts/1/demodselect', 0)
        daq_uhf.setInt(f'/{device_uhf}/auxouts/1/outputselect', 0)

        # setting Demod Y to channel -4
        daq_uhf.setInt(f'/{device_uhf}/auxouts/3/demodselect', 0)
        daq_uhf.setInt(f'/{device_uhf}/auxouts/3/outputselect', 1)

        # setting up the gain
        daq_uhf.setDouble(f'/{device_uhf}/auxouts/1/scale', gain)
        daq_uhf.setDouble(f'/{device_uhf}/auxouts/3/scale', gain)
        pass

        
    def pregain(self, value=50):
        daq_uhf.setDouble(f"/{device_uhf}/sigins/0/scaling", value)
        pass

    def S21_sweep(self, start_fc, stop_fc, npts, filter_order, reverse = False ):
        daq_uhf.setInt(f'/{device_uhf}/sigins/0/ac', 1)
        daq_uhf.setInt(f'/{device_uhf}/sigins/0/imp50', 1)
        self.input_range(100*1e-3)
        self.pregain(20)
        
        # start = np.abs(self.LO_freq() - start_fc)
        # stop = np.abs(self.LO_freq() - stop_fc)
        start = np.abs(start_fc)
        stop = np.abs(stop_fc)

        print(start*1e-9, stop*1e-9)

        sweeper.set("gridnode", "oscs/3/freq")
        sweeper.set("start", min(start,stop))
        sweeper.set("stop", max(start,stop))
        sweeper.set("samplecount", npts)
        sweeper.set("xmapping", 0)
        
        if reverse == True:
            if self.sideband == 'left':
                sweeper.set("scan", 3)
            elif self.sideband == 'right':
                sweeper.set("scan", 0)
        elif reverse == False:

            if self.sideband == 'left':
                sweeper.set("scan", 0)
            elif self.sideband == 'right':
                sweeper.set("scan", 3)


        sweeper.set("loopcount", 1)
        daq_uhf.setInt(f'/{device_uhf}/demods/3/enable', 1)
        ################################################
        # Speed Needs to be optimized
        
        # sweeper.set("bandwidthcontrol", 0)
        # sweeper.set("settling/time", 0.001)
        # sweeper.set("settling/inaccuracy", 0.001)
        # sweeper.set("averaging/tc", 5)
        # sweeper.set("averaging/sample", 10)
        # sweeper.set("averaging/time", 0.001)
        sweeper.set("order", filter_order)
        # sweeper.set("averaging/time", 0.1)
        # sweeper.set("maxbandwidth", 1000)
        sweeper.set("omegasuppression",60)
        # daq_uhf.setDouble("/dev2232/demods/3/timeconstant", 0.001)
        ###############################################
        sweeper.subscribe(f'/{device_uhf}/demods/3/sample')
        flat_dictionary_key = True
        sweeper.execute()
        start_t = time()
        while True:
            test = sweeper.finished()
            # print(test)
            if test:
                data = sweeper.read(True)
                x = data[f'/{device_uhf}/demods/3/sample'][0][0]['x']
                y = data[f'/{device_uhf}/demods/3/sample'][0][0]['y']
                stop_t = time()
                print(f'Time taken:  {stop_t-start_t} sec')
                sweeper.unsubscribe("*")
                return x+1j*y
                break
            else:
                # print('waiting ...')
                sleep(1)
                

    def S21_single_point(self, tc=100e-3):
        # osc_freq = np.abs(self.LO_freq() - freq_c)
        # osc_freq = freq_c
        # self.osc_freq(osc_freq)
        self.time_constant_and_order(tc,1)
        daq_uhf.setDouble(f'/{device_uhf}/demods/0/rate', 6)
        daq_uhf.setInt(f'/{device_uhf}/demods/0/enable', 1)
        start_t = time()
        daq_uhf.subscribe(f'/{device_uhf}/demods/0/sample')
        sleep_length = 2*tc
        sleep(sleep_length)
        poll_length = 2*tc 
        poll_timeout = 2000  # [ms]
        poll_flags = 0
        poll_return_flat_dict = True
        data = daq_uhf.poll(poll_length, poll_timeout, poll_flags, poll_return_flat_dict)
        daq_uhf.unsubscribe("*")
        stop_t = time()
        print(stop_t - start_t)
        
        x = data['/dev2232/demods/0/sample']['x']
        y = data['/dev2232/demods/0/sample']['y']
        return np.mean(x) + 1j*np.mean(y), np.abs(np.mean(x) + 1j*np.mean(y))
        

    def S21_pulse(self, tc = 300*ns, n_rows = 1, avg = 10, duration = 5*1e-6, npts=10):
        # input settings
        self.input_range(100*1e-3)
        daq_uhf.setInt(f'/{device_uhf}/sigins/0/imp50', 1)
        daq_uhf.setInt(f'/{device_uhf}/sigins/0/ac', 1)
        self.pregain(50)
        
        # Settings demods
        daq_uhf.setInt(f'/{device_uhf}/demods/3/order', 2)
        daq_uhf.setDouble(f'/{device_uhf}/demods/3/timeconstant', tc)
        daq_uhf.setInt(f'/{device_uhf}/demods/3/trigger', 33554432) # AWG Trig2 High
        daq_uhf.setDouble(f'/{device_uhf}/demods/3/rate', 14*MHz)
        daq_uhf.setInt(f'/{device_uhf}/demods/3/enable', 1)
        
        # DAQ settings
        # daq.signals_clear()
        daq.set('triggernode', '/dev2232/demods/3/sample.TrigAWGTrig2')
        daq.set('clearhistory',1)
        daq.set('edge',0)
        daq.set('holdoff/time', 1e-6)
        daq.set('delay', 0)
        
        # DAQ grid settings
        daq.set('grid/mode', 2) # linear
        daq.set('grid/cols', npts)
        daq.set('grid/rows', n_rows)
        daq.set('duration', 5e-6)
        daq.set('grid/rowrepetition',1)
        daq.set('grid/direction', 0)
        
        pass

    def two_tone(self, freq_deviation, power, freq_points):
        sg.enable_LF('OFF')
        sg.enable_RF('OFF')
        sg.enable_modulation('OFF')
        sg.amplitude_RF(-80)
        sg.enable_RF('ON')
        ms = 1e-3

        # start = time()

        start = self.frequency - freq_deviation*MHz
        stop = self.frequency + freq_deviation*MHz

        # freq_points = 1001
        freq_list = np.linspace(start, stop, freq_points)

        
        # print((time()-start))#/2000)
     
        daq_uhf.setInt(f'/{device_uhf}/sigins/0/ac', 1)
        daq_uhf.setInt(f'/{device_uhf}/sigins/0/imp50', 1)
        
        osc_freq = self.mix_freq
        self.osc_freq(osc_freq)

        daq_uhf.setDouble(f'/{device_uhf}/demods/3/rate', 1e3)
        daq_uhf.setInt(f'/{device_uhf}/demods/3/enable', 1)

        
        daq_uhf.subscribe(f'/{device_uhf}/demods/3/sample')
        sleep_length = 0.4
        sleep(sleep_length)
        poll_length = 10*ms # [s]
        poll_timeout = 100  # [ms]
        poll_flags = 0
        poll_return_flat_dict = True

        
        x_list = []
        y_list = []

        
        start_t = time()
        count = 0
        for i in (freq_list):
            if count==500:
                sg.amplitude_RF(-25)
                # print('xxx')
            else:
                sg.amplitude_RF(-50)


            count = count+1

            sg.frequency(i) 
            sleep(10*ms)

            data = daq_uhf.poll(poll_length, poll_timeout, poll_flags, poll_return_flat_dict)

            y_list = y_list + list(data['/dev2232/demods/3/sample']['y'])
            x_list = x_list + list(data['/dev2232/demods/3/sample']['x'])

            # array_size = 
            
        daq_uhf.unsubscribe("*")
        stop_t = time()
        print(stop_t - start_t)
        

        out = np.abs(np.array(x_list) + 1j*np.array(y_list))

        np.savetxt('two_tone.txt', out)
        
        
        pass 


##############################################################################################################

#   Control

##############################################################################################################


# (daq_hdawg, device_hdawg, _) = create_api_session(HDAWG_ADDRESS, 6)
# api_server_version_check(daq_hdawg)

# from zhinst.qcodes import HDAWG
# from qcodes.instrument_drivers.stanford_research.SG396 import SRS_SG396


# sg1 = SRS_SG396('sg1', SG2_ADDRESS) # Mixure LO for drive signal
# sg1.enable_RF('ON') 



# class Control(HDAWG):
#     def __init__(self, address: str, host,
#                  reset: bool = False, **kwargs: Any):
#         super().__init__(address, host, **kwargs)

#         self.frequency = 5.0*GHz
#         self.power = 9 #dBm
#         self.sideband = 'left'
#         self.mix_freq = 75*MHz
#         self.awg_sin_amp = 0.1
#         self.awg_gain = 0.5
        
#         daq_hdawg.setInt(f"/{device_hdawg}/system/clocks/referenceclock/source", 1)
#         daq_hdawg.setInt(f"/{device_hdawg}/sigouts/0/filter", 1)
#         daq_hdawg.setInt(f"/{device_hdawg}/sigouts/1/filter", 1)
#         daq_hdawg.setInt(f"/{device_hdawg}/sigouts/0/direct", 1)
#         daq_hdawg.setInt(f"/{device_hdawg}/sigouts/1/direct", 1)
              
    
#     def LO_freq(self):
#         if self.sideband == 'left':
#             LO_freq = self.frequency + self.mix_freq
#         elif self.sideband == 'right':
#             LO_freq = self.frequency - self.mix_freq
#         else:
#             print('Unclear sideband')
#         return LO_freq
    
#     def mlist(self):
#         return [self.LO_freq()-self.mix_freq, self.LO_freq(), self.LO_freq()+self.mix_freq]

#     def _sg_setup(self):
#         sg1.frequency(self.LO_freq())
#         sg1.amplitude_RF(self.power)
#         sg1.setup_IQ_mod_ext()
#         sg1.enable_RF()
#         pass



#     def Control_LO_enable(self, value='ON'):
#         sg1.enable_RF(value)


#     def _hdawg_setup(self, setup):
#         daq_hdawg.setInt(f"/{device_hdawg}/awgs/0/enable", 0)
#         if setup == 1:
#             # i_dc_ch.offset(0.0)
#             daq_hdawg.setDouble(f'/{device_hdawg}/sigouts/0/offset', 0)
#             # q_dc_ch.offset(0.0)
#             daq_hdawg.setDouble(f'/{device_hdawg}/sigouts/1/offset', 0)
#             # i_dc_ch.on(1)
#             daq_hdawg.setInt(f'/{device_hdawg}/sigouts/0/on', 1)
#             # q_dc_ch.on(1)
#             daq_hdawg.setInt(f'/{device_hdawg}/sigouts/1/on', 1)
#             # sin0.enables0(0)
#             daq_hdawg.setInt(f'/{device_hdawg}/sines/0/enables/0', 0)
#             # sin1.enables1(0)
#             daq_hdawg.setInt(f'/{device_hdawg}/sines/1/enables/1', 0)
#             pass
#         elif setup == 2:
#             # osc0.freq(IF)
#             daq_hdawg.setDouble(f'/{device_hdawg}/oscs/0/freq', self.mix_freq)
#             # aw0.gain1(awg_gain)
#             daq_hdawg.setDouble(f'/{device_hdawg}/awgs/0/outputs/0/gains/0', self.awg_gain)
#             # aw0.gain2(awg_gain)
#             daq_hdawg.setDouble(f'/{device_hdawg}/awgs/0/outputs/1/gains/1', self.awg_gain)
#             # sin0.amplitudes0(awg_sin_amp)
#             daq_hdawg.setDouble(f'/{device_hdawg}/sines/0/amplitudes/0', self.awg_sin_amp)
#             # sin1.amplitudes1(awg_sin_amp)
#             daq_hdawg.setDouble(f'/{device_hdawg}/sines/1/amplitudes/1', self.awg_sin_amp)
#             # sin0.enables0(1)
#             daq_hdawg.setInt(f'/{device_hdawg}/sines/0/enables/0', 1)
#             # sin1.enables1(1)
#             daq_hdawg.setInt(f'/{device_hdawg}/sines/1/enables/1', 1)
#             pass
#         elif setup == 3:     
#             # aw0.gain1(awg_gain)
#             daq_hdawg.setDouble(f'/{device_hdawg}/awgs/0/outputs/0/gains/0', self.awg_gain)
#             # aw0.gain2(awg_gain)
#             daq_hdawg.setDouble(f'/{device_hdawg}/awgs/0/outputs/1/gains/1', self.awg_gain)
#             # sin0.amplitudes0(awg_sin_amp)
#             daq_hdawg.setDouble(f'/{device_hdawg}/sines/0/amplitudes/0', self.awg_sin_amp)
#             # sin1.amplitudes1(awg_sin_amp)
#             daq_hdawg.setDouble(f'/{device_hdawg}/sines/1/amplitudes/1', self.awg_sin_amp)
#             # sin0.enables0(1)
#             daq_hdawg.setInt(f'/{device_hdawg}/sines/0/enables/0', 1)
#             # sin1.enables1(1)
#             daq_hdawg.setInt(f'/{device_hdawg}/sines/1/enables/1', 1)
#             pass
#         else:
#             pass
    
#     def _sa_setup(self, setup):
#         if setup == 1:
#             sa.center_frequency(self.LO_freq())
#             sa.span(250*kHz)
#             sa.bandwidth(3*kHz)
#             sa.sweep_points(201)
#             sa.reference_level(-10)
#             sleep(1)
#             sa.markers_off()
#             sa.sweep_single()
#             sa.markers_add_at([self.LO_freq()])
#             pass
#         elif setup == 2:
#             sa.center_frequency(self.LO_freq())
#             sa.span(2*self.mix_freq+5e6)
#             sa.bandwidth(30*kHz)
#             sa.sweep_points(4001)
#             sa.reference_level(-10)
#             sa.markers_off()
#             sa.sweep_single()
#             sa.markers_add_at(self.mlist())
#             pass

#     def _get_power(self):
#         sa.sweep_single()
#         sleep(0.010)
#         return sa.markers_read_Y()[0]

#     def _sideband_diff(self):
#         sa.sweep_single()
#         left, _ , right = sa.markers_read_Y()
#         if self.sideband=='left':
#             dif = left-right
#         elif self.sideband=='right':
#             dif = right-left
#         else:
#             raise Exception("Use sideband = left or right")
#         return dif

#     def _dc_sweep(self, i_arr, q_arr, plot = True):
#         progress_bar = progressbar.ProgressBar(maxval=len(i_arr), \
#             widgets=['\rOptimizing DC Offsets: ', progressbar.Bar('.', '', ''), ' ', progressbar.Percentage(), ' (', progressbar.ETA(), ') '])
#         progress_bar.start()
#         pow_arr = []
#         for index, i in enumerate(i_arr):
#             # i_dc_ch.offset(i)
#             daq_hdawg.setDouble(f'/{device_hdawg}/sigouts/0/offset', i)
#             pow_arr.append([])
#             progress_bar.update(index+1)
#             for idq, q in enumerate(q_arr):
#                 # q_dc_ch.offset(q)
#                 daq_hdawg.setDouble(f'/{device_hdawg}/sigouts/1/offset', q)
#                 if idq == 0:
#                     sleep(0.050)
#                 pow_arr[-1].append(self._get_power())
#         progress_bar.finish()
#         pow_arr = np.array(pow_arr)
#         indices = np.where(pow_arr == pow_arr.min())
#         # i_dc_ch.offset(i_arr[indices[0][0]])
#         daq_hdawg.setDouble(f'/{device_hdawg}/sigouts/0/offset', i_arr[indices[0][0]])
#         # q_dc_ch.offset(q_arr[indices[1][0]])
#         daq_hdawg.setDouble(f'/{device_hdawg}/sigouts/1/offset', q_arr[indices[1][0]])

#         if plot:
#             plt.imshow(pow_arr, aspect='auto', extent=[q_arr[0]*1e3, q_arr[-1]*1e3, i_arr[-1]*1e3, i_arr[-0]*1e3])
#             plt.colorbar()
#             plt.ylabel('I values (mV)')
#             plt.xlabel('Q values (mV)')
#             plt.show(block = False)
#         return i_arr[indices[0][0]],q_arr[indices[1][0]]


#     def optimize_dc(self, plot = False):
#         # ADD a save to file
#         self._sa_setup(1)
#         self._sg_setup()
#         self._hdawg_setup(1)

#         file_path = r'C:\Users\normaluser\miniconda3\envs\qcodes\Lib\site-packages\vslab\_control_IQ.txt'
#         if isfile(file_path):
#             with open(file_path, "r") as file:
#                 lastline = file.readlines()[-1].split('\t')
#                 lastline = list(map(float, lastline))
#             file.close()
#             i_guess = opt_i = float(lastline[0])
#             q_guess = opt_q = float(lastline[1])

#         else:
#             i_guess = opt_i = -1*0e-3
#             q_guess = opt_q = 1*0e-3

#         # Coarse sweep
#         #
#         # Fine sweep
#         i_arr = np.linspace(opt_i-20e-3, opt_i+20e-3, 16)
#         q_arr = np.linspace(opt_q-20e-3, opt_q+20e-3, 16)
#         opt_i, opt_q = self._dc_sweep(i_arr, q_arr, plot)
#         # print(f'fine i = {opt_i} and q = {opt_q}')
#         # Finer sweep
#         i_arr = np.linspace(opt_i-2*1e-3, opt_i+2*1e-3, 16)
#         q_arr = np.linspace(opt_q-2*1e-3, opt_q+2*1e-3, 16)
#         opt_i, opt_q = self._dc_sweep(i_arr, q_arr, plot)
#         # print(f'finer i = {opt_i} and q = {opt_q}')
#         sa.sweep_cont()
#         # i_ch.offset(opt_i)
#         #daq_uhf.setDouble(f"/{device_uhf}/sigouts/0/offset", opt_i)
#         # q_ch.offset(opt_q)
#         #daq_uhf.setDouble(f"/{device_uhf}/sigouts/1/offset", opt_q)
#         save = True
#         if save:
#             with open(file_path, "a") as iqfile:
#                 iqfile.write('\n'+str(opt_i)+'\t'+str(opt_q))
#         iqfile.close()
#         return opt_i, opt_q

#     def _optimize_ph(self, ph_arr, plot = True):
#         diffs = []
#         progress_bar = progressbar.ProgressBar(maxval=len(ph_arr), \
#             widgets=['\rOptimizing Phase ', progressbar.Bar('.', '', ''), ' ', progressbar.Percentage(), ' (', progressbar.ETA(), ') '])
#         progress_bar.start()
#         for index, phase in enumerate(ph_arr):
#             # aw0.modulation_phase_shift(phase)
#             daq_hdawg.setDouble(f'/{device_hdawg}/sines/1/phaseshift', phase)
#             sa.sweep_single()
#             diffs.append(self._sideband_diff())
#             progress_bar.update(index+1)
#         progress_bar.finish()
#         diffs = np.array(diffs)
#         ph_opt = ph_arr[np.argmax(diffs)]
#         # aw0.modulation_phase_shift(ph_opt)
#         daq_hdawg.setDouble(f'/{device_hdawg}/sines/1/phaseshift', ph_opt)
#         if plot:
#             plt.plot(ph_arr, diffs, '-ro')
#             plt.title('Phase calibration result')
#             plt.xlabel('Phase difference (degree)')
#             plt.ylabel('Sideband Difference (dB)')
#             plt.show()
#         return ph_opt

#     def optimize_phase(self, plot=True):
#         self._sa_setup(2)
#         self._hdawg_setup(2)
#         if self.sideband == 'right':
#             ph_arr = np.linspace(-110, -80, 41)
#         elif self.sideband == 'left':
#             ph_arr = np.linspace(85, 105, 41)
#         else:
#             raise Exception('Use sideband = left or right')
#         # Coarse sweep
#         opt_ph = self._optimize_ph(ph_arr, plot)
#         # Fine sweep
#         ph_arr = np.linspace(opt_ph - 1., opt_ph + 1., 41)
#         opt_ph = self._optimize_ph(ph_arr, plot)
#         # Finer sweep
#         ph_arr = np.linspace(opt_ph - 0.1, opt_ph + 0.1, 41)
#         sa.sweep_cont()
#         opt_ph = self._optimize_ph(ph_arr, plot)
#         # aw0.modulation_phase_shift(opt_ph)
#         daq_hdawg.setDouble(f'/{device_hdawg}/sines/1/phaseshift', opt_ph)
#         return opt_ph

#     def _optimize_amp(self, q_arr, plot=True):
#         diffs = []
#         import progressbar
#         progress_bar = progressbar.ProgressBar(maxval=len(q_arr), \
#             widgets=['\rOptimizing Amplitude', progressbar.Bar('.', '', ''), ' ', progressbar.Percentage(), ' (', progressbar.ETA(), ') '])
#         progress_bar.start()
#         for index, q in enumerate(q_arr):
#             # sin1.amplitudes1(q)
#             daq_hdawg.setDouble(f'/{device_hdawg}/sines/1/amplitudes/1', q)
#             diffs.append(self._sideband_diff())
#             progress_bar.update(index+1)
#         progress_bar.finish()

#         diffs = np.array(diffs)
        
#         if plot:
#             plt.plot(q_arr, diffs, '-ro')
#             plt.title('Ampltude calibration result')
#             plt.xlabel('Amplitude imbalance')
#             plt.ylabel('Sideband Difference (dB)')
#             plt.show()
#         opt_q = q_arr[np.argmax(diffs)]
#         return opt_q


#     def _optimize_amp(self, q_arr, plot=True):
#         diffs = []
#         import progressbar
#         progress_bar = progressbar.ProgressBar(maxval=len(q_arr), \
#             widgets=['\rOptimizing Amplitude', progressbar.Bar('.', '', ''), ' ', progressbar.Percentage(), ' (', progressbar.ETA(), ') '])
#         progress_bar.start()
#         for index, q in enumerate(q_arr):
#             # sin1.amplitudes1(q)
#             daq_hdawg.setDouble(f'/{device_hdawg}/sines/1/amplitudes/1', q)
#             diffs.append(self._sideband_diff())
#             progress_bar.update(index+1)
#         progress_bar.finish()

#         diffs = np.array(diffs)
        
#         if plot:
#             plt.plot(q_arr, diffs, '-ro')
#             plt.title('Ampltude calibration result')
#             plt.xlabel('Amplitude imbalance')
#             plt.ylabel('Sideband Difference (dB)')
#             plt.show()
#         opt_q = q_arr[np.argmax(diffs)]
#         return opt_q


#     def optimize_amplitude(self, plot=True):
#         self._sa_setup(2)
#         self._hdawg_setup(3)
#         q_arr = np.linspace(self.awg_sin_amp-0.05, self.awg_sin_amp+0.05,41)
#         opt_q = self._optimize_amp(q_arr, plot)
#         # sin1.amplitudes1(opt_q)
#         daq_hdawg.setDouble(f'/{device_hdawg}/sines/1/amplitudes/1', opt_q)
        
#         # Fine sweep
#         q_arr = np.linspace(opt_q-0.01, opt_q+0.01, 41)
#         opt_q = self._optimize_amp(q_arr, plot)
#         # sin1.amplitudes1(opt_q)
#         daq_hdawg.setDouble(f'/{device_hdawg}/sines/1/amplitudes/1', opt_q)
#         # Finer sweep

#         q_arr = np.linspace(opt_q-0.003, opt_q+0.003, 41)
#         opt_q = self._optimize_amp(q_arr, plot)
#         # sin1.amplitudes1(opt_q)
#         daq_hdawg.setDouble(f'/{device_hdawg}/sines/1/amplitudes/1', opt_q)
#         sa.sweep_cont()
#         return opt_q


#     def optimize_all(self, plot=True):
#         self.optimize_dc(plot)
#         self.optimize_phase(plot)
#         self.optimize_amplitude(plot)
#         self.post_calibration_ready()
#         pass

#     def post_calibration_ready(self):
#         # sin0.enables0(0)
#         daq_hdawg.setInt(f'/{device_hdawg}/sines/0/enables/0', 0)
#         # sin1.enables1(0)
#         daq_hdawg.setInt(f'/{device_hdawg}/sines/1/enables/1', 0)
#         daq_hdawg.setInt(f'/{device_hdawg}/awgs/0/outputs/1/modulation/mode', 2)
#         daq_hdawg.setInt(f'/{device_hdawg}/awgs/0/outputs/0/modulation/mode', 1)
#         # aw0.gain1(sin0.amplitudes0())
#         sin0amp0 = daq_hdawg.getDouble(f'/{device_hdawg}/sines/0/amplitudes/0')
#         daq_hdawg.setDouble(f'/{device_hdawg}/awgs/0/outputs/0/gains/0', sin0amp0)
#         # aw0.gain2(sin1.amplitudes1())
#         sin1amp1 = daq_hdawg.getDouble(f'/{device_hdawg}/sines/1/amplitudes/1')
#         daq_hdawg.setDouble(f'/{device_hdawg}/awgs/0/outputs/1/gains/1', sin1amp1)
#         pass

#     def osc_amp(self, value):
#         mod_amp_1 = daq_hdawg.getDouble(f"/{device_hdawg}/sines/0/amplitudes/0")
#         mod_amp_2 = daq_uhf.getDouble(f"/{device_hdawg}/sines/1/amplitudes/1")
#         ratio_iq = mod_amp_1 / mod_amp_2
#         daq_hdawg.setDouble(f"/{device_hdawg}/sines/0/amplitudes/0", value*ratio_iq)
#         daq_hdawg.setDouble(f"/{device_hdawg}/sines/1/amplitudes/1", value)
#         pass

#     def LO_power(self, value=9):
#         sg1.amplitude_RF(value)
#         self.power = value

#     def osc_amp_pulse(self, value):
#         mod_amp_1 = daq_hdawg.getDouble(f"/{device_hdawg}/awgs/0/outputs/0/gains/0")
#         mod_amp_2 = daq_uhf.getDouble(f"/{device_hdawg}/awgs/0/outputs/1/gains/1")
#         ratio_iq = mod_amp_1 / mod_amp_2
#         daq_hdawg.setDouble(f"/{device_hdawg}/awgs/0/outputs/0/gains/0", value*ratio_iq)
#         daq_hdawg.setDouble(f"/{device_hdawg}/awgs/0/outputs/1/gains/1", value)
#         pass

#     def cw_mode_on(self):
#         daq_hdawg.setInt(f'/{device_hdawg}/sines/0/enables/0', 1)
#         daq_hdawg.setInt(f'/{device_hdawg}/sines/1/enables/1', 1)
#         print('Stop AWG manually')

#     def pulse_mode_on(self):
#         self.post_calibration_ready()

    

################       Example 1           ####################


# from vslab.rack import *
# from vslab.constants import *
# from vslab.Readout_Control_vs import Readout, Control

# readout_frequency =  7.36849*GHz
# control_frequency = 6.12797*GHz

# # rd = Readout(UHF_ADDRESS, 'localhost')
# # rd.frequency = readout_frequency
# # rd.sideband = 'left'
# # rd.optimize_all()

# # rd.osc_amp(0.5)
# # rd.readout_mode_pulse()

# # rd.input_range(50e-3)
# # rd.pregain(10)
# # rd.time_constant_and_order(50e-9, 1)
# # rd.config_aux_for_scope(1500)


# cn = Control(HDAWG_ADDRESS, 'localhost')
# cn.frequency = control_frequency
# cn.sideband = 'right'
# cn.optimize_all()


################     Example 2           ####################

# rd = UHF(UHF_ADDRESS, 'localhost')
# # # data = rd._S21_osc_sweep(5.95*GHz, 6.050*GHz, 101)
# # # rd.optimize_all(True)

# rd.S21_pulse()
# daq.subscribe('/dev2232/demods/3/sample.X')
# daq.subscribe('/dev2232/demods/3/sample.Y')
# daq.execute()
# sleep(3)
# data = daq.read(flat=True)
# daq.unsubscribe('*')

            
            # x_array.append(data['/dev2232/demods/3/sample']['x'])
            # y_array.append(data['/dev2232/demods/3/sample']['y'])

            # mean_values

            # x_list.append(np.mean(data['/dev2232/demods/3/sample']['x']))
            # y_list.append(np.mean(data['/dev2232/demods/3/sample']['y']))

            # print((data['/dev2232/demods/3/sample']['x']))