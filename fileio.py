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
from typing import Sequence, Optional, Any, List
from shutil import copy, copy2
import matplotlib.pyplot as plt

from qcodes import initialise_or_create_database_at
from qcodes import load_or_create_experiment
from qcodes import config


################################################################################################################
'''
These functions are used with vslab based measurement scripts.
Typical structrue is

begin_save()
loop_write()
mcopy()
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
    GIVES a warning if file already exists and append the data. 
    It will NEVER over-write existing file. 
    '''
    if os.path.exists(filepath):  # Check if file already exists
        print(f"SERIOUS Warning: '{filepath}' already exists!")
    
    with open(filepath, 'a+') as fl:  # Use 'a+' mode to append data
        rows, cols = data.shape
        
        for row in range(rows):
            for col in range(cols):
                fl.write(str(data[row][col]) + '\t')
            fl.write('\n')

# Example Usage
# data = np.array([[1, 2, 3], [4, 5, 6]])
# loop_write2(data, "output.txt")

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
##  This part of the codes in under testing
# Attempt to made - meta_quick.py - as universal writer



def _loop_to_meta(l: Any) -> list:
    """
    Convert a 'loop'-like object to the meta-list format expected by meta_quick_list:
       [n_points (int), first_val, last_val, name_str]
    Uses l.to_list() if available to avoid re-implementing step/endpoint logic.
    """
    # Get iterable values
    if hasattr(l, "to_list") and callable(getattr(l, "to_list")):
        vals = l.to_list()
    else:
        # last resort: exhaust the iterator (works for most iterables)
        vals = list(iter(l))

    n = len(vals)
    if n == 0:
        # fallback: use start/stop attributes if available
        first = getattr(l, "start", 0)
        last = getattr(l, "stop", first)
    else:
        first = vals[0]
        last = vals[-1]

    name = getattr(l, "name", None)
    # ensure a string for name (original code used 'Nothing' in some places)
    name = str(name) if name is not None else "Nothing"

    return [n, first, last, name]


def meta_quick_list(meta_in: Sequence, meta_out: Optional[Sequence], dims: int = 1, ppath: Optional[str] = None) -> List[str]:
    """
    Backwards-compatible implementation of your original meta_quick.
    Parameters
    ----------
    meta_in : sequence-like
        Expecting [n_points, first, last, name] (like your previous meta_in)
    meta_out : sequence-like or None
        Same format as meta_in but for the outer loop (only used if dims==2)
    dims : int
        1 or 2 (the function raises if dims > 2)
    ppath : str or None
        Path to search for .dat files (defaults to cwd or _read_ppath()).
    Returns
    -------
    List[str] -- list of file paths written
    """
    _num_ind = int(dims)
    if _num_ind not in (1, 2):
        raise Exception(' Can not create meta file for more than 2 dimensions sweeps')

    # Build inner string (preserve original ordering / behaviour)
    _inner_string = '#Inner\n' + str(int(meta_in[0])) + '\n' + str(meta_in[1]) + '\n' + str(meta_in[2]) + '\n' + str(meta_in[3]) + '\n'

    if _num_ind == 1:
        _outer_string = '#Outer\n1\n0\n1\nNothing\n'
        _outmost_string = '#Outmost\n1\n0\n1\nNothing\n'
    else:  # dims == 2
        # NOTE: preserve original code's ordering for outer (meta_out[2], meta_out[1]) for compatibility
        _outer_string = '#Outer\n' + str(int(meta_out[0])) + '\n' + str(meta_out[2]) + '\n' + str(meta_out[1]) + '\n' + str(meta_out[3]) + '\n'
        _outmost_string = '#Outmost\n1\n0\n1\nNothing\n'

    if ppath is None:
        filepath = _read_ppath()
    else:
        filepath = ppath

    # Use glob to find .dat files
    _files = glob(os.path.join(filepath, '*.dat'))
    written_files = []
    for file in _files:
        outname = file[:-4] + '.meta.txt'  # strip .dat and append .meta.txt
        with open(outname, 'w+') as metafile:
            metafile.write(_inner_string + _outer_string + _outmost_string)
            metafile.write(f'#for each of the values\n{6}\nMeasurement\n')
        written_files.append(outname)

    return written_files


def meta_quick_loop(loop_in: Any, loop_out: Optional[Any] = None, dims: Optional[int] = None, ppath: Optional[str] = None) -> List[str]:
    """
    Create meta files from loop-like objects. Converts loops to meta-lists and calls meta_quick_list.

    Parameters:
        loop_in, loop_out : loop-like objects (must be iterable or have to_list()/start/stop)
        dims : if provided, will be used; otherwise inferred (2 if loop_out given, else 1)
    """
    inferred_dims = 2 if loop_out is not None else 1
    _dims = inferred_dims if dims is None else int(dims)

    meta_in = _loop_to_meta(loop_in)
    meta_out = _loop_to_meta(loop_out) if loop_out is not None else None

    return meta_quick_list(meta_in, meta_out, dims=_dims, ppath=ppath)


def meta_quick(*args, dims: Optional[int] = None, ppath: Optional[str] = None) -> List[str]:
    """
    Dispatcher function:
      - meta_quick(meta_in_list, meta_out_list, dims)  -> calls meta_quick_list
      - meta_quick(loop_in, loop_out)                 -> calls meta_quick_loop
    Returns list of written file paths.

    Examples:
      meta_quick([10, 0, 9, 'X'], [5, 0, 4, 'Y'], 2)
      meta_quick(loop1, loop2)
    """
    # Two args -> treat as loop objects if they look like loops
    if len(args) == 2:
        a, b = args
        is_loop_a = hasattr(a, 'start') and hasattr(a, 'stop')
        is_loop_b = hasattr(b, 'start') and hasattr(b, 'stop')
        if is_loop_a and is_loop_b:
            return meta_quick_loop(a, b, dims=dims, ppath=ppath)
        # fallback: maybe user supplied meta lists without dims; treat as lists with dims=2
        if isinstance(a, Sequence) and isinstance(b, Sequence):
            _dims = 2 if dims is None else int(dims)
            return meta_quick_list(a, b, dims=_dims, ppath=ppath)

    # Three args: assume (meta_in_list, meta_out_list, dims)
    if len(args) == 3:
        meta_in, meta_out, _dims = args
        if not isinstance(_dims, int):
            raise TypeError("Third argument (dims) must be an int (1 or 2).")
        return meta_quick_list(meta_in, meta_out, dims=_dims, ppath=ppath)

    raise TypeError("Invalid arguments. Use either:\n"
                    "  meta_quick(meta_in_list, meta_out_list, dims)\n"
                    "  meta_quick(loop_in, loop_out)")

# If you want a convenience alias for the old name:
meta_quick_list.__doc__ = "Use meta_quick_list(meta_in, meta_out, dims) to keep old behaviour."











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
    config.add("base_location",ppath,
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
        os.rename(file, _new_name)



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



##################################
# 14-Dec-2025 UPDATE


from qcodes.instrument.base import Instrument

def close_all_instruments():
    Instrument.close_all()