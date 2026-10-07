"""Analyze an ODIM polar-volume HDF5 radar file with NumPy."""

import argparse

import numpy as np
import pyart


def load_field(radar, field_name):
    try:
        field_data = radar.fields[field_name]["data"]
    except KeyError as error:
        available = ", ".join(sorted(radar.fields))
        raise SystemExit(
            f"Required radar field {field_name!r} is missing. "
            f"Available fields: {available}"
        ) from error

    values = np.ma.asarray(field_data).filled(np.nan)
    return np.asarray(values, dtype=np.float32)


def main():
    parser = argparse.ArgumentParser(
        description="Count and summarize radar gates above a reflectivity threshold."
    )
    parser.add_argument("file", help="Path to a .pvol.h5 ODIM radar volume")

    parser.add_argument("--min-reflectivity", type=float, default=-5.0)
    parser.add_argument("--max-reflectivity", type=float, default=15.0)

    args = parser.parse_args()

    radar = pyart.aux_io.read_odim_h5(args.file)
    reflectivity = load_field(radar, "reflectivity_horizontal")
    velocity = load_field(radar, "velocity_horizontal")
    if reflectivity.shape != velocity.shape:
        raise SystemExit(
            "Reflectivity and velocity fields have different shapes: "
            f"{reflectivity.shape} vs {velocity.shape}"
        )

    qualifying = (
        np.isfinite(reflectivity)
        & (reflectivity >= args.min_reflectivity)
        & (reflectivity <= args.max_reflectivity)
    )

    reflectivity_values = reflectivity[qualifying]
    qualifying_count = reflectivity_values.size

    print(f"File: {args.file}")
    print(f"Radar field shape: {tuple(reflectivity.shape)}")
    print(f"Reflectivity range: {args.min_reflectivity:.1f} to {args.max_reflectivity:.1f} dBZ")
    print(f"Qualifying radar gates: {qualifying_count:,}")
    if qualifying_count == 0:
        print("No valid gates met the threshold.")
        return

    print(
        "Mean reflectivity at qualifying gates: "
        f"{np.mean(reflectivity_values):.2f} dBZ"
    )

    valid_velocity = qualifying & np.isfinite(velocity)
    velocity_values = velocity[valid_velocity]
    velocity_count = velocity_values.size
    print(f"Qualifying gates with valid velocity: {velocity_count:,}")
    if velocity_count:
        absolute_velocity = np.abs(velocity_values)
        print(
            "Mean absolute radial velocity: "
            f"{np.mean(absolute_velocity):.2f} m/s"
        )
        print(
            "Maximum absolute radial velocity: "
            f"{np.max(absolute_velocity):.2f} m/s"
        )


if __name__ == "__main__":
    main()
