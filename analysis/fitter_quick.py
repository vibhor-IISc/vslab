import numpy as np
import lmfit as lm
import matplotlib.pyplot as plt
import inspect

def approx_FWHM(X,Y):
    half_max = np.max(Y) / 2.
    #find when function crosses line half_max (when sign of diff flips)
    #take the 'derivative' of signum(half_max - Y[])
    d = np.sign(half_max - np.array(Y[0:-1])) - np.sign(half_max - np.array(Y[1:]))
    #plot(X[0:len(d)],d) #if you are interested
    #find the left and right most indexes
    left_idx = np.where(d > 0)[0][0]
    right_idx = np.where(d < 0)[0][-1]
    return X[right_idx] - X[left_idx] #return the difference (full width)

def normalizedComplexRootLorentzian(f, f0, kappa):
	return (kappa/2)/(kappa/2-1j*(f-f0))

def complexRootLorentzian(f, f0, kappa, norm):
	return norm*normalizedComplexRootLorentzian(f, f0, kappa)

def complexRootLorentzianWithConstantPhase(f, f0, kappa, norm, phase):
	return complexRootLorentzian(f, f0, kappa, norm)*np.exp(1j*phase)

def complexRootLorentzianWithFrequencyDependantPhase(f, f0, kappa, norm, freq_phase):
	return complexRootLorentzian(f, f0, kappa, norm)*np.exp(1j*f*freq_phase)

def complexRootLorentzianWithFrequencyDependantPhaseAndConstantPhase(f, f0, kappa, norm, freq_phase, phase):
	return complexRootLorentzianWithFrequencyDependantPhase(f, f0, kappa, norm, freq_phase)*np.exp(1j*phase)

def complexRootLorentzianWithFrequencyDependantPhaseConstantPhaseAndOffset(f, f0, kappa, norm, freq_phase, phase, real_offset, imag_offset):
	return complexRootLorentzianWithFrequencyDependantPhaseAndConstantPhase(f, f0, kappa, norm, freq_phase, phase)+real_offset+1j*imag_offset

def complexRootLorentzianWithOffset(f, f0, kappa, norm, real_offset, imag_offset):
	return complexRootLorentzian(f, f0, kappa, norm)+real_offset+1j*imag_offset

def rootLorentzian(f, f0, kappa, norm):
	return np.abs(complexRootLorentzian(f, f0, kappa, norm))

def invertedRootLorentzian(f, f0, kappa, norm):
	return -np.abs(complexRootLorentzian(f, f0, kappa, norm))

def rootLorentzianWithOffset(f, f0, kappa, norm, offset):
	return rootLorentzian(f, f0, kappa, norm)+offset

def invertedRootLorentzianWithOffset(f, f0, kappa, norm, offset):
	return -rootLorentzian(f, f0, kappa, norm)+offset

def lorentzian(f, f0, kappa, norm):
	return rootLorentzian(f, f0, kappa, norm)**2

def invertedLorentzian(f, f0, kappa, norm):
	return -rootLorentzian(f, f0, kappa, norm)**2

def lorentzianWithOffset(f, f0, kappa, norm, offset):
	return lorentzian(f, f0, kappa, norm)+offset

def invertedLorentzianWithOffset(f, f0, kappa, norm, offset):
	return -lorentzian(f, f0, kappa, norm)+offset

def normalizedS11(f, f0, ke, ki):
	return 1-ke/((ki+ke)/2+1j*(f-f0))

def S11(f, f0, ke, ki, norm):
	return norm*normalizedS11(f, f0, ke, ki)

def S11WithConstantPhase(f, f0, ke, ki, norm, phase):
	return S11(f, f0, ke, ki, norm)*np.exp(1j*phase)

def S11WithConstantPhaseAndFrequencyDependentPhase(f, f0, ke, ki, norm, phase, freq_phase):
	return S11WithConstantPhase(f, f0, ke, ki, norm, phase)*np.exp(1j*f*freq_phase)

def exponential(t, tau, norm):
	return norm*np.exp(-t/tau)

def custom(x, a, b, c):
	return a*x**2 + b*x + c

