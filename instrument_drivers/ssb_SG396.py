import qt
from constants import *
from ZurichInstruments_UHFLI import ZurichInstruments_UHFLI
import numpy as np
import matplotlib.pyplot as plt
import time
import progressbar

# aps = qt.instruments.create('APSYN420',	'AnaPico_APSYN420',	address = APSYN420_ADDRESS)
fsv = qt.instruments.create('FSV', 'RhodeSchwartz_FSV', address = FSV_ADDRESS)
# sgs = qt.instruments.create('sgs', 'RS_SGS100A', address = SGS100A_ADDRESS)
uhf = ZurichInstruments_UHFLI('dev2232') # Initializing UHFLI

freq = 97
mix_freq = freq*MHz
# Test example assuming a 5 GHz qubit
sgs_freq =  6*GHz# + mix_freq  # ThIS is SGS freq = qubit_freq + mix_freq; as lower sideband would be matched with w_q
base_i = 0.9
sideband = 'right'

print('Setting LO...')
# sgs.set_frequency(sgs_freq)
qt.msleep(1)
# print(sgs.get_frequency()/GHz)


def get_power():
	_ , power = fsv.get_max_freqs(1)
	return power[0]


def sideband_diff():
	qt.msleep(0.2)
	freqs, powers = fsv.get_max_freqs(2)
	while (abs(freqs[0]-freqs[1]) < mix_freq*2-2*MHz or abs(freqs[0]-freqs[1]) > mix_freq*2+2*MHz):
		fsv.marker_next(2)
		freqs, powers = fsv.get_max_freqs(2)
	powers = [power for _,power in sorted(zip(freqs,powers))]
	if sideband is 'right':
		return powers[-1]-powers[0]
	elif sideband is 'left':
		return powers[0]-powers[-1]
	else:
		print('You have entered sideband other than left or right')



def dc_sweep(i_arr, q_arr, plot = False):
	uhf.set('sigouts/0/offset', 0.0)
	uhf.set('sigouts/1/offset', 0.0)
	import progressbar
	progress_bar = progressbar.ProgressBar(maxval=len(i_arr), \
	    widgets=['Optimizing DC Offsets: ', progressbar.Bar('.', '', ''), ' ', progressbar.Percentage(), ' (', progressbar.ETA(), ') '])
	progress_bar.start()
	pow_arr = []
	for index, i in enumerate(i_arr):
		uhf.set('sigouts/0/offset', i)
		pow_arr.append([])
		progress_bar.update(index+1)
		for q in q_arr:
			uhf.set('sigouts/1/offset', q)
			pow_arr[-1].append(get_power())
	progress_bar.finish()
	pow_arr = np.array(pow_arr)
	indices = np.where(pow_arr == pow_arr.min())
	uhf.set('sigouts/0/offset', i_arr[indices[0][0]])
	uhf.set('sigouts/1/offset', q_arr[indices[1][0]])
	if plot:
		plt.imshow(pow_arr, aspect='auto', extent=[q_arr[0], q_arr[-1], i_arr[-1], i_arr[-0]])
		plt.show()
	return i_arr[indices[0][0]],q_arr[indices[1][0]]


def optimize_dc(plot = False):
	fsv.set_centerfrequency(sgs_freq)
	fsv.set_span(1*MHz)
	fsv.set_bandwidth(1*kHz)
	fsv.set_sweep_points(501)
	fsv.set_referencelevel(-10)
	uhf.set('sigouts/0/offset', 0.0)
	uhf.set('sigouts/1/offset', 0.0)
	qt.msleep(1)
	fsv.marker_to_max()
	freq, power = fsv.get_max_freqs(1)


	i_arr = np.linspace(-500e-3, 500e-3, 25) # -18.49m
	q_arr = np.linspace(-500e-3, 500e-3, 25) # -24.24m
	opt_i, opt_q = dc_sweep(i_arr, q_arr, plot)
	# Coarse sweep
	i_arr = np.linspace(opt_i-25e-3, opt_i+25e-3, 10)
	q_arr = np.linspace(opt_q-25e-3, opt_q+25e-3, 10)
	opt_i, opt_q = dc_sweep(i_arr, q_arr, plot)
	# Fine sweep
	i_arr = np.linspace(opt_i-5e-3, opt_i+5e-3, 10)
	q_arr = np.linspace(opt_q-5e-3, opt_q+5e-3, 10)
	opt_i, opt_q = dc_sweep(i_arr, q_arr, plot)
	# Finer sweep
	i_arr = np.linspace(opt_i-1.e-3, opt_i+1.e-3, 20)
	q_arr = np.linspace(opt_q-1.e-3, opt_q+1.e-3, 20)
	return dc_sweep(i_arr, q_arr, plot)

def awg_program(phase=0,per = freq):
	awg_program_string = """
	//sine(samples, amplitude, phaseOffset, nrOfPeriods)
	wave w2 = sine(1800, 0.9, %f, %d);
	wave w3 = sine(1800, 0.9, 0, %d);	
	while (true) {
	  playWave(w2, w3);
	}""" % \
	(phase, per, per)
	return awg_program_string


