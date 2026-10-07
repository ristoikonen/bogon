import csv
from pathlib import Path

import numpy as np
import pyart

FILES = {
    "September": Path("40_20260924_180000.pvol.h5"),
    "August": Path("26aug/40_20260826_180000.pvol.h5"),
}
MIN_DBZ = -5.0
MAX_DBZ = 15.0
RANGE_BIN_KM = 10.0


def analyze_file(path):
    radar = pyart.aux_io.read_odim_h5(str(path))
    reflectivity = np.ma.asarray(
        radar.fields["reflectivity_horizontal"]["data"]
    ).filled(np.nan)
    ranges_km = radar.range["data"] / 1000.0

    if radar.nsweeps != 13:
        raise ValueError(f"{path}: expected 13 sweeps, found {radar.nsweeps}")

    max_edge = np.ceil(np.max(ranges_km) / RANGE_BIN_KM) * RANGE_BIN_KM
    edges = np.arange(0.0, max_edge + RANGE_BIN_KM, RANGE_BIN_KM)
    range_grid = np.broadcast_to(ranges_km, reflectivity.shape)
    results = []

    for sweep in range(radar.nsweeps):
        start = int(radar.sweep_start_ray_index["data"][sweep])
        end = int(radar.sweep_end_ray_index["data"][sweep]) + 1
        values = reflectivity[start:end]
        gate_ranges = range_grid[start:end]

        valid = np.isfinite(values)
        in_band = valid & (values >= MIN_DBZ) & (values <= MAX_DBZ)

        valid_counts, _ = np.histogram(gate_ranges[valid], bins=edges)
        target_counts, _ = np.histogram(gate_ranges[in_band], bins=edges)
        elevation = float(np.mean(radar.elevation["data"][start:end]))

        results.append((elevation, valid_counts, target_counts))

    return edges, results


scans = {label: analyze_file(path) for label, path in FILES.items()}
september_edges, september = scans["September"]
august_edges, august = scans["August"]

if not np.array_equal(september_edges, august_edges):
    raise ValueError("The scans have different range bins; compare their ranges first.")

with Path("sweep_range_comparison.csv").open("w", newline="") as output:
    writer = csv.writer(output)
    writer.writerow([
        "sweep", "September elevation (deg)", "August elevation (deg)",
        "range start (km)", "range end (km)",
        "September gates", "August gates", "difference",
        "September % of valid gates", "August % of valid gates",
    ])

    for sweep, (sep, aug) in enumerate(zip(september, august)):
        sep_elev, sep_valid, sep_counts = sep
        aug_elev, aug_valid, aug_counts = aug

        for band in range(len(september_edges) - 1):
            sep_count = int(sep_counts[band])
            aug_count = int(aug_counts[band])
            sep_pct = 100 * sep_count / sep_valid[band] if sep_valid[band] else 0
            aug_pct = 100 * aug_count / aug_valid[band] if aug_valid[band] else 0

            writer.writerow([
                sweep,
                f"{sep_elev:.1f}",
                f"{aug_elev:.1f}",
                f"{september_edges[band]:.0f}",
                f"{september_edges[band + 1]:.0f}",
                sep_count,
                aug_count,
                sep_count - aug_count,
                f"{sep_pct:.2f}",
                f"{aug_pct:.2f}",
            ])

print("Wrote sweep_range_comparison.csv")