
from vslab.analysis.fitter2 import Fitter
from vslab.analysis.data import Data2D
import numpy as np
import matplotlib.pyplot as plt

path = '/Users/vibhor/Downloads/daa'


MHz = 1e6; GHz = 1e9;

resonator_list = [592.4*MHz, 
                  3.351958*GHz, 
                  4.052902*GHz, 
                  4.754020*GHz, 
                  5.455336*GHz, 
                  6.156110*GHz,
                  6.857500*GHz,
                  7.559713*GHz,
                  8.261530*GHz,
                  8.964630*GHz,
                  10.36900*GHz]


da = Data2D(path)

xdata = da.X + resonator_list[0]
power = np.flip(da.Y)

for idx, pw in enumerate(power):
    ft = Fitter('S21sideComplex')
    ydata = da.Z(2)[idx]
    ft.fit(xdata, ydata, save=True, 
           filename=path+'/fit_results/fit', 
           file_index=idx)



from glob import glob
files = sorted(glob(path+'/fit_results/fit*.npz'))

from vslab.analysis.fitter2 import post_process
res = post_process(files)

plt.errorbar(power, res['x0'], res['err_x0'])


plt.errorbar(power, res['k'], res['err_k'])

    









