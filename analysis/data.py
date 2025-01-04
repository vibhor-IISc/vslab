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