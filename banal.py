import numpy as np
import pyart
import numpy as np

# 1. Load the data - 26sept/40_20260826_180000.pvol.h5 ref file too!
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



# =====================================================================
# ANALYSIS 1: CALCULATION OF SWARM FLIGHT DIRECTION (HEADING)
# =====================================================================
# Extract velocity data matching your 128,131 swarm bins
swarm_velocities = velocity[matching_bins]
clean_velocities = swarm_velocities[~np.isnan(swarm_velocities)]

# Doppler radars measure radial velocity: 
# Negative values indicate targets moving TOWARD the radar antenna.
# Positive values indicate targets moving AWAY from the radar antenna.
incoming_velocity_bins = clean_velocities[clean_velocities < 0]
outgoing_velocity_bins = clean_velocities[clean_velocities > 0]

print("\n=== SWARM KINEMATICS ANALYSIS ===")
print(f"Bins moving toward radar: {len(incoming_velocity_bins):,}")
print(f"Bins moving away from radar: {len(outgoing_velocity_bins):,}")

# Determine heading relative to the Captains Flat station coordinates
if len(incoming_velocity_bins) > len(outgoing_velocity_bins):
    print("Dominant Swarm Vector: The bulk of the biomass is closing in toward the station.")
else:
    print("Dominant Swarm Vector: The bulk of the biomass is moving away/past the station.")

# Calculate the average ground-track component speed
avg_speed_knots = np.mean(np.abs(clean_velocities)) * 1.94384
print(f"Average radial stream speed: {np.mean(np.abs(clean_velocities)):.2f} m/s ({avg_speed_knots:.1f} knots)")



# =====================================================================
# ANALYSIS 2: GEOGRAPHIC FOOTPRINT CALCULATION (AREA IN SQ KM)
# =====================================================================
# Extract the gate spacing dynamically by checking the distance interval between gates
gate_range_array = radar.range['data']
gate_spacing_meters = float(gate_range_array[1] - gate_range_array[0])

# Since matching_bins is a tuple containing multi-dimensional index arrays,
# extracting the length of the first coordinate array gives the total count of matched bins.
num_matching_bins = len(matching_bins[0])

# Calculate the area of a single range gate block (in square kilometres)
# For standard sweeps, this baseline layout calculates a safe vertical column footprint approximation.
approx_gate_area_km2 = (gate_spacing_meters / 1000.0) ** 2  
total_area_km2 = num_matching_bins * approx_gate_area_km2

print("\n=== SWARM ECO-SPATIAL FOOTPRINT ===")
print(f"Single gate baseline scale: {gate_spacing_meters:.1f} meters")
print(f"Total calculated swarm area: {total_area_km2:,.2f} square kilometres")

# Eco-metric evaluation helper
if total_area_km2 > 5000:
    print("Migration Scale: Massive Synoptic Event (Regional migration wave spanning multiple catchments)")
elif total_area_km2 > 1000:
    print("Migration Scale: Major Cohort Wave (Localised high-density bio-front)")
else:
    print("Migration Scale: Scattered/Local Migratory Stream")

