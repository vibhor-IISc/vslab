# -*- coding: utf-8 -*-
"""
Created on Sat Apr 23 15:38:59 2022

@author: normaluser
"""

import os
from datetime import datetime
import errno
import numpy as np
from glob import glob
from pathlib import Path


from shutil import copy, copy2
import matplotlib.pyplot as plt
import qcodes as qc
from qcodes import initialise_or_create_database_at
from qcodes import load_or_create_experiment


################################################################################################################
'''
These functions are used with vslab based measurement scripts.
Typical structrue is

begin_save()
loop_write()
meta_quick()

'''
###################################

def begin_save(filename='exp_name', device_id = 'sample'):
    '''
    Parameters
    ----------
    exp_name : String
        DESCRIPTION - experiment name.
        The default is 'exp'. Give exp_name like
        rabi, power_rabi, omit, power_sweep, etc.

    device_id : String
        DESCRIPTIONS - A name of the sample. 
        The default is 'sample'

    Returns --> None
    Actions:
    create a date-time directory, and ppath.log to 
    save the data and script later. 

    '''
    filestr =datetime.now().strftime('%Y%m%d_%H%M%S').split('_')
    mydir = os.path.join('D:\\Data', filestr[0]+'_'+device_id, filestr[1]+'_'+filename)
    file2disk = filestr[1]+filename
    try:
        os.makedirs(mydir)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise  # This was not a "directory exist" error..
    
    with open('ppath.log', 'w') as fl:
        fl.write(mydir)

    return mydir, file2disk




def loop_write(data, filename):
    '''
    Parameters
    ----------
    data : Numpy data block
    filename: String

    Returns --> None
    Actions:
    writes the data to disk in .dat format using the path 
    specified by ppath and filename.

    FUTURE: Make filename optional and add support for hdf5

    '''
    filepath = _read_ppath()
    fl = open(filepath+'\\'+filename+'.dat','a+')
    rows = data.shape[0]
    cols = data.shape[1]
    for row in np.arange(rows):
        for col in np.arange(cols):
            fl.write(str(data[row][col])+'\t')
        fl.write('\n')
    fl.close()



def loop_write2(data, filepath):
    '''
    Parameters
    ----------
    data : Numpy data block
    filepath: Full path of the file

    Returns --> None
    Actions:
    writes the data to disk in .dat format using the path 
    specified by ppath and filename.


    '''
    fl = open(filepath,'a+')
    rows = data.shape[0]
    cols = data.shape[1]
    for row in np.arange(rows):
        for col in np.arange(cols):
            fl.write(str(data[row][col])+'\t')
        fl.write('\n')
    fl.close()


def meta_quick(meta_in, meta_out, dims):
    '''
    Parameters
    ----------
    (meta_in, meta_out, dims=1 or 2)

    '''
    _num_ind = dims

    _inner_string = '#Inner\n'+str(int(meta_in[0]))+'\n'+str(meta_in[1])+'\n'+str(meta_in[2])+'\n'+meta_in[3]+'\n'
    if _num_ind == 1:
        _outer_string = '#Outer\n1\n0\n1\nNothing\n'
        _outmost_string = '#Outmost\n1\n0\n1\nNothing\n'
    elif _num_ind == 2:
        _outer_string = '#Outer\n'+str(int(meta_out[0]))+'\n'+str(meta_out[2])+'\n'+str(meta_out[1])+'\n'+meta_out[3]+'\n'
        _outmost_string = '#Outmost\n1\n0\n1\nNothing\n'
    # elif _num_ind == 3:
    #     _outer_string = '#Outer\n'+str(int(_lengths[1]))+'\n'+str(_last_vals[1])+'\n'+str(_first_vals[1])+'\n'+_var_ind[1]+'\n'
    #     _outmost_string = '#Outmost\n'+str(int(_lengths[2]))+'\n'+str(_first_vals[2])+'\n'+str(_last_vals[2])+'\n'+_var_ind[2]+'\n'
    else:
        raise Exception(' Can not create meta file for more than 3 dimensions sweeps')


    filepath = _read_ppath()
    _files = glob(filepath+'\\*.dat')
    for file in _files:
        with open(file[:-4]+'.meta.txt', 'w+') as metafile:
            metafile.write(_inner_string+_outer_string+_outmost_string)
            metafile.write(f'#for each of the values\n{6}\nMeasurement')




