import numpy as np

mapping_coordinates = {
    "cartesian": {"x": "x1", "y": "x2", "z": "x3"},
    "polar": {"r": "x1", "phi": "x2", "z": "x2"},
    "cylindrical": {"r": "x1", "z": "x3"},
    "spherical": {"r": "x1", "theta": "x2", "phi": "x3"},
}

def mapping_grid(coordinates: str) -> dict:
    """
    Generate variable name mapping for specified coordinate system.
    E.g. `phi` gets mapped to `x2` for polar coordinates, and to `x3` for spherical coordinates.
    Implements maping for all coordinates (cell edges and centers) as well as
    velocity components.

    coordinates: str from {'cartesian', 'polar', 'cylindrical', 'spherical'}
    """
    if coordinates not in mapping_coordinates:
        raise NotImplementedError(
            "Coordinate system {} not implemented".format(coordinates)
        )
    mapping = mapping_coordinates[coordinates].copy()
    grid_mappings = {}
    for key, value in mapping.items():
        grid_mappings[key + "l"] = value + "l"
        grid_mappings[key + "r"] = value + "r"
        grid_mappings["d" + key] = "d" + value
    mapping.update(grid_mappings)
    return mapping

def mapping_vars(coordinates: str) -> dict:
    if coordinates not in mapping_coordinates:
        raise NotImplementedError(
            "Coordinate system {} not implemented".format(coordinates)
        )
    return {'v'+key: 'v'+value for key, value in mapping_coordinates[coordinates].items()}

def mapping_tex(coordinates: str) -> dict:
    """
    Generate latex variable mapping in coordinate system
    for correct axis labels in plots.
    """
    if coordinates not in mapping_coordinates:
        raise NotImplementedError(
            "Tex mappings for {} not implemented".format(coordinates)
        )
    mapping = mapping_coordinates[coordinates].copy()
    velocities = {}
    for key, value in mapping.items():
        velocities["v" + key] = "v_" + value
    mapping.update(velocities)
    mapping["rho"] = r"\rho"
    mapping["prs"] = "P"
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
