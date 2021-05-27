"""Functions and mappings for coordinate grid"""
from functools import lru_cache
from typing import Dict

import numpy as np

base_coordinate_mappings: Dict[str, Dict[str, str]] = {
    "cartesian": {"x": "x1", "y": "x2", "z": "x3"},
    "polar": {"r": "x1", "phi": "x2", "z": "x3"},
    "cylindrical": {"r": "x1", "z": "x2"},
    "spherical": {"r": "x1", "theta": "x2", "phi": "x3"},
}


@lru_cache
def mapping_grid(coordinates: str) -> Dict[str, str]:
    """Generate variable name mapping for specified coordinate system.

    Implements mapping for all coordinates (cell edges and centers) as well as
    velocity components.

    Args:
        coordinates (str): coordinate system name (cartesian, polar, cylindrical, spherical)

    Returns:
        dict[str, str]: Mapping from coordinate system dependend name to PLUTO name
    """
    if coordinates not in base_coordinate_mappings:
        raise NotImplementedError(f"Coordinate system {coordinates} not implemented")

    mapping = base_coordinate_mappings[coordinates].copy()
    grid_mappings = {}
    for coord_name, coord_num in mapping.items():
        grid_mappings[f"{coord_name}l"] = f"{coord_num}l"
        grid_mappings[f"{coord_name}r"] = f"{coord_num}r"
        grid_mappings[f"d{coord_name}"] = f"d{coord_num}"
        grid_mappings[f"L{coord_name}"] = f"Lx{coord_num}"
    mapping.update(grid_mappings)
    return mapping


@lru_cache
def mapping_vars(coordinates: str) -> Dict[str, str]:
    """Coordinate name mapping for velocity components

    Note:
        Names for magnetic and radiative variables are always included.

    Args:
        coordinates (str): coordinate system name (cartesian, polar, cylindrical, spherical)

    Returns:
        dict[str, str]: Mapping from coordinate system dependend name to PLUTO name
    """
    if coordinates not in base_coordinate_mappings:
        raise NotImplementedError(f"Coordinate system {coordinates} not implemented")

    mapping = {}
    for coord_name, coord_num in base_coordinate_mappings[coordinates].items():
        # velocity components
        mapping[f"v{coord_name}"] = f"v{coord_num}"
        # magnetic field
        mapping[f"B{coord_name}"] = f"B{coord_num}"
        mapping[f"B{coord_name}s"] = f"B{coord_num}s"
        # radiativ flux
        mapping[f"fr{coord_name}"] = f"fr{coord_num[1:]}"

    return mapping


tex_chars = {
    "theta": r"\theta",
    "rho": r"\rho",
    "phi": r"\phi",
    "prs": "P",
    "enr": "E_r",
    "Bs": r"B^{(s)}",
    "fr": r"F^{(r)}",
}


@lru_cache
def mapping_tex(coordinates: str) -> Dict[str, str]:
    """Coordinate and variable mapping to LaTeX math mode symbols.

    This maps from variables/coordinates as named in PLUTO outputs
    to Latex names in the respective coordinate system.
    This is useful for plotting.

    Args:
        coordinates (str): coordinate system name (cartesian, polar, cylindrical, spherical)

    Returns:
        dict[str, str]: Mapping from PLUTO name to LaTeX name in coordinate system
    """
    if coordinates not in base_coordinate_mappings:
        raise NotImplementedError(f"Tex mappings for {coordinates} not implemented")

    mapping = {}
    for coord_name, coord_num in base_coordinate_mappings[coordinates].items():
        mapping[coord_num] = mapping[coord_name] = tex_chars.get(coord_name, coord_name)

    mapping_vars = {}
    for coord, tex in mapping.items():
        # velocity
        mapping_vars[f"v{coord}"] = f"v_{tex}"
        # magnetic field
        mapping_vars[f"B{coord}"] = f"B_{tex}"
        mapping_vars[f"B{coord}s"] = f"{tex_chars['Bs']}_{tex}"
        # radiative flux
        mapping_vars[f"fr{coord}"] = f"{tex_chars['fr']}_{tex}"
    # fix radiative flux naming
    for i in range(1, 4):
        try:
            mapping_vars[f"fr{i}"] = mapping_vars.pop(f"frx{i}")
        except KeyError:
            pass
    mapping.update(mapping_vars)

    for key in ("rho", "prs"):
        mapping[key] = tex_chars.get(key, key)

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
