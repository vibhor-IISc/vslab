import numpy as np
import matplotlib.pyplot as plt


class Oscillator:
    def __init__(self, osc_freq=0.075, amp=1, ssb_phase=90,q_ratio=1,sample_rate=2.4, IQ= 'cos'):
        '''
        
        Initialize an Oscillator:
        osc_freq = IF freq in GHz
        ssb_phase in degree
        q_ratio
        sample_rate = 2.4 GHz
        IQ = {'cos', 'sin'}

        '''

        self.osc_freq = osc_freq
        self.amp = amp
        self.q_ratio = q_ratio
        self.ssb_phase = ssb_phase
        self.samp_rate = sample_rate
        self.IQ = IQ

    def modulate(self, gate_seq):
        sq = []
        for gate in gate_seq:
            sq = np.append(sq, gate.samples)

        tfinal = np.arange(len(sq))
        
        osc1X = np.cos(2*np.pi*self.osc_freq*tfinal/self.samp_rate)
        osc1Y = self.q_ratio*np.sin(2*np.pi*self.osc_freq*tfinal/self.samp_rate)
        
        osc1X_ssb = np.cos(2*np.pi*self.osc_freq*tfinal/self.samp_rate + self.ssb_phase*np.pi/180)
        osc1Y_ssb = self.q_ratio*np.sin(2*np.pi*self.osc_freq*tfinal/self.samp_rate + self.ssb_phase*np.pi/180)

        sqi = np.real(sq)
        sqq = np.imag(sq)

        return [sqi*osc1X + sqq*osc1Y, sqi*osc1X_ssb + sqq*osc1Y_ssb]


class Gate():
    def __init__(self, shape, gate_length=256, amp=1, t0=0,sigma=256/2.66, IQ='cos', user_path="C:\\temp.txt"):
        self.shape = shape
        self.gate_length = gate_length
        self.amp = amp
        self.sigma = sigma
        self.t0 = t0
        self.IQ = IQ
        self.user_path = user_path
        self.samples = self.get_samples()


    valid_shapes = np.array(['gauss', 'id', 'user'])

    def gauss(self):
        t = np.arange(self.gate_length)
        t0 = self.gate_length/2
        sigma = self.sigma
        return np.exp(-0.5*((t-t0)/sigma)**2)

    def gauss2(self):
        t = np.arange(self.gate_length)
        sigma = self.sigma
        t0 = self.t0
        return np.exp(-0.5*((t-t0)/sigma)**2)

    def get_samples(self):
        
        quad = (int(self.IQ=='cos')+ int(self.IQ=='sin')*1j)

        if self.shape == 'gauss':
            return self.amp*self.gauss()*quad
        elif self.shape == 'rect':
            return self.amp*np.ones(self.gate_length)*quad
        elif self.shape == 'id':
            return np.zeros(self.gate_length)*quad
        elif self.shape == 'user':
            shape = np.loadtxt(self.user_path, unpack=True)
            return shape*quad
        else:
            raise Exception('Valid shapes are: gauss, rect, id, and user')    

def append_gate(gate_list):
    sq = []
    for gate in gate_list:
        sq = np.append(sq, gate.get_samples())
    return sq

def wave_add(*args):
    if not args:
        return None  # Return None if no arguments are provided
    
    arrays = [np.array(arg) for arg in args]
    result = sum(arrays)
    result_list = result.tolist()
    return result_list

def gate_plotter(gate_seq):
    '''
    Plots waves which can be passed as list of lists:
    '''
    fig, axs = plt.subplots(len(gate_seq), 1, figsize = (5, 2*len(gate_seq)))
    for idx, ax in enumerate(axs):
        ax.plot(np.real(append_gate(gate_seq[idx])), label='cos')
        ax.plot(np.imag(append_gate(gate_seq[idx])), label='sin')
        ax.legend()
        ax.set_ylim(-1.2,1.2)

    plt.tight_layout()
    plt.show()


def wave_plotter(waves):
    '''
    Plots waves which can be passed as list of lists:
    '''

    fig, axs = plt.subplots(len(waves), 1, figsize = (5, 2*len(gate_seq)))
    for idx, ax in enumerate(axs):
        ax.plot(waves[idx][0])
        ax.set_ylim(-1.2,1.2)

    plt.tight_layout()
    plt.show()

def write_waves1(waves_pack, name):
    '''
    args: (waves as list of lists, filename)
    Return : Write the files to disk
    '''
    [ch1, ch2] = waves_pack # unpacking
    _path = r'C:\Users\normaluser\Documents\Zurich Instruments\LabOne\WebServer\awg\waves'
    np.savetxt(_path+'/' + name+'_temp.txt',np.stack((ch1,ch2), axis=1), fmt = '%.6f')
     # write to file
    return [ch1, ch2]

def write_waves(waves_pack, name = '_temp'):
    '''
    args: (waves as list of lists, filename)
    Return : Write the files to disk
    '''
    [ch1, ch2] = waves_pack # unpacking
    _path = r'C:\Users\normaluser\Documents\Zurich Instruments\LabOne\WebServer\awg\waves'
    np.savetxt(_path+'/'+name+'.txt',np.stack((ch1,ch2), axis=1), fmt = '%.6f')
    # write to file
    return [ch1, ch2]





idd = Gate('id')
rx90 = Gate('gauss', IQ='cos')
ry90 = Gate('gauss', IQ='sin')
stp_s = Gate('id')
stp_p = Gate('gauss', IQ='cos')

# rec = Gate('rect') + Gate('gauss')


gate_seq1 = [rx90, idd, idd, stp_p]
gate_seq2 = [idd, idd, stp_s, ry90]


t1 = Oscillator(osc_freq=0.075)
t2 = Oscillator(osc_freq = 0.100)


wave1 = t1.modulate(gate_seq1)
wave2 = t2.modulate(gate_seq2)

gate_seq = [gate_seq1, gate_seq2]

gate_plotter(gate_seq)
wave_plotter([wave1,wave2])

plt.plot(wave_add(wave1,wave2)[0])
plt.show()

# print(rx90.samples)
















