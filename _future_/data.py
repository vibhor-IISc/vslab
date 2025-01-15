import os
import numpy as np
import xarray as xr

class Data2D:
    def __init__(self, directory):
        if not os.path.isdir(directory):
            raise ValueError(f"The provided path '{directory}' is not a valid directory.")
        
        self.directory = directory
        self.data_file = {}
        self.meta_data = {}
        self.X = {}
        self.Y = {}
        self.numeric_columns = {}
        self.num_data_columns = {}
        self._load_metadata_and_columns()
        self._X()
        self._Y()


    def _load_metadata_and_columns(self):
        """
        Private method to parse metadata files and count numeric columns in .dat files.

        Raises
        ------
        ValueError
            If there are multiple `.dat` or `.meta.txt` files in the directory.
        """
        dat_files = [f for f in os.listdir(self.directory) if f.endswith(".dat")]
        meta_files = [f for f in os.listdir(self.directory) if f.endswith(".meta.txt")]

        # Check for multiple files
        if len(dat_files) > 1:
            raise ValueError(f"Multiple .dat files found: {dat_files}. Expected only one.")
        if len(meta_files) > 1:
            raise ValueError(f"Multiple .meta.txt files found: {meta_files}. Expected only one.")
        if not dat_files:
            raise FileNotFoundError("No .dat file found in the directory.")
        if not meta_files:
            raise FileNotFoundError("No .meta.txt file found in the directory.")

        # Process single .meta.txt file
        meta_file = os.path.join(self.directory, meta_files[0])
        self.meta_data = self._parse_meta_file(meta_file)

        # Process single .dat file
        self.data_file = os.path.join(self.directory, dat_files[0])
        self.numeric_columns = self._count_numeric_columns(self.data_file)
        self.num_data_columns = self.numeric_columns - 2


    def _parse_meta_file(self, filepath):
        with open(filepath, 'r') as file:
            lines = [line.strip() for line in file if not line.startswith('#') and line.strip()]
        
        meta_in = [
            int(lines[0]), float(lines[1]), float(lines[2]), lines[3]
        ]
        if len(lines) > 4:
            dims = 2
            meta_out = [
                int(lines[4]), float(lines[5]), float(lines[6]), lines[7]
            ]
        else:
            dims = 1
            meta_out = []
        
        return meta_in, meta_out, dims

    def _count_numeric_columns(self, filepath):
        with open(filepath, 'r') as file:
            for line in file:
                if not line.startswith('#') and line.strip():
                    return len(line.split())
        raise ValueError("No numeric data found in the file.")

    def get_meta_data(self):
        return self.meta_data

    def get_numeric_columns(self):
        return self.numeric_columns
    
    def get_num_data_columns(self):
        return self.num_data_columns

    def _Y(self):
        meta_in, _, _ = self.meta_data
        npts, start, stop = meta_in[:3]
        self.X = np.linspace(start, stop, npts)
        

    def _X(self):
        _, meta_out, _ = self.meta_data
        npts, start, stop = meta_out[:3]
        self.Y = np.linspace(start, stop, npts)
    
    def read_column(self, column_index, **kwargs):
        """
        Reads a specific column from the .dat file and rearranges 
        it to the size (len(inner_loop), len(outer_loop)).
    
        Parameters
        ----------
        column_index : int
            The index of the column to read (0-based).
        **kwargs : dict
            Additional keyword arguments to pass to np.loadtxt, such as `delimiter`, `unpack`, etc.
    
        Returns
        -------
        numpy.ndarray
            The rearranged array of size (len(inner_loop), len(outer_loop)).
        """
        
        if not (0 <= column_index <  self.numeric_columns):
            raise ValueError(f"Invalid column index {column_index}. Must be between 0 and {self.num_data_columns - 1}.")


    
        # Extract inner and outer dimensions from metadata
        meta_in, meta_out, dims = self.meta_data
        inner_npts = len(self.X)
        outer_npts = len(self.Y)
    

        data = np.loadtxt(self.data_file, usecols=[column_index], **kwargs)
    
        # Ensure data size matches the expected size
        if len(data) != inner_npts * outer_npts:
            raise ValueError(f"Data size {len(data)} does not match the expected size {inner_npts * outer_npts}.")
    
        # Rearrange data to (len(inner_loop), len(outer_loop))
        return data.reshape((outer_npts, inner_npts))
    
    def Z(self, column_index, **kwargs):
        return self.read_column(column_index, **kwargs)
    
    
    
    
def SaveNpy(dir_path):
    '''
    Parameters
    ----------
    dir_path : directoty where .dat and .meta.txt file lives.

    Returns
    -------
    Save X, Y, all Z columns in numpy arrays in the same directory
    
    In future we should update a new function, which saves
    everthing in more managable binary container like xarray
    Numpy arrays have fixed size issue, and any other approach
    in my opinion will never be as fast. 

    '''
    
    d = Data2D(dir_path)
    
    # Saving X array
    filename_x = d.data_file[:-4]+'_X1'+'.npy'
    np.save(filename_x, d.X)
    
    # Saving Y array
    filename_y = d.data_file[:-4]+'_Y2'+'.npy'
    np.save(filename_y, d.Y)
    
    # Saving Z arrays
    for i in np.arange(d.num_data_columns):
        filename = d.data_file[:-4]+f'_Z{i+2}'+'.npy'
        np.save(filename, d.Z(2+i))
    
    print('All .npy files written to disk.')
    pass

    


def SaveHD5(dir_path):
    '''

    Parameters
    ----------
    dir_path : directoty where .dat and .meta.txt file lives.

    Returns
    -------
    Reoranize the .dat file into a .h5 file with all Z columns, and Coordinates
    
    In future we shd update the coord names from meta. 

    '''
    d = Data2D(dir_path)
    
    # Combining different Z columns
    data_vars = {}
    for i in np.arange(d.num_data_columns):
        data_vars[f"Z{2+i}"] = (["Y", "X"], d.Z(2+i))
        
    # Creating a Xarray dataset with coordinates
    ds = xr.Dataset(data_vars, coords = {"Y": d.Y, "X": d.X})
    
    # Writing the Dataset to disk using h5 format
    file_name = d.data_file[:-4]+'.h5'
    ds.to_netcdf(file_name, engine="h5netcdf")
    print('.h5 written to disk.')
    pass














