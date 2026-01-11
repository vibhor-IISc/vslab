################################################
#
#   Minimum code required to for 
#  any measurement scripts using qcodes
#
from vslab.constants import *
from vslab.rack import *
close_all_instruments()
# from vslab.uhf_fast_readout import setup_uhf_fast_read
from tqdm import tqdm
import numpy as np
from time import sleep
import zhinst.qcodes as zi
from qcodes.instrument_drivers.rohde_schwarz.RTE1000 import RTE1000
from vslab.shfqc import mySHFQC
from qcodes import Measurement, Parameter


osc = RTE1000('osc', address = RTE_ADDRESS, model = 'RTE1034')

sqc = mySHFQC(1)

drive_frequency = 6.2e9 + 157.8*MHz
center_frequency = 6.2e9

sqc.initialize_channel(
    center_frequency=center_frequency,
    oscillator_frequency=drive_frequency-center_frequency,
    output_range = -10
)

exp_name='rabi20'
sample_name="FLUXONIUM_rabi"
mstart(sample_name = sample_name, exp_name = exp_name)

def progressBar(current, total, barLength = 20):
    percent = float(current) * 100 / total
    arrow   = '-' * int(percent/100 * barLength - 1) + '>'
    spaces  = ' ' * (barLength - len(arrow))
    print('\rProgress: [%s%s] %d %%' % (arrow, spaces, percent), end='')


seqc_program = lambda length :"""const len = %d;

wave w_flat = rect(len, 0.500);
wave w_marker = marker(len, 1);
wave w_sig_marker = w_flat + w_marker;

while (true) {
  playWave(w_sig_marker, w_sig_marker);
  waitWave();
  wait(100e-6*2e9);
}"""%length


# def awg_safety_check():
  
#AWG parameters
start_point = 32
stop_point = 700
incr = 16

len_arr = np.arange(start_point, stop_point, incr)

npts = len(len_arr)


# ############ Prep instruments for Power Rabi measurement


# ############

meas = Measurement()

t_ax    = Parameter(name='t_ax', label='time', unit='s')
d_x = Parameter(name='data_x', label='I-quad', unit='V')
d_y = Parameter(name='data_y', label='Q-quad', unit='V')
d_r = Parameter(name='data_r', label='R-abs', unit='V')
duration = Parameter(name='duration', label='len', unit='awg_points')

meas.register_parameter(duration)
meas.register_parameter(t_ax)
meas.register_parameter(d_x, setpoints=(duration, t_ax))
meas.register_parameter(d_y, setpoints=(duration, t_ax))
meas.register_parameter(d_r, setpoints=(duration, t_ax))

once = True
length_array = len_arr #np.linspace(start_point, stop_point, npts)
with meas.run() as datasaver:
    for index, length in enumerate(length_array):
        # run awg code-
        # awg_safety_check()
        sqc.load_program(seqc_program(length))
        sqc.enable_sequencer(single=1)
        osc.run_single()
        sleep(23)
        osc.ch1.trace.prepare_trace()
        osc.ch2.trace.prepare_trace()
        dt = osc.ch1.trace.setpoints[0]
        dx = osc.ch1.trace()
        dy = osc.ch2.trace()
        dr = np.sqrt(dx**2+dy**2)
        datasaver.add_result((duration, length),(t_ax, dt),(d_x, dx),(d_y, dy),(d_r, dr))
        progressBar(index+1, npts)
        if once:
            mcopy(__file__)
            once = False
dataset = datasaver.dataset
mdata(dataset)



