import pyart
import numpy as np

# 1. Load the raw polar volume ODIM HDF5 file
radar = pyart.aux_io.read_odim_h5('40_20260924_180000.pvol.h5')

# 2. Check the available field keys in your file
print("Available fields:", radar.fields.keys())
# Usually named 'cross_correlation_coefficient', 'rhohv', or 'RHOHV'

# 3. Extract the correlation coefficient array and reflectivity
# Replace 'cross_correlation_coefficient' with your exact key if different
rhohv_field = 'cross_correlation_coefficient' 
rhohv_data = radar.fields[rhohv_field]['data']
reflectivity_data = radar.fields['reflectivity']['data']

# 4. Filter data matching your threshold (e.g., exactly 0.77, or a threshold mask)
# Example A: Extracting exact indices where coefficient is close to 0.77
matching_indices = np.where(np.isclose(rhohv_data, 0.77, atol=0.01))

# Example B: Mask out non-meteorological clutter using 0.77 as a baseline threshold
filtered_reflectivity = np.ma.masked_where(rhohv_data < 0.77, reflectivity_data)

print(f"Found {len(matching_indices[0])} data bins matching coefficient ~0.77")
