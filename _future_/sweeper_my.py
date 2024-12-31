# -*- coding: utf-8 -*-
"""
Created on Sat Jun 18 14:37:42 2022

@author: normaluser
"""

import time
import numpy as np
import zhinst.utils
import matplotlib.pyplot as plt
from zhinst.utils import create_api_session, api_server_version_check
from vslab.constants import *
from vslab.rack import *
close_all_instruments()


(daq_uhf, device_uhf, _) = create_api_session(UHF_ADDRESS, 6)
api_server_version_check(daq_uhf)

daq_uhf.sync()


sweeper = daq_uhf.sweep()

sweeper.set("device", device_uhf)

sweeper.set("gridnode", "oscs/3/freq")
sweeper.set("start", 45e6)
sweeper.set("stop", 50e6)
sweeper.set("samplecount", 500)
sweeper.set("xmapping", 0)
sweeper.set("scan", 0)
sweeper.set("loopcount", 1)



# sweeper.set("bandwidthcontrol", 0)
# sweeper.set("settling/time", 0.001)
# sweeper.set("settling/inaccuracy", 0.001)
# sweeper.set("averaging/tc", 5)
# sweeper.set("averaging/sample", 10)
# sweeper.set("averaging/time", 0.001)


sweeper.set("order", 4)
# sweeper.set("averaging/time", 0.1)
# sweeper.set("maxbandwidth", 1000)
sweeper.set("omegasuppression",60)

# daq_uhf.setDouble("/dev2232/demods/3/timeconstant", 0.001)


sweeper.subscribe('/dev2232/demods/3/sample')
flat_dictionary_key = True


# sweeper.set("save/filename", "sweep_with_save")
# sweeper.set("save/fileformat", "csv")

sweeper.execute()

start = time.time()
while True:
    test = sweeper.finished()
    # print(test)
    if test:
        data = sweeper.read(True)
        xx = data['/dev2232/demods/3/sample'][0][0]['x']
        yy = data['/dev2232/demods/3/sample'][0][0]['y']
        plt.plot(np.sqrt(xx**2+yy**2))
        stop = time.time()
        print(stop-start)
        break
    else:
        # print('waiting ...')
        time.sleep(1)
    

















