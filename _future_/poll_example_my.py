# from time import time

daq_uhf.setDouble(f'/{device_uhf}/demods/3/rate', 13)
start_t = time()
daq_uhf.subscribe(f'/{device_uhf}/demods/3/sample')
sleep_length = 0.4
sleep(sleep_length)
poll_length = 1 # [s]
poll_timeout = 2000  # [ms]
poll_flags = 0
poll_return_flat_dict = True
data = daq_uhf.poll(poll_length, poll_timeout, poll_flags, poll_return_flat_dict)
daq_uhf.unsubscribe("*")
stop_t = time()
print(stop_t - start_t)

x = data['/dev2232/demods/3/sample']['x']
y = data['/dev2232/demods/3/sample']['y']

plt.plot(y)
print(len(y))


plt.plot(x)
