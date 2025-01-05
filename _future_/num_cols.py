import numpy as np

def count_numeric_columns(filepath):
    """
    Counts the number of numeric columns in a file.
    
    Parameters
    ----------
    filepath : str
        Path to the text file.
        
    Returns
    -------
    int
        Number of numeric columns in the file.
    """
    with open(filepath, 'r') as file:
        for line in file:
            if not line.startswith('#') and line.strip():  # Skip header lines and empty lines
                # Split the first data line and count the columns
                num_columns = len(line.split())
                return num_columns
    raise ValueError("No numeric data found in the file.")

# Example usage:
filename = "/Users/vibhor/Library/CloudStorage/OneDrive-IndianInstituteofScience/Data-IISc/Flux coupled with coax cavity/Fig1_part_2 - avoided crossinge etc/104043_perpendicular_field_current_sweep.dat"
num_columns = count_numeric_columns(filename)

print(f"Number of numeric columns: {num_columns}")

# Read specific columns using numpy.loadtxt
# desired_column = 3  # Example: Column 3 (0-indexed for np.loadtxt)
# data = np.loadtxt(filename, comments='#', usecols=desired_column)

# print(f"Data from column {desired_column + 1}:")
# print(data)
