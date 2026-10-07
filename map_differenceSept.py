import numpy as np
import matplotlib.pyplot as plt
import pyart

# To check whether September’s excess forms a geographically coherent patch:
# Map sweep 10 (1.4° elevation), using gates estimated 
# to be 150–1,200 m above the radar.

FILES = {
    "18:00 UTC": "40_20260924_180000.pvol.h5",
    "19:00 UTC": "40_20260924_190000.pvol.h5",
}

SWEEP = 10
MIN_DBZ, MAX_DBZ = -5, 15
CELL_DEGREES = 0.025  # approximately 2-3 km per map cell


def read_sweep(path):
    radar = pyart.aux_io.read_odim_h5(path)
    start = int(radar.sweep_start_ray_index["data"][SWEEP])
    end = int(radar.sweep_end_ray_index["data"][SWEEP]) + 1

    reflectivity = np.ma.asarray(
        radar.fields["reflectivity_horizontal"]["data"][start:end]
    ).filled(np.nan)
    height = (
        np.ma.asarray(radar.gate_altitude["data"][start:end]).filled(np.nan)
        - float(radar.altitude["data"][0])
    )
    latitude = radar.gate_latitude["data"][start:end]
    longitude = radar.gate_longitude["data"][start:end]

    valid = (
        np.isfinite(reflectivity)
        & np.isfinite(height)
        & (height >= 150)
        & (height <= 1200)
    )
    in_range = valid & (reflectivity >= MIN_DBZ) & (reflectivity <= MAX_DBZ)
    return latitude, longitude, valid, in_range, radar


scans = {name: read_sweep(path) for name, path in FILES.items()}

all_lat = np.concatenate([scan[0][scan[2]] for scan in scans.values()])
all_lon = np.concatenate([scan[1][scan[2]] for scan in scans.values()])
lat_edges = np.arange(all_lat.min(), all_lat.max() + CELL_DEGREES, CELL_DEGREES)
lon_edges = np.arange(all_lon.min(), all_lon.max() + CELL_DEGREES, CELL_DEGREES)


def percentage(scan):
    lat, lon, valid, in_range, _ = scan
    valid_count, _, _ = np.histogram2d(
        lat[valid], lon[valid], bins=(lat_edges, lon_edges)
    )
    range_count, _, _ = np.histogram2d(
        lat[in_range], lon[in_range], bins=(lat_edges, lon_edges)
    )
    return np.divide(
        100 * range_count,
        valid_count,
        out=np.full_like(valid_count, np.nan),
        where=valid_count >= 5,
    )


sep_pct = percentage(scans["18:00 UTC"])
aug_pct = percentage(scans["19:00 UTC"])
difference = aug_pct - sep_pct

fig, axes = plt.subplots(1, 3, figsize=(16, 6), constrained_layout=True)

pct_18 = percentage(scans["18:00 UTC"])
pct_19 = percentage(scans["19:00 UTC"])
difference = pct_19 - pct_18

plots = [
    (pct_18, "18:00 UTC: percent in range", 0, 100, "viridis",
     "% of valid gates", [0, 25, 50, 75, 100]),
    (pct_19, "19:00 UTC: percent in range", 0, 100, "viridis",
     "% of valid gates", [0, 25, 50, 75, 100]),
    (difference, "19:00 minus 18:00", -50, 50, "RdBu_r",
     "Percentage-point difference", [-50, -25, 0, 25, 50]),
]

for ax, (data, title, low, high, cmap, colorbar_label, ticks) in zip(axes, plots):
    image = ax.pcolormesh(
        lon_edges, lat_edges, data,
        shading="auto", cmap=cmap, vmin=low, vmax=high
    )
    ax.set_title(title)
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    fig.colorbar(image, ax=ax, shrink=0.72, pad=0.03, label=colorbar_label, ticks=ticks)

fig.suptitle("Sweep 10 (1.4°), 18:00 to 19:00 UTC")
plt.savefig("september_18_to_19_spatial_difference.png", dpi=180)
# plt.show()