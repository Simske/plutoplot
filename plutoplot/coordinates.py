import numpy as np

mapping_coordinates = {
    "cartesian": {"x": "x1", "y": "x2", "z": "x3"},
    "polar": {"r": "x1", "phi": "x2", "z": "x3"},
    "cylindrical": {"r": "x1", "z": "x2"},
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

tex_mapping = {
    'theta': r"\theta",
    'rho': r"\rho",
    'phi': r"\phi",
    'prs': "P"
}

def mapping_tex(coordinates: str) -> dict:
    """
    Generate latex variable mapping in coordinate system
    for correct axis labels in plots.
    !! TODO: magnetic components
    """
    if coordinates not in mapping_coordinates:
        raise NotImplementedError(
            "Tex mappings for {} not implemented".format(coordinates)
        )
    # invert coordinate mapping map, because x1 needs to become named variable
    mapping = { value: tex_mapping.get(key, key) for key, value in mapping_coordinates[coordinates].items() }

    vel = {}
    for key, value in mapping.items():
        vel['v' + key] = 'v_{}'.format(value)
    mapping.update(vel)

    for key in ('rho', 'prs'):
        mapping[key] = tex_mapping.get(key, key)


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