#################################################################################################################
#################################################################################################################
'''
These functions are typically used with qcodes style file saving.
The structure in the measurement script should be like:

mstart()
mdata()
mcopy()

'''


def _np_unique(array):
    '''
    Function retruns the unique values in an array 
    without sorting them in ascending order.
    Note that it is different from np.unique()
    '''
    _indices = np.unique(array, return_index=True)[1]
    return [array[index] for index in sorted(_indices)]


def mstart(sample_name, exp_name):
    '''
    
    Parameters
    ----------
    sample_name : String
        DESCRIPTION - sample name
    exp_name : String OPTIONAL
        DESCRIPTION. The default is 'exp'. Give exp_name like
        rabi, power_rabi, omit, power_sweep, etc.

    Returns --> None
    Actions:
        1: initialize_or_create_experiment. It happens everytime.
        2: initialize_or_create_database. It happends once everyday
        3: Config the database to "D:\\database\\"
        4. Save the PPATH info in a temporary file 'ppath.log'
    -------
    '''
    # setting the experiemnt
    
    _date_time = datetime.now()
    _d = _date_time.strftime("%Y%m%d")
    _t = _date_time.strftime("%H%M%S")
    ppath = 'D:\\data\\'+_d+'\\'+_t
    
    initialise_or_create_database_at('D:\\database\\'+_d+'_'+sample_name+'.db')
    qc.config.add("base_location",ppath, 
                  value_type="string", 
                  description="Location of data", 
                  default=ppath)
    ppath_tag = ppath + f'_{exp_name}'
    
    exp = load_or_create_experiment(experiment_name=exp_name,
                                sample_name=sample_name)
    
    with open('ppath.log', 'w') as fl:
        fl.write(ppath_tag)
    pass

def mdata(dataset):
    '''
    Parameters
    ----------
    dataset : "datasaver.dataset"
        First input should be a "dataset"
    
    Returns --> None.
    Actions: 
        1: Save spyview compatible data
        2: create *.meta
    
    '''
    _create_dir_from_ppath()
    
    ppath_tag = _read_ppath()
    # converting from database to ASCII
    dataset.write_data_to_text_file(ppath_tag)
    # Renaming with DATE/Time stamp etc
    _rename_files(ppath_tag, '.dat')
    # creating metagen
    _metagen(dataset, ppath_tag)
    pass

def mcopy(script2copy):
    '''
    Parameters
    ----------
    script2copy : __file__
        DESCRIPTION --> use the __file__  magic dunder to give the full 
        path of the measurement script.

    Returns --> None
    Actions:
        1: read the ppath info from *.log
        2: copy the measurement script to date/time folder
    -------

    '''
    ppath_tag = _read_ppath()
    _create_dir_from_ppath()
    copy2(script2copy, ppath_tag)
    # renaming to give unique time and experiment stamp
    _rename_files(ppath_tag, '.py')
    pass




# def mcopy_NEW(destination_path):
#     """
#     Copies the current script or notebook file to the specified destination path.

#     Parameters:
#         destination_path (str): The destination path where the file should be copied.
#     """
#     try:
#         # Attempt to get the current file name (for .py files)
#         current_file_path = os.path.abspath(__file__)
#     except NameError:
#         # If __file__ is not available (likely a Jupyter Notebook), use ipynbname
#         try:
#             import ipynbname
#             current_file_path = str(ipynbname.path())
#         except ModuleNotFoundError:
#             raise RuntimeError("Unable to determine current file. Ensure you are running from a .py script or install 'ipynbname' for notebooks.")

#     # Ensure the destination directory exists
#     os.makedirs(os.path.dirname(destination_path), exist_ok=True)

#     # Copy the file to the destination
#     shutil.copy(current_file_path, destination_path)
#     print(f"File copied to: {destination_path}")

# # Example usage
# # Provide the path where you want to copy the file (modify as needed)
# destination = "backup/my_copied_file"
# copy_current_file(destination)



def _read_ppath():
    with open('ppath.log','r+') as fl:
        ppath_tag = fl.read()
    return ppath_tag
    

def _create_dir_from_ppath():
    ppath_tag = _read_ppath()
    Path(ppath_tag).mkdir(parents=True, exist_ok=True)
    pass


