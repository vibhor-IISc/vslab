def parse_meta_file(meta_filepath):
    """
    Reads a .meta.txt file and extracts meta_in, meta_out, and dims values.

    Parameters
    ----------
    meta_filepath : str
        Path to the .meta.txt file.

    Returns
    -------
    tuple
        (meta_in, meta_out, dims) where:
        - meta_in is a list of inner meta values [length, first, last, variable].
        - meta_out is a list of outer meta values [length, last, first, variable].
        - dims is an integer indicating the dimensionality (1 or 2).
    """
    with open(meta_filepath, 'r') as metafile:
        lines = [line.strip() for line in metafile if not line.startswith('#') and line.strip()]

    # Initialize variables
    meta_in = []
    meta_out = []
    dims = 1  # Assume 1D by default

    # Read meta_in values (first four values in sequence)
    meta_in = [
        int(lines[0]),   # length
        float(lines[1]), # first
        float(lines[2]), # last
        lines[3]         # variable
    ]

    # Check if more values exist for meta_out (2D case)
    if len(lines) > 4:
        dims = 2  # Update to 2D since outer meta exists
        meta_out = [
            int(lines[4]),   # length
            float(lines[5]), # last
            float(lines[6]), # first
            lines[7]         # variable
        ]

    return meta_in, meta_out, dims


# Example usage
meta_file_path = "/Users/vibhor/Library/CloudStorage/OneDrive-IndianInstituteofScience/Data-IISc/Flux coupled with coax cavity/Fig1_part_2 - avoided crossinge etc/104043_perpendicular_field_current_sweep.meta.txt"  # Replace with the actual file path
try:
    meta_in, meta_out, dims = parse_meta_file(meta_file_path)
    print("meta_in:", meta_in)
    print("meta_out:", meta_out)
    print("dims:", dims)
except FileNotFoundError:
    print(f"File not found: {meta_file_path}")
except Exception as e:
    print(f"Error parsing meta file: {e}")
