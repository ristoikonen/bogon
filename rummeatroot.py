import numpy as np
import pyart

radar = pyart.aux_io.read_odim_h5("40_20260924_180000.pvol.h5")

# Approximate height above the radar site, not above local terrain.
gate_height = (
    np.ma.asarray(radar.gate_altitude["data"])
    - float(radar.altitude["data"][0])
)
ranges_km = radar.range["data"] / 1000.0

for sweep in range(radar.nsweeps):
    start = int(radar.sweep_start_ray_index["data"][sweep])
    end = int(radar.sweep_end_ray_index["data"][sweep]) + 1

    # Median across rays in this sweep gives a representative gate height.
    heights = np.ma.median(gate_height[start:end], axis=0)
    in_layer = (heights >= 150) & (heights <= 1200)

    if np.any(in_layer):
        selected_ranges = ranges_km[in_layer]
        elevation = float(np.ma.mean(radar.elevation["data"][start:end]))
        print(
            f"Sweep {sweep:2d}, elevation {elevation:4.1f} deg: "
            f"about {selected_ranges.min():.1f}-"
            f"{selected_ranges.max():.1f} km range"
        )