lorentzian_func_list = [
				 normalizedComplexRootLorentzian,
				 complexRootLorentzian,
				 complexRootLorentzianWithConstantPhase,
				 complexRootLorentzianWithFrequencyDependantPhase,
				 complexRootLorentzianWithFrequencyDependantPhaseAndConstantPhase,
				 complexRootLorentzianWithFrequencyDependantPhaseConstantPhaseAndOffset,
				 complexRootLorentzianWithOffset,
				 rootLorentzian,
				 rootLorentzianWithOffset,
				 lorentzian,
				 lorentzianWithOffset
				 ]

inverted_lorentzian_func_list = [
					 invertedRootLorentzian,
					 rootLorentzianWithOffset,
					 invertedRootLorentzianWithOffset,
					 invertedLorentzian,
					 invertedLorentzianWithOffset
					 ]

single_port_func_list = [
						normalizedS11,
						S11,
						S11WithConstantPhase,
						S11WithConstantPhaseAndFrequencyDependentPhase
						]

exp_func_list = [
				exponential,
				]

all_funcs = lorentzian_func_list + inverted_lorentzian_func_list + single_port_func_list

def help(*args):
	if len(args) == 0:
		print("*********************")
		print(" List of available functions")
		print("*********************")
		for i,f in enumerate(all_funcs):
			print("%02d"%(i+1) + ". "+ f.__name__)

	else:
		for func in args:
			if func in all_funcs:
				print("*********************")
				print(func.__name__)
				print("*********************")
				for p in inspect.getargspec(func)[0][1:]:
					print(p)
			else:
				raise Exception("Unrecognized input")

