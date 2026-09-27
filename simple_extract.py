import pyart
import numpy as np

# 1. Load the data 26sept/40_20260826_180000.pvol.h5 - ref file too!
# radar = pyart.aux_io.read_odim_h5('26aug/40_20260826_180000.pvol.h5')
radar = pyart.aux_io.read_odim_h5('40_20260924_180000.pvol.h5')
reflectivity = radar.fields['reflectivity_horizontal']['data']

# 2. Set your research threshold (e.g., 20.0 dBZ for rain)
target_threshold = 10.0

# 3. Find indices where data is valid, not NaN, and greater than or equal to 20 dBZ
matching_bins = np.where(
    (~reflectivity.mask) & 
    (~np.isnan(reflectivity)) & 
    (reflectivity >= target_threshold)
)

print(f"Number of radar bins tracking rain (>= {target_threshold} dBZ): {len(matching_bins[0]):,}")

# 4. Extract the physical values matching this rain envelope
rain_values = reflectivity[matching_bins]
print(f"Average reflectivity of the rain system: {np.mean(rain_values):.2f} dBZ")


import matplotlib.pyplot as plt

# 5. Create a Py-ART RadarDisplay object
display = pyart.graph.RadarDisplay(radar)

# 6. Setup a clean figure workspace
fig = plt.figure(figsize=(10, 8))
ax = fig.add_subplot(111)

# Extract the velocity array 
velocity = radar.fields['velocity_horizontal']['data']

# Extract velocities only where you found the "rain" targets
moth_velocities = velocity[matching_bins]

# Remove NaNs and print the speed attributes
clean_velocities = moth_velocities[~np.isnan(moth_velocities)]
print(f"Max travel velocity of targets: {np.max(np.abs(clean_velocities)):.2f} m/s")

# 7. Plot the horizontal reflectivity for the lowest sweep (Sweep 0)
# vmin and vmax set the standard color limits for weather radar maps
# Updated Line 36 using the correct colormap name string
display.plot_ppi('reflectivity_horizontal', 0, vmin=-10, vmax=65,
                 title="Canberra (Captains Flat) Radar PPI",
                 ax=ax, cmap='NWSRef')


# 8. Add range rings at 50km, 100km, and 150km intervals
display.plot_range_rings([50, 100, 150])

# 9. Save and display the figure
plt.savefig('captains_flat_storm_map.png', dpi=300, bbox_inches='tight')
plt.show()
# print("Map successfully generated and saved as 'captains_flat_storm_map.png'!")


