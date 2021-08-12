"""Functions and mappings for coordinate grid"""
from functools import lru_cache
from typing import Dict

import numpy as np

base_coordinate_mappings: Dict[str, Dict[str, str]] = {
    "cartesian": {"x": "x1", "y": "x2", "z": "x3"},
    "polar": {"r": "x1", "phi": "x2", "z": "x3"},
    "cylindrical": {"r": "x1", "z": "x2", "x3": "x3"},
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
        grid_mappings[f"{coord_name}i"] = f"{coord_num}i"
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


def transform_mesh(grid, mesh1, mesh2):
    if grid.coordinates == "cartesian":
        return (
            f"{grid.mapping_tex[f'x{grid.rdims_ind[0]+1}']}",
            f"{grid.mapping_tex[f'x{grid.rdims_ind[1]+1}']}",
        ), (mesh1, mesh2)
    elif grid.coordinates == "spherical":
        if grid.rdims_ind == (0, 1):
            r = mesh1
            z = r * np.cos(mesh2)
            return ("r", "z"), (r, z)
        elif grid.rdims_ind == (0, 2):
            factor = mesh1 * np.sin(grid.x2[0])
            x = factor * np.cos(mesh2)
            y = factor * np.sin(mesh2)
            return ("x", "y"), (x, y)
        raise NotImplementedError("Projection in (theta, phi) not supported")
    elif grid.coordinates == "cylindrical":
        return ("r", "z"), (mesh1, mesh2)
    elif grid.coordinates == "polar":
        if grid.rdims_ind == (0, 1):
            x = mesh1 * np.cos(mesh2)
            y = mesh2 * np.sin(mesh2)
            return ("x", "y"), (x, y)
        elif grid.rdims_ind == (0, 2):
            return ("r", "z"), (mesh1, mesh2)
        else:
            raise NotImplementedError("Projection in (phi, z) not supported")