class Fitter(object):
	'''
	Use to define the Model.To see the full list use: help()
	Available methods:
	.fit()
	.plot()
	.save_plot()
	.save_fit_values()
	'''

	def __init__(self, func, complex_fit=False):
		self.method = 'leastsq'
		self.complex_fit = complex_fit
		self.func = func
		self.params = []
		for p in inspect.getargspec(func)[0][1:]:
				self.params.append(Parameter(name=p, fitter=self))

	def fit(self, xdata, ydata, print_report=False, use_previous_values=False, **kwargs):
		'''
		Return result object from lm.minimizer

		'''
		y = np.copy(ydata)
		if self.func in lorentzian_func_list:
			offset = np.average(y[int(0.9*len(y)):len(y)])
			norm = np.max(y)-offset
			f0 = xdata[np.argmax(y)]
			abs_off_y = np.abs((np.abs(y)-np.abs(offset)))
			kappa = approx_FWHM(xdata, abs_off_y)

		elif self.func in inverted_lorentzian_func_list:
			offset = np.average(np.abs(y)[int(0.9*len(y)):len(y)])
			norm = np.min(np.abs(y))-offset
			f0 = xdata[np.argmin(np.abs(y))]
			abs_off_y = np.abs((np.abs(y)-offset))
			kappa = approx_FWHM(xdata, abs_off_y)

		elif self.func in single_port_func_list:
			norm = np.average(np.abs(y)[int(0.9*len(y)):len(y)])
			f0 = xdata[np.argmin(np.abs(y))]
			abs_off_y = np.abs((np.abs(y)-norm))
			kappa = approx_FWHM(xdata, abs_off_y)

		elif self.func in exp_func_list:
			norm = np.max(np.abs(y))
			tau = np.abs(xdata[-1]-xdata[0])/3

		if self.complex_fit:
			ydata = np.concatenate((np.real(ydata), np.imag(ydata)))
			def residual(params):
				p=[]
				for key,value in list(params.valuesdict().items()):
					p.append(value)
				print(p)
				return np.concatenate((np.real(self.func(xdata, *p)), np.imag(self.func(xdata, *p))))-ydata
		else:
			# ydata = np.abs(ydata)
			def residual(params):
				p=[]
				for key,value in list(params.valuesdict().items()):
					p.append(value)
				return np.abs(self.func(xdata, *p)) - y

		lmfit_params = lm.Parameters()
		for param in self.params:
			# print param.val, param.start, param.stop
			if param.name in kwargs:
				param.init = kwargs[param.name]

			elif use_previous_values:
				init = param.val

			elif self.func in lorentzian_func_list or self.func in inverted_lorentzian_func_list:
				if param.name == 'f0':
					param.init = f0
				elif param.name == 'kappa':
					param.init = kappa
				elif param.name == 'norm':
					param.init = norm
				elif param.name == 'offset':
					param.init = offset
				elif param.name == 'real_offset':
					param.init = 0
				elif param.name == 'imag_offset':
					param.init = 0
				elif param.name == 'freq_phase':
					param.init = 0
				elif param.name == 'phase':
					param.init = 0

			elif self.func in single_port_func_list:
				if param.name == 'f0':
					param.init = f0
				elif param.name =='ki':
					param.init = kappa/2
				elif param.name =='ke':
					param.init = kappa/2
				elif param.name == 'norm':
					param.init = norm
				elif param.name == 'phase':
					param.init = 0
				elif param.name == 'freq_phase':
					param.init = 0

			elif self.func in exp_func_list:
				if param.name == 'tau':
					param.init = tau
				elif param.name == 'norm':
					param.init = norm

			init = param.init
			lmfit_params.add(param.name, value=init, min=param.start, max=param.stop)
		# print lmfit_params
		self.mi = lm.minimize(residual,lmfit_params,method=self.method)
		for param in self.params:
			param.val = self.mi.params[param.name].value
			param.stderr = self.mi.params[param.name].stderr
		if print_report:
			print(lm.fit_report(self.mi))
		self.ydata = ydata
		self.xdata = xdata
		return self.mi

	def plot(self):
		'''
		Plots the last fit
		'''
		param_values = []
		for param in self.params:
			param_values.append(param.val)
		fit_data = self.func(self.xdata, *param_values)
		xdata = self.xdata
		if self.complex_fit:
			xdata = np.concatenate((self.xdata, self.xdata))
			fit_data = np.concatenate((np.real(fit_data), np.imag(fit_data)))
		plt.clf()
		plt.plot(xdata, self.ydata, 'bo')
		plt.plot(xdata, fit_data, 'r')
		# plt.plot(self.xdata, self.mi.residual+self.ydata, 'r')
		plt.show()

	def save_plot(self, fname):
		'''
		Saves the last fit figure using Matplotlib
		'''
		param_values = []
		for param in self.params:
			param_values.append(param.val)
		fit_data = self.func(self.xdata, *param_values)
		xdata = self.xdata
		if self.complex_fit:
			xdata = np.concatenate((self.xdata, self.xdata))
			fit_data = np.concatenate((np.real(fit_data), np.imag(fit_data)))
		plt.clf()
		plt.plot(xdata, self.ydata, 'bo')
		plt.plot(xdata, fit_data, 'r')
		# plt.plot(self.xdata, self.mi.residual+self.ydata, 'r')
		plt.savefig(fname)
		plt.close()

	def save_fit_values(self, fname, Header = False):
		'''
		Write the fit parameters to a file.
		Use Header = True to write the header information
		'''
		with open(fname, 'w') as f:
			if Header:
				f.write('#')
				for param in self.params:
					f.write(str(param.name) + '\t')
			else:
				f.write('\n')
				for param in self.params:
					f.write(str(param.val) + '\t')
				for param in self.params:
					f.write(str(param.stderr) + '\t')
			f.write('\n')
			pass



class Parameter(object):

	def __init__(self, name, fitter, start=None, stop=None, init=None):
		self.fitter = fitter
		self.start = start
		self.stop = stop
		self.name = name
		self.init = init
		self.val = self.init
		self.stderr = None

