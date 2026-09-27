import pyart
import numpy as np

# 1. Load the raw polar volume ODIM HDF5 file
radar = pyart.aux_io.read_odim_h5('40_20260924_180000.pvol.h5')

# 2. Extract arrays using your exact file keys
reflectivity_data = radar.fields['reflectivity_horizontal']['data']
velocity_data = radar.fields['velocity_horizontal']['data']
total_power_data = radar.fields['total_power_horizontal']['data']

# 3. Define your biological threshold (e.g., 10.0 dBZ for the mass swarm footprint)
target_threshold = 10.0

# 4. Find valid data indices that match or exceed your threshold
# (Filters out masked values and NaNs)
matching_bins = np.where(
    (~reflectivity_data.mask) & 
    (~np.isnan(reflectivity_data)) & 
    (reflectivity_data >= target_threshold)
)

# 5. Extract values within the swarm envelope
swarm_reflectivity = reflectivity_data[matching_bins]
swarm_velocity = velocity_data[matching_bins]

# The difference between total power and clean horizontal reflectivity 
# can highlight static ground clutter vs active moving biology
clutter_signal = total_power_data - reflectivity_data
# Create a mask for high clutter areas (static terrain)
terrain_mask = clutter_signal > 15.0

# Clean your reflectivity data to leave pure biological/atmospheric returns
clean_biological_ref = np.ma.masked_where(terrain_mask, reflectivity_data)
# Identify bins where biology dominates: high reflectivity but zero terrain filtering
pure_moth_bins = np.where(
    (reflectivity_data >= 10.0) & 
    (clutter_signal <= 2.0) & 
    (~reflectivity_data.mask)
)

moth_only_reflectivity = reflectivity_data[pure_moth_bins]
# Refined extraction: 
# 1. Target must be above your biological tracking threshold (10 dBZ)
# 2. Clutter signal must be low (< 3 dB) to ensure it's not a ridge-line or hill
moth_bins = np.where(
    (~reflectivity_data.mask) &
    (reflectivity_data >= 10.0) &
    (clutter_signal < 3.0)
)


print(f"Number of radar bins tracking swarm (>= {target_threshold} dBZ): {len(matching_bins[0]):,}")
print(f"Average reflectivity of the swarm system: {np.mean(swarm_reflectivity):.2f} dBZ")
print(f"Max travel velocity of targets: {np.max(np.abs(swarm_velocity)):.2f} m/s")

print(f"Total raw bins matching threshold: {len(np.where(reflectivity_data >= 10.0)[0]):,}")
print(f"Refined biological bins (clutter excluded): {len(moth_bins[0]):,}")
