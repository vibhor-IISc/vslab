# -*- coding: utf-8 -*-
"""
Created on Thu May 22 16:16:08 2025

@author: user
"""

# -*- coding: utf-8 -*-
"""
Created on Thu Mar 27 10:45:39 2025

@author: user
"""

from vslab.analysis.data import Data2D
from vslab.analysis.fitter import Fitter
from vslab.fileio import loop_write2
import matplotlib.pyplot as plt
import numpy as np
from glob import glob

key = 7
paths = glob(rf'E:\Downloads\20250523\*{key}*')



for ix in np.arange(6):

    path = paths[ix]
    print(path)
    d = Data2D(path)
    
    xdata = d.X
    pw = d.Y
    da = d.Z(2)
    
    ki= []
    kierr = []
    
    for idx, val in enumerate(pw):
        ydata = da[idx]
        fitter = Fitter("S21sideComplex")
        result = fitter.fit(xdata, ydata)
        fitter.saveplot(path+'\\fit_figs'+'\\S21side_'+str(idx).zfill(2)+'.png')
        plt.clf()
        k = result.params['k'].value
        k_err = result.params['k'].stderr
        ke = result.params['ke'].value
        ke_err = result.params['ke'].stderr
        phi = result.params['phi'].value
        phi_err = result.params['phi'].stderr
        
        # Computing ki
        ki.append(np.abs(np.abs(k) - np.abs(ke)*np.abs(np.cos(phi))))
        # Computing ki error
        ki_err = k_err+ke_err*np.cos(phi) + np.abs(ke)*np.sin(phi_err)
        print(ki_err)
        kierr.append(ki_err)
    
    data = np.array(list(zip(pw, ki, kierr)))
    loop_write2(data, path+'\\fit_figs'+f'\\result_{key}_'+str(ix)+'.dat')
    
    plt.clf()
    
    plt.errorbar(np.flip(pw), ki, kierr, 
                 marker = 's',
                 markersize=5,
                 markerfacecolor='black',
                 ecolor='grey',
                 capsize=3,
                 elinewidth=1)
    
    plt.xlabel('power [dBm]')
    plt.ylabel('ki [Hz]')
    plt.tight_layout()
    plt.title(path.split('\\')[-1])
    plt.savefig(path+'\\fit_figs'+f'\\S21side_Power{ix}.png')
plt.clf()    
    

