# -*- coding: utf-8 -*-
"""
Created on Mon May  3 15:53:00 2021

@author: normaluser
"""

sideband = 'left'
cavity_freq = 6.07856*1e9
IF = 56.25*1e6  # THIS IS HARD CODED. DO NOT CHANGE. 

LO_freq = cavity_freq + IF #(LO)
mlst = [LO_freq-IF, LO_freq, LO_freq+IF]
LO_power = 14.0

awg_sin_amp = 0.1



import time
import textwrap
import progressbar
import numpy as np
import matplotlib.pyplot as plt
from zhinst.utils import create_api_session, api_server_version_check

from vslab.constants import *
from vslab.rack import *

close_all_instruments()

import zhinst.qcodes as zi
from qcodes.instrument_drivers.rohde_schwarz.FSV13_2 import FSV13_2
from qcodes.instrument_drivers.rohde_schwarz.SGS100A import RohdeSchwarz_SGS100A


uhf = zi.UHFLI(UHF_ADDRESS, 'localhost')
LO = RohdeSchwarz_SGS100A('LO', 'TCPIP0::169.254.2.20::inst0::INSTR') # Mixure Lo
sa = FSV13_2('sa', address = FSV_ADDRESS)

###### Setting up LO




(daq_uhf, device_uhf, _) = create_api_session(UHF_ADDRESS, 6)
api_server_version_check(daq_uhf)

i_ch = uhf.sigouts[0]
q_ch = uhf.sigouts[1]

awg_uhf = daq_uhf.awgModule()
awg_uhf.set("device", device_uhf)
awg_uhf.execute()

def _uhf_initial_setup():
    # SET UHF to external 10 MHz
    uhf.system.extclk(1)
    # setting all oscillators to common frequency
    uhf.oscs.oscs0.freq(IF)
    uhf.oscs.oscs1.freq(IF)
    uhf.oscs.oscs2.freq(IF)
    uhf.oscs.oscs3.freq(IF)
    uhf.oscs.oscs4.freq(IF)
    uhf.oscs.oscs5.freq(IF)
    uhf.oscs.oscs6.freq(IF)
    uhf.oscs.oscs7.freq(IF)
    
    # Linking Demods to Osc
    uhf.demods.demods0.oscselect(0)
    uhf.demods.demods1.oscselect(1)
    uhf.demods.demods2.oscselect(2)
    uhf.demods.demods3.oscselect(3)
    uhf.demods.demods4.oscselect(4)
    uhf.demods.demods5.oscselect(5)
    uhf.demods.demods6.oscselect(6)
    # special command for SSB
    # to set 8th Demod to 4th Osc
    uhf.demods.demods7.oscselect(3)
    pass



def modulation_phase_shift(phase):
    # src_s = _awg_prep_code(phase)
    uhf.demods.demods7.phaseshift(phase)
    # _uhf_awg_upload_compile_execute(src_s)
    pass

def sin1_amplitudes1(opt_q):
    daq_uhf.setDouble("/dev2232/sigouts/0/amplitudes/3",opt_q)
    # q_ch.amplitudes7(opt_q)
    pass

def _awg_prep_code(phase):
    return awg_program.replace("_ph_",str(phase))


awg_post_calibration_program = textwrap.dedent(
    """\
wave wave1 = rect(6000*5, 1);
while (true) 
  {
    waitDigTrigger(1, 1);
    setTrigger(0b0010);
    // waitDemodOscPhase(4);
    playWave(wave1, wave1);
    waitWave();
    setTrigger(0b0000);
    wait(200e-6/4.4e-9);
  }
    """
    )


def _uhf_awg_upload_compile_execute(src_string):
    awg_uhf.set("compiler/sourcestring", src_string)
    while awg_uhf.getInt("compiler/status") == -1:
        time.sleep(0.1)
    if awg_uhf.getInt("compiler/status") == 1:
        raise Exception(awg_uhf.getString("compiler/statusstring"))
    if awg_uhf.getInt("compiler/status") == 0:
        pass
    if awg_uhf.getInt("compiler/status") == 2:
        print("Compilation successful with warnings, will upload the program to the instrument.")
        print("Compiler warning: ", awg_uhf.getString("compiler/statusstring"))

    # Wait for the waveform upload to finish
    time.sleep(0.2)
    i = 0
    while (awg_uhf.getDouble("progress") < 1.0) and (awg_uhf.getInt("elf/status") != 1):
        # print(f"{i} progress: {awg_uhf.getDouble('progress'):.2f}")
        time.sleep(0.5)
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



def _signal_core_setup():
    # check if 10 MHz is needed.
    LO.frequency(LO_freq)
    LO.power(LO_power)
    LO.status(True)
    pass

