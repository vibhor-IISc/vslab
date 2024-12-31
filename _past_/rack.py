## Addresses of different instruments
# Our convention
# 10-series for VNAs and SA
# 20-series is for microwave signal generator
# 30-series if for AWGs


from qcodes.instrument.base import Instrument

def close_all_instruments():
	Instrument.close_all()

SEQUENCER_ADDRESS = r'C:\Users\normaluser\Documents\Zurich Instruments\LabOne\WebServer\awg\src'
ZNB_ADDRESS = "TCPIP0::192.168.1.3::inst0::INSTR"
ZNB6_ADDRESS = "TCPIP0::192.168.1.52::inst0::INSTR"
HDAWG_ADDRESS ="dev8351"  # IP Address for AWG1 = 192.168.1.31
UHF_ADDRESS ="dev2232"
FSV_ADDRESS = "TCPIP0::192.168.1.8::inst0::INSTR"
ZVL_ADDRESS = "TCPIP0::192.168.1.9::inst0::INSTR"
SG1_ADDRESS = "TCPIP0::192.168.1.21::inst0::INSTR"
SG2_ADDRESS = "TCPIP0::192.168.1.22::inst0::INSTR"
APSYN_ADDRESS = "TCPIP0::192.168.1.7::inst0::INSTR"
SMF_ADDRESS = "TCPIP0::192.168.1.4::inst0::INSTR"
RTE_ADDRESS = 'TCPIP0::192.168.1.6::inst0::INSTR'
GS820_ADDRESS = 'TCPIP0::192.168.1.19::inst0::INSTR'
SGS_ADDRESS = "TCPIP0::192.168.0.100::inst0::INSTR"  #"TCPIP0::169.254.2.20::inst0::INSTR"



# __loc = locals()
# _instrument_list = ['vna','hdawg','uhf','sg1','sg2','aps','sa', 'dac', 'dmm']


# def build_rack(ins_list):
#     '''
#     Parameters
#     ----------
#     ins_list:
#         DESCRIPTION-> Use an input like ['sa', 'vna', 'sg1'].
#     Returns:
#         DESCRIPTION-> list of inst handles like [sa, vna, sg1]
#     Raises Exception ---> if the input is a subset of pre-defined names.
    
#     Manintainence:
#         The helper file rack.py needs to updated everytime a 
#         new purchased equipment is added to the network.
        
#     -------

#     '''
#     if set(ins_list).issubset(set(_instrument_list)):
#         ins_rack = []
#         for instrument in ins_list:
#             if instrument == 'vna':
#                 global vna
#                 try:
#                     _name = vna.ask('*IDN?')
#                     print(f'Instrument already exist: skipping...{_name}')
#                 except NameError:
#                     from qcodes.instrument_drivers.rohde_schwarz.ZNB import ZNB
#                     vna = ZNB('ZNB20', ZNB_ADDRESS)
                
#             elif instrument == 'hdawg':
#                 global hdawg
#                 try:
#                     _name = hdawg.ask('*IDN?')
#                     print(f'Instrument already exist: skipping...{_name}')
#                 except NameError:
#                     import zhinst.qcodes as zi
#                     hdawg = zi.HDAWG('hdawg', address = HDAWG_ADDRESS)

#             elif instrument == 'uhf':
#                 global uhf
#                 try:
#                     _name = uhf.ask('*IDN?')
#                     print(f'Instrument already exist: skipping...{_name}')
#                 except NameError:
#                     import zhinst.qcodes as zi
#                     uhf = zi.UHFLI('uhf', address = UHF_ADDRESS)
                
#             elif instrument == 'sg1':
#                 global sg1
#                 try:
#                     _name = sg1.ask('*IDN?')
#                     print(f'Instrument already exist: skipping...{_name}')
#                 except NameError:
#                     from qcodes.instrument_drivers.stanford_research.SG396 import SRS_SG396
#                     sg1 = SRS_SG396('sg1', address = SG1_ADDRESS)

#             elif instrument == 'sg2':
#                 global sg2
#                 try:
#                     _name = sg2.ask('*IDN?')
#                     print(f'Instrument already exist: skipping...{_name}')
#                 except NameError:
#                     from qcodes.instrument_drivers.stanford_research.SG396 import SRS_SG396
#                     sg2 = SRS_SG396('sg2', address = SG2_ADDRESS)
            
#             elif instrument == 'aps':
#                 global aps
#                 try:
#                     _name = aps.ask('*IDN?')
#                     print(f'Instrument already exist: skipping...{_name}')
#                 except NameError:
#                     from qcodes.instrument_drivers.Anapico.APSYN420 import APSYN420
#                     aps = APSYN420('aps', address = APSYN_ADDRESS)
#                     ins_rack.append(aps)

#             elif instrument == 'sa':
#                 global sa
#                 try:
#                     _name = sa.ask('*IDN?')
#                     print(f'Instrument already exist: skipping...{_name}')
#                 except NameError:
#                     from qcodes.instrument_drivers.rohde_schwarz.FSV13_2 import FSV13_2
#                     sa = FSV13_2('sa', address = FSV_ADDRESS)
#                     ins_rack.append(sa)
                
#             elif instrument =='dac':
#                 global dac
#                 try:
#                     __loc['dac']
#                     print('dac already exist: skipping...')
#                 except KeyError:
#                     from qcodes.tests.instrument_mocks import DummyInstrument
#                     dac = DummyInstrument('dac', gates=['ch1', 'ch2'])
                
#             elif instrument == 'dmm':
#                 global dmm
#                 try:
#                     __loc['dmm']
#                     print(f'dmm already exist: skipping...{_name}')
#                 except KeyError:
#                     from qcodes.tests.instrument_mocks import DummyInstrumentWithMeasurement
#                     dmm = DummyInstrumentWithMeasurement('dmm', setter_instr=dac)
                
#             else:
#                 raise Exception('Unknown Instrument: Update rack routine')
#         return ins_rack
#     else:
#         raise Exception('Check the instrument names OR Update rack routine')
#     pass
    