def awg_program_amp(amp, phase=0,per = freq):
	awg_program_string = """
	//sine(samples, amplitude, phaseOffset, nrOfPeriods)
	wave w2 = sine(1800, 1, %f, %d);
	wave w3 = sine(1800, 1, 0, %d);	
	while (true) {
	  playWave(w2, w3);
	}""" % \
	(phase, per, per)
	return awg_program_string


def set_device_settings(number):
	if number == 1:
		# uhf.extclk()
		# aps.set_external_reference()
		# aps.set_frequency(center_freq)
		# aps.rf_on()
		# uhf.set('oscs/0/freq', mix_freq)
		# uhf.set('oscs/1/freq', mix_freq)
		uhf.set('awgs/0/enable', 0)
		uhf.set('sigouts/0/on', 1)
		uhf.set('sigouts/1/on', 1)
		uhf.set('sigouts/0/enables/3', 0)
		uhf.set('sigouts/1/enables/7', 0)
		uhf.imp_50()

	elif number == 2:
		uhf.set('sigouts/0/enables/3', 1)
		uhf.set('sigouts/1/enables/7', 1)
		# uhf.set('sigouts/1/amplitudes/7', 700e-3)
		# uhf.set('sigouts/0/amplitudes/3', 700e-3)
		uhf.set('awgs/0/outputs/0/amplitude', 700e-3/750e-3)
		uhf.set('awgs/0/outputs/1/amplitude', 700e-3/750e-3)
		fsv.set_span(2*mix_freq + 20*MHz)
		if freq > 200:
			fsv.set_bandwidth(1*MHz)
		else:
			fsv.set_bandwidth(5*kHz)
		fsv.set_sweep_points(20001)
		qt.msleep(1)
		fsv.markers_to_peaks(3)
		uhf.awg_on(single=False)


def optimize_ph(ph_arr, plot = False):
	diffs = []
	import progressbar
	progress_bar = progressbar.ProgressBar(maxval=len(ph_arr), \
	    widgets=['Optimizing Phase ', progressbar.Bar('.', '', ''), ' ', progressbar.Percentage(), ' (', progressbar.ETA(), ') '])
	progress_bar.start()
	uhf.set('awgs/0/outputs/0/amplitude', 0.5)
	uhf.set('awgs/0/outputs/1/amplitude', 0.5)
	for index, phase in enumerate(ph_arr):
		# uhf.set('demods/3/phaseshift', phase)
		uhf.setup_awg(awg_program(phase))
		uhf.awg_on(single=False)
		qt.msleep(1)
		fsv.markers_to_peaks(2)
		diffs.append(sideband_diff())
		progress_bar.update(index+1)
	progress_bar.finish()
	diffs = np.array(diffs)
	indices = np.where(diffs == diffs.max())
	# uhf.set('demods/3/phaseshift', ph_arr[indices[0][0]])
	uhf.setup_awg(awg_program(ph_arr[indices[0][0]]))
	uhf.awg_on(single=False)
	if plot:
		plt.plot(ph_arr, diffs, '-ro')
		plt.show()
	return ph_arr[indices[0][0]]



def optimize_phase(plot=False):
	if sideband is 'right':
		ph_arr = np.linspace(0, np.pi, 41)
		opt_ph = optimize_ph(ph_arr, plot)
		# opt_ph = -1.544
	elif sideband is 'left':
		# ph_arr = np.linspace(0, np.pi, 41)
		# opt_ph = optimize_ph(ph_arr, plot)
		if freq > 200: opt_ph = 1.4748
		else: opt_ph = 1.5460 
	else:
		print('You have entered sideband other than left or right')
	# Fine sweep
	ph_arr = np.linspace(0.97*opt_ph, 1.03*opt_ph, 21)
	opt_ph = optimize_ph(ph_arr, plot)
	# Finer sweep
	ph_arr = np.linspace(0.995*opt_ph, 1.005*opt_ph, 21)
	return optimize_ph(ph_arr, plot)


def optimize_amp(i_arr, q_arr, plot=False):
	diffs = []
	import progressbar
	progress_bar = progressbar.ProgressBar(maxval=len(i_arr), \
	    widgets=['Optimizing Amplitude', progressbar.Bar('.', '', ''), ' ', progressbar.Percentage(), ' (', progressbar.ETA(), ') '])
	progress_bar.start()
	for index, i in enumerate(i_arr):
		uhf.set('awgs/0/outputs/0/amplitude', i)
		# uhf.set('sigouts/0/amplitudes/3', i)
		diffs.append([])
		progress_bar.update(index+1)
		for q in q_arr:
			uhf.set('awgs/0/outputs/1/amplitude', q)
			# uhf.set('sigouts/1/amplitudes/7', q)
			diffs[-1].append(sideband_diff())
	progress_bar.finish()
	diffs = np.array(diffs)
	indices = np.where(diffs == diffs.max())
	uhf.set('sigouts/0/amplitudes/3', i_arr[indices[0][0]])
	uhf.set('sigouts/1/amplitudes/7', q_arr[indices[1][0]])
	if plot:
		plt.imshow(diffs, aspect='auto', extent=[q_arr[0], q_arr[-1], i_arr[-1], i_arr[-0]])
		plt.show()
	return i_arr[indices[0][0]],q_arr[indices[1][0]]