class Data(object):

	def __init__(self, fname, dtype=float,
							 comments='#',
							 delimiter=None,
							 converters=None,
							 skiprows=0,
							 usecols=None,
							 unpack=True,
							 ndmin=0,
							 encoding=bytes):

		self.data = np.loadtxt(fname, 
							   dtype=dtype, 
							   comments=comments, 
							   delimiter=delimiter, 
							   converters=converters, 
							   skiprows=skiprows, 
							   usecols=usecols, 
							   unpack=unpack)

		self.read_meta(fname)

		if self.znpts == 1:
			if self.ynpts == 1:
				self.dim = 1
				self.rearrange(1)
			else:
				self.dim = 2
				self.rearrange(2)
		else:
			self.dim = 3
			self.rearrange(3)

	def rearrange(self, dim):
		self.x = np.linspace(self.xstart, self.xstop, self.xnpts)
		self.y = [1]
		self.z = [1]

		if dim == 1:
			if self.data.shape[0] == 5:
				# real, imag, abs, phase (HOPEFULLY THIS WON'T CHANGE)
				if np.abs(self.data[1][0]+1j*self.data[2][0] - self.data[3][0]*np.exp(1j*self.data[4][0])) > 1e-10:
					raise Exception('Data is probably not in the format [real, imag, abs, phase]')
				self.data = self.data[3]*np.exp(1j*self.data[4])

			elif self.data.shape[0] == 3:
				# abs, phase (HOPEFULLY THIS WON'T CHANGE)
				self.data = self.data[1]*np.exp(1j*self.data[2])

		if dim == 2:
			if self.data.shape[0] == 6:
				# real, imag, abs, phase (HOPEFULLY THIS WON'T CHANGE)
				if np.abs(self.data[2][0]+1j*self.data[3][0] - self.data[4][0]*np.exp(1j*self.data[5][0])) > 1e-10:
					raise Exception('Data is probably not in the format [real, imag, abs, phase]')
				self.data = self.data[4]*np.exp(1j*self.data[5])

			elif self.data.shape[0] == 4:
				# abs, phase (HOPEFULLY THIS WON'T CHANGE)
				self.data = self.data[2]*np.exp(1j*self.data[3])
				self.y = np.linspace(self.ystart, self.ystop, self.ynpts)
				self.data = np.array(np.split(self.data, self.ynpts))

			elif self.data.shape[0] == 3:# specially adjusted for Qcodes
				self.data = self.data[2]
				self.y = np.linspace(self.ystart, self.ystop, self.ynpts)
				self.data = np.array(np.split(self.data, self.ynpts))

		if dim == 3:
			if self.data.shape[0] == 7:
				# real, imag, abs, phase (HOPEFULLY THIS WON'T CHANGE)
				if np.abs(self.data[3][0]+1j*self.data[4][0] - self.data[5][0]*np.exp(1j*self.data[6][0])) > 1e-10:
					raise Exception('Data is probably not in the format [real, imag, abs, phase]')
				self.data = self.data[5]*np.exp(1j*self.data[6])

			elif self.data.shape[0] == 5:
				# abs, phase (HOPEFULLY THIS WON'T CHANGE)
				self.data = self.data[3]*np.exp(1j*self.data[4])
			self.z = np.linspace(self.zstart, self.zstop, self.znpts)
			self.data = np.array([np.split(d, self.znpts) for d in self.data])

		if dim > 3:
			Exception('Cannot rearrange more than 3 dimensions')

	def read_meta(self, fname):
		meta = open(fname[:-3]+'meta.txt', 'r')
		lines = meta.readlines()
		line = 0
		def next_line(line):
			while lines[line][0] == '#':
				line+=1
			return line
		line = next_line(line)
		self.xnpts = int(lines[line])
		line = next_line(line+1)
		self.xstart = float(lines[line])
		line = next_line(line+1)
		self.xstop = float(lines[line])
		line = next_line(line+1)
		line = next_line(line+1)
		self.ynpts = int(lines[line])
		line = next_line(line+1)
		self.ystart = float(lines[line])
		line = next_line(line+1)
		self.ystop = float(lines[line])
		line = next_line(line+1)
		line = next_line(line+1)
		self.znpts = int(lines[line])
		line = next_line(line+1)
		self.zstart = float(lines[line])
		line = next_line(line+1)
		self.zstop = float(lines[line])
		meta.close()

# x = np.linspace(-6, 6, 100)
# plt.plot(x, np.abs(normalizedComplexRootLorentzian(x, 0, 2)))
# plt.show()
# d = Data(r'D:\data\2018-08-07_JPA\#008_Power Sweep__16-53-40\ZNB_S21_power_set_S21_frequency_set.dat')
# lorentzianFitter = Fitter(invertedLorentzianWithOffset, complex_fit=True)

# mi = lorentzianFitter.fit(d.x, d.data[14])
# save_fit_values
# savefig
# show_plot

# # x0 kappa norm
# value1 value2.. error1 error2