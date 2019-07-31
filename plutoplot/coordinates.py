import numpy as np


def generate_coord_mapping(coordinates: str) -> dict:
    mappings = {
        "cartesian": {"x": "x1", "y": "x2", "z": "x3"},
        "polar": {"r": "x1", "phi": "x2", "z": "x2"},
        "cylindrical": {"r": "x1", "z": "x3"},
        "spherical": {"r": "x1", "theta": "x2", "phi": "x3"},
    }
    if coordinates not in mappings:
        raise NotImplementedError(
            "Coordinate system {} not implemented".format(coordinates)
        )
    mapping = mappings[coordinates]
    grid_mappings = {}
    for key, value in mapping.items():
        grid_mappings[key + "l"] = value + "l"
        grid_mappings[key + "r"] = value + "r"
        grid_mappings["d" + key] = "d" + value
    velocities = {}
    for key, value in mapping.items():
        velocities["v" + key] = "v" + value
    mapping.update(grid_mappings)
    mapping.update(velocities)
    return mapping


def generate_tex_mapping(coordinates: str) -> dict:
    mappings = {
        "cartesian": {"x1": "x", "x2": "y", "x3": "z"},
        "cylindrical": {"x1": "r", "x2": "z"},
        "polar": {"x1": "r", "x2": r"\phi", "x3": "z"},
        "spherical": {"x1": "r", "x2": r"\theta", "x3": r"\phi"},
    }
    if coordinates not in mappings:
        raise NotImplementedError(
            "Tex mappings for {} not implemented".format(coordinates)
        )
    mapping = mappings[coordinates]
    velocities = {}
    for key, value in mapping:
        velocities["v" + key] = "v_" + value
    mapping.update(velocities)
    mapping["rho"] = r"\rho"
    mapping["prs"] = "p"
    return mapping


def transform_mesh(coordinates, x1, x2):
    if coordinates == "cartesian":
        return x1, x2
    elif coordinates == "spherical":
        x = x1 * np.sin(x2)
        y = x1 * np.cos(x2)
        return x, y
    elif coordinates == "cylindrical":
        return x1, x2
    elif coordinates == "polar":
        x = x1 * np.cos(x2)
        y = x1 * np.sin(x2)
        return x, y