# This function fixes the amplitude of one ch. to 0.5 and 
# vary the ampltude of q ch. alone

def optimize_amp_update(q_arr, plot=False):
	diffs = []
	import progressbar
	progress_bar = progressbar.ProgressBar(maxval=len(q_arr), \
	    widgets=['Optimizing Amplitude', progressbar.Bar('.', '', ''), ' ', progressbar.Percentage(), ' (', progressbar.ETA(), ') '])
	progress_bar.start()
	uhf.set('awgs/0/outputs/1/amplitude', base_i)
	for index, q in enumerate(q_arr):
		uhf.set('awgs/0/outputs/0/amplitude', q)
		# qt.msleep(1)
		diffs.append(sideband_diff())
		progress_bar.update(index+1)
	progress_bar.finish()

	diffs = np.array(diffs)
	idx = np.argmax(diffs)
	# uhf.set('awgs/0/outputs/1/amplitude', q_arr[idx])
	if plot:
		plt.plot(q_arr, diffs, '-ro')
		plt.show()
	
	return q_arr[idx]


def optimize_amplitude(i_dc, q_dc, plot=False):
	i_arr = np.linspace(0, 480e-3-abs(i_dc), 10)/500e-3
	q_arr = np.linspace(0, 480e-3-abs(q_dc), 10)/500e-3
	opt_i, opt_q = optimize_amp(i_arr, q_arr, plot)
	# Fine sweep
	i_arr = (np.linspace(opt_i-10e-3/500e-3, opt_i+10e-3/500e-3, 20)).clip(0,700e-3/750e-3)
	q_arr = (np.linspace(opt_q-10e-3/500e-3, opt_q+10e-3/750e-3, 20)).clip(0,700e-3/750e-3)
	opt_i, opt_q = optimize_amp(i_arr, q_arr, plot)
	# Finer sweep
	i_arr = (np.linspace(opt_i-0.5e-3/750e-3, opt_i+0.5e-3/750e-3, 20)).clip(0,700e-3/750e-3)
	q_arr = (np.linspace(opt_q-0.5e-3/750e-3, opt_q+0.5e-3/750e-3, 20)).clip(0,700e-3/750e-3)
	return optimize_amp(i_arr, q_arr, plot)

# This function fixes the amplitude of one ch. to 0.5 and 
# vary the ampltude of q ch. alone

def optimize_amplitude_update(plot=False):
	q_arr = np.linspace(0.8, 1, 41)
	opt_q = optimize_amp_update(q_arr, plot)
	uhf.set('awgs/0/outputs/0/amplitude', opt_q)
	# Fine sweep

	q_arr = np.linspace(opt_q-0.050, opt_q+0.050, 41)
	opt_q = optimize_amp_update(q_arr, plot)
	uhf.set('awgs/0/outputs/0/amplitude', opt_q)
	# Finer sweep

	q_arr = np.linspace(opt_q-0.010, opt_q+0.010, 41)
	opt_q = optimize_amp_update(q_arr, plot)
	uhf.set('awgs/0/outputs/0/amplitude', opt_q)
	return opt_q


def optimize_all(plot=False):
	uhf.setup_awg(awg_program())
	set_device_settings(1)
	i_dc, q_dc = optimize_dc(plot=plot)
	set_device_settings(2)
	phase = optimize_phase(plot=plot)
	i_amp, q_amp = optimize_amplitude(i_dc, q_dc, plot=plot)
	freqs, powers = fsv.get_max_freqs(2)
	with open('Qubit/optimize_data.txt', 'a') as file:
		file.write('\n%f %f %f %f %f %f %f %f:%f %f:%f'%(sgs_freq, mix_freq, i_dc, q_dc, phase, i_amp, q_amp, freqs[0], powers[0], freqs[1], powers[1]))
	return i_dc, q_dc, phase, i_amp, q_amp


def optimize_all_update(plot=False):
	uhf.setup_awg(awg_program())
	set_device_settings(1)
	i_dc, q_dc = optimize_dc(plot=False)
	set_device_settings(2)
	phase = optimize_phase(plot=plot)

	q_amp = optimize_amplitude_update(plot=plot)
	freqs, powers = fsv.get_max_freqs(2)
	print(i_dc, q_dc, phase, base_i, q_amp)
	fsv.set_markerN_frequency(3, sgs_freq)
	with open('Qubit/optimize_data_update.txt', 'a') as file:
		file.write('\n%f %f %f %f %f %f %f %f %f %f %f'%(sgs_freq, mix_freq, i_dc, q_dc, phase, base_i, q_amp, freqs[0], powers[0], freqs[1], powers[1]))
	return i_dc, q_dc, phase, base_i, q_amp


if __name__=='__main__':
	optimize_all_update(plot=True)