def _awg_uhf_setup(setup):
    if daq_uhf.getInt(f"/{device_uhf}/awgs/0/enable")==1:
            daq_uhf.setInt(f"/{device_uhf}/awgs/0/enable", 0)
            pass
    if setup == 1:
        '''
        LO minimization
        '''
        i_ch.offset(0.0)
        q_ch.offset(0.0)
        i_ch.on(1)
        q_ch.on(1)
        # i_ch.enables3(0)
        daq_uhf.setInt("/dev2232/sigouts/0/enables/3", 0)
        # q_ch.enables7(0)
        daq_uhf.setInt("/dev2232/sigouts/1/enables/7", 0)
        pass

    elif setup == 2:
        ''' Phase optimization
        '''
        daq_uhf.setDouble("/dev2232/sigouts/0/amplitudes/3",awg_sin_amp)
        # daq_uhf.setDouble("/dev2232/awgs/0/outputs/0/amplitude",0.1)
        # i_ch.amplitudes3(awg_sin_amp)
        daq_uhf.setDouble("/dev2232/sigouts/1/amplitudes/7",awg_sin_amp)
        # daq_uhf.setDouble("/dev2232/awgs/0/outputs/1/amplitude",0.1)
        # q_ch.amplitudes7(awg_sin_amp)
        
        daq_uhf.setInt("/dev2232/sigouts/0/enables/3", 1)
        # i_ch.enables3(1)
        daq_uhf.setInt("/dev2232/sigouts/1/enables/7", 1)
        # q_ch.enables7(1)
        # _awg_prep_code(np.pi/2)
        pass
    
    elif setup == 3:
        ''' amplitude optimization
        '''
        daq_uhf.setDouble("/dev2232/sigouts/0/amplitudes/3",awg_sin_amp)
        # daq_uhf.setDouble("/dev2232/awgs/0/outputs/0/amplitude",awg_sin_amp)
        # i_ch.amplitudes3(awg_sin_amp)
        daq_uhf.setDouble("/dev2232/sigouts/1/amplitudes/7",awg_sin_amp)
        # daq_uhf.setDouble("/dev2232/awgs/0/outputs/1/amplitude",awg_sin_amp)
        # q_ch.amplitudes7(awg_sin_amp)
        i_ch.on(1)
        q_ch.on(1)
        pass
    else:
        pass
            
def _sa_setup(setup):
    if setup == 1:
        sa.center_frequency(LO_freq)
        sa.span(200*kHz)
        sa.bandwidth(5*kHz)
        sa.sweep_points(201)
        sa.reference_level(-10)
        time.sleep(1)
        sa.markers_off()
        sa.sweep_single()
        sa.markers_add_at([LO_freq])
        pass
    elif setup == 2:
        sa.center_frequency(LO_freq)
        sa.span(2*IF+5e6)
        sa.bandwidth(30*kHz)
        sa.sweep_points(4001)
        sa.sweep_count(1)
        sa.reference_level(-10)
        sa.markers_off()
        sa.sweep_single()
        sa.markers_add_at(mlst)
        pass
        
def _get_power():
    sa.sweep_single()
    return sa.markers_read_Y()[0]

def _sideband_diff(mlist, sideband):
    sa.sweep_single()
    left, _, right = sa.markers_read_Y()
    if sideband=='left':
        dif = left-right
    elif sideband=='right':
        dif = right-left
    else:
        raise Exception("Use sideband = left or right")
    return dif

def _dc_sweep(i_arr, q_arr, plot = False):
    progress_bar = progressbar.ProgressBar(maxval=len(i_arr), \
        widgets=['\rOptimizing DC Offsets: ', progressbar.Bar('.', '', ''), ' ', progressbar.Percentage(), ' (', progressbar.ETA(), ') '])
    progress_bar.start()
    pow_arr = []
    for index, i in enumerate(i_arr):
        i_ch.offset(i)
        pow_arr.append([])
        progress_bar.update(index+1)
        for q in q_arr:
            q_ch.offset(q)
            pow_arr[-1].append(_get_power())
    progress_bar.finish()
    pow_arr = np.array(pow_arr)
    indices = np.where(pow_arr == pow_arr.min())
    i_ch.offset(i_arr[indices[0][0]])
    q_ch.offset(q_arr[indices[1][0]])
    if plot:
        plt.imshow(pow_arr, aspect='auto', extent=[q_arr[0]*1e3, q_arr[-1]*1e3, i_arr[-1]*1e3, i_arr[-0]*1e3])
        plt.colorbar()
        plt.ylabel('I values (mV)')
        plt.xlabel('Q values (mV)')
        plt.show(block = False)
    return i_arr[indices[0][0]],q_arr[indices[1][0]]

def optimize_dc(plot = False):
    _sa_setup(1)
    _signal_core_setup()
    _awg_uhf_setup(1)
    i_guess = opt_i = -19*1e-3
    q_guess = opt_q = -25*1e-3
    # Coarse sweep
    #
    # Fine sweep
    i_arr = np.linspace(opt_i-70e-3, opt_i+100e-3, 11)
    q_arr = np.linspace(opt_q-70e-3, opt_q+50e-3, 11)
    opt_i, opt_q = _dc_sweep(i_arr, q_arr, plot)
    # print(f'fine i = {opt_i} and q = {opt_q}')
    # Finer sweep
    i_arr = np.linspace(opt_i-10.*1e-3, opt_i+10.*1e-3, 21)
    q_arr = np.linspace(opt_q-10.*1e-3, opt_q+10.*1e-3, 21)
    opt_i, opt_q = _dc_sweep(i_arr, q_arr, plot)
    # print(f'finer i = {opt_i} and q = {opt_q}')
    sa.sweep_cont()
    i_ch.offset(opt_i)
    q_ch.offset(opt_q)
    return opt_i, opt_q