def _rename_files(ppath_tag, extn):
    _files = glob(ppath_tag+'\\*'+extn)
    _last_dir = ppath_tag.split('\\')[-1]
    for file in _files:
        _new_name = ppath_tag+'\\'+_last_dir+'_'+file.split('\\')[-1]
#        _new_name = _last_dir + file[:-4]+ '.dat'
        os.rename(file, _new_name)


# Array and numeric datatype has been fixed with the function below
#

def _metagen2(dataset, ppath_tag):
    '''
    Parameters
    ----------
    dataset : Dataset from qcodes
    ppath_tag : file info
    '''
    pass



def _metagen(dataset, ppath_tag):
    # ppath is the directory where ASCII data has been saved.
    # Analyzing the structure of the dataset object
    
    _var = dataset.parameters.split(',')
    _total_num = len(_var)
    _num_dep = len(dataset.dependent_parameters)
    _num_ind = _total_num - _num_dep
    
    _var_ind = _var[:_num_ind]
    # following line was added after finding inner/outer
    # loops were getting reversed in the metafile
    # Compatibility with 1D-sweep is not not tested
    _var_ind.reverse()
    #
    _var_dep = _var[_num_ind:]
    
# Getting all information from the datset

    _lengths = []
    for val in _var_ind:
        if dataset.paramspecs[val].type == 'array':
            _len = int(len(_np_unique(dataset.get_parameter_data(val)[val][val][0])))
        elif dataset.paramspecs[val].type == 'numeric':
            _len = int(len(_np_unique(dataset.get_parameter_data(val)[val][val])))
        else:
            raise Exception('Unable to determine the value type')
        
        _lengths = np.append(_lengths, _len)
    
    
    _first_vals = []
    for val in _var_ind:
        if dataset.paramspecs[val].type == 'array':
            _val_first = dataset.get_parameter_data(val)[val][val][0][0]
        elif dataset.paramspecs[val].type == 'numeric':
            _val_first = dataset.get_parameter_data(val)[val][val][0]
        else:
            raise Exception('Unable to determine the value type')
            
        _first_vals = np.append(_first_vals, _val_first)
    
    _last_vals = []
    for val in _var_ind:
        if dataset.paramspecs[val].type == 'array':
            _val_last = dataset.get_parameter_data(val)[val][val][0][-1]
        elif dataset.paramspecs[val].type == 'numeric':
            _val_last = dataset.get_parameter_data(val)[val][val][-1]
        else:
            raise Exception('Unable to determine the value type')

        _last_vals = np.append(_last_vals, _val_last)

#  Structure of the various strings in the meta file

    _inner_string = '#Inner\n'+str(int(_lengths[0]))+'\n'+str(_first_vals[0])+'\n'+str(_last_vals[0])+'\n'+_var_ind[0]+'\n'
    if _num_ind == 1:
        _outer_string = '#Outer\n1\n0\n1\nNothing\n'
        _outmost_string = '#Outmost\n1\n0\n1\nNothing\n'
    elif _num_ind == 2:
        _outer_string = '#Outer\n'+str(int(_lengths[1]))+'\n'+str(_last_vals[1])+'\n'+str(_first_vals[1])+'\n'+_var_ind[1]+'\n'
        _outmost_string = '#Outmost\n1\n0\n1\nNothing\n'
    elif _num_ind == 3:
        _outer_string = '#Outer\n'+str(int(_lengths[1]))+'\n'+str(_last_vals[1])+'\n'+str(_first_vals[1])+'\n'+_var_ind[1]+'\n'
        _outmost_string = '#Outmost\n'+str(int(_lengths[2]))+'\n'+str(_first_vals[2])+'\n'+str(_last_vals[2])+'\n'+_var_ind[2]+'\n'
    else:
        raise Exception(' Can not create meta file for more than 3 dimensions sweeps')
    
    # Reading att the *.dat files and create .meta.txt for each.

    _files = glob(ppath_tag+'\\*.dat')
    for file in _files:
        with open(file[:-4]+'.meta.txt', 'w+') as metafile:
            metafile.write(_inner_string+_outer_string+_outmost_string)
            metafile.write(f'#for each of the values\n{len(_var_ind)+1}\nMeasurement')



