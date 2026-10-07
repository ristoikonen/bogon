"""Analyze an ODIM polar-volume HDF5 radar file with TensorFlow."""

import argparse

import numpy as np
import pyart
import tensorflow as tf


def load_tensor_field(radar, field_name):
    try:
        field_data = radar.fields[field_name]["data"]
    except KeyError as error:
        available = ", ".join(sorted(radar.fields))
        raise SystemExit(
            f"Required radar field {field_name!r} is missing. "
            f"Available fields: {available}"
        ) from error

    values = np.ma.asarray(field_data).filled(np.nan)
    return tf.convert_to_tensor(np.asarray(values, dtype=np.float32))


def main():
    parser = argparse.ArgumentParser(
        description="Count and summarize radar gates above a reflectivity threshold."
    )
    parser.add_argument("file", help="Path to a .pvol.h5 ODIM radar volume")
    parser.add_argument(
        "--threshold",
        type=float,
        default=10.0,
        help="Minimum reflectivity in dBZ (default: 10)",
    )
    args = parser.parse_args()

    radar = pyart.aux_io.read_odim_h5(args.file)
    reflectivity = load_tensor_field(radar, "reflectivity_horizontal")
    velocity = load_tensor_field(radar, "velocity_horizontal")
    if reflectivity.shape != velocity.shape:
        raise SystemExit(
            "Reflectivity and velocity fields have different shapes: "
            f"{reflectivity.shape} vs {velocity.shape}"
        )

    qualifying = tf.math.is_finite(reflectivity) & (
        reflectivity >= args.threshold
    )
    reflectivity_values = tf.boolean_mask(reflectivity, qualifying)
    qualifying_count = int(tf.size(reflectivity_values).numpy())

    print(f"File: {args.file}")
    print(f"Radar field shape: {tuple(reflectivity.shape)}")
    print(f"Reflectivity threshold: >= {args.threshold:.1f} dBZ")
    print(f"Qualifying radar gates: {qualifying_count:,}")
    if qualifying_count == 0:
        print("No valid gates met the threshold.")
        return

    print(
        "Mean reflectivity at qualifying gates: "
        f"{float(tf.reduce_mean(reflectivity_values).numpy()):.2f} dBZ"
    )

    valid_velocity = qualifying & tf.math.is_finite(velocity)
    velocity_values = tf.boolean_mask(velocity, valid_velocity)
    velocity_count = int(tf.size(velocity_values).numpy())
    print(f"Qualifying gates with valid velocity: {velocity_count:,}")
    if velocity_count:
        absolute_velocity = tf.abs(velocity_values)
        print(
            "Mean absolute radial velocity: "
            f"{float(tf.reduce_mean(absolute_velocity).numpy()):.2f} m/s"
        )
        print(
            "Maximum absolute radial velocity: "
            f"{float(tf.reduce_max(absolute_velocity).numpy()):.2f} m/s"
        )


if __name__ == "__main__":
    main()