def _optimize_ph(ph_arr, plot = False):
    diffs = []
    progress_bar = progressbar.ProgressBar(maxval=len(ph_arr), \
        widgets=['\rOptimizing Phase ', progressbar.Bar('.', '', ''), ' ', progressbar.Percentage(), ' (', progressbar.ETA(), ') '])
    progress_bar.start()
    for index, phase in enumerate(ph_arr):
        modulation_phase_shift(phase)
        sa.sweep_single()
        diffs.append(_sideband_diff(mlst, sideband))
        progress_bar.update(index+1)
    progress_bar.finish()
    diffs = np.array(diffs)
    ph_opt = ph_arr[np.argmax(diffs)]
    modulation_phase_shift(ph_opt)
    if plot:
        plt.plot(ph_arr, diffs, '-ro')
        plt.title('Phase calibration result')
        plt.xlabel('Phase difference (degree)')
        plt.ylabel('Sideband Difference (dB)')
        plt.show()
    return ph_opt

def optimize_phase(plot=False):
    _sa_setup(2)
    _awg_uhf_setup(2)
    if sideband == 'left':
        ph_arr = np.linspace(-150, -70, 41)
    elif sideband == 'right':
        ph_arr = np.linspace(150, 100, 41)
    else:
        raise Exception('Use sideband = left or right')
    # Coarse sweep
    opt_ph = _optimize_ph(ph_arr, plot)
    # Fine sweep
    ph_arr = np.linspace(opt_ph - 2., opt_ph + 2., 41)
    opt_ph = _optimize_ph(ph_arr, plot)
    # Finer sweep
    ph_arr = np.linspace(opt_ph - 0.1, opt_ph + 0.1, 21)
    sa.sweep_cont()
    opt_ph = _optimize_ph(ph_arr, plot)
    modulation_phase_shift(opt_ph)
    return opt_ph

def _optimize_amp(q_arr, plot=False):
    diffs = []
    import progressbar
    progress_bar = progressbar.ProgressBar(maxval=len(q_arr), \
        widgets=['\rOptimizing Amplitude', progressbar.Bar('.', '', ''), ' ', progressbar.Percentage(), ' (', progressbar.ETA(), ') '])
    progress_bar.start()
    for index, q in enumerate(q_arr):
        sin1_amplitudes1(q)
        diffs.append(_sideband_diff(mlst, sideband))
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

def optimize_amplitude(plot=False):
    _sa_setup(2)
    _awg_uhf_setup(3)
    q_arr = np.linspace(awg_sin_amp-0.05,awg_sin_amp+0.05,41)
    opt_q = _optimize_amp(q_arr, plot)
    
    sin1_amplitudes1(opt_q)
    
    # Fine sweep
    q_arr = np.linspace(opt_q-0.01, opt_q+0.01, 41)
    opt_q = _optimize_amp(q_arr, plot)
    sin1_amplitudes1(opt_q)
    # Finer sweep

    q_arr = np.linspace(opt_q-0.005, opt_q+0.005, 41)
    opt_q = _optimize_amp(q_arr, plot)
    sin1_amplitudes1(opt_q)
    sa.sweep_cont()
    return opt_q

def optimize_all(plot=False):
    _uhf_initial_setup()
    
    optimize_dc(plot)
    ph_op = optimize_phase(plot)
    optimize_amplitude(plot)
    daq_uhf.sync()
    return ph_op

def post_calibration_ready(phase):
    mod_amp_1 = daq_uhf.getDouble(f"/{device_uhf}/sigouts/0/amplitudes/3")
    mod_amp_2 = daq_uhf.getDouble(f"/{device_uhf}/sigouts/1/amplitudes/7")
    daq_uhf.setDouble(f"/{device_uhf}/awgs/0/outputs/0/amplitude", mod_amp_1)
    daq_uhf.setDouble(f"/{device_uhf}/awgs/0/outputs/1/amplitude", mod_amp_2)
    daq_uhf.setInt(f"/{device_uhf}/awgs/0/outputs/0/mode", 1)
    daq_uhf.setInt(f"/{device_uhf}/awgs/0/outputs/1/mode", 1)
    # Writing the READOUT AWG code
    _uhf_awg_upload_compile_execute(awg_post_calibration_program)
    # Setting up the DIGITAL Triggers
    uhf.triggers.out.out0.source(32)
    uhf.triggers.out.out0.drive(0)
    daq_uhf.setInt(f"/{device_uhf}/awgs/0/auxtriggers/0/channel", 0)
    daq_uhf.setInt(f"/{device_uhf}/awgs/0/auxtriggers/0/slope", 1)
    pass
       
    

if __name__ == '__main__':
    phase = optimize_all(plot= True)
    post_calibration_ready(phase)
    LO.status(True)
    
    
    
