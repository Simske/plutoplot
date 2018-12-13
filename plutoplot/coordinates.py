import numpy as np


def generate_coord_mapping(coordinates: str) -> dict:
    mappings = {
        'cartesian': {
            'x': 'x1',
            'y': 'x2',
            'z': 'x3',
        },
        'polar': {
            'r': 'x1',
            'z': 'x2'
        },
        'cylindrical': {
            'r': 'x1',
            'phi': 'x2',
            'z': 'x3'
        },
        'spherical': {
            'r': 'x1',
            'theta': 'x2',
            'phi': 'x3',
        }
    }
    if coordinates not in mappings:
        raise NotImplementedError(f'Coordinate system {coordinates} not implemented')
    mapping = mappings[coordinates]
    velocities = {}
    for key, value in mapping.items():
        velocities[f"v{key}"] = f"v{value}"
    mapping.update(velocities)
    return mapping

def generate_tex_mapping(coordinates: str) -> dict:
    mappings = {
        'cartesian': {
            'x1': 'x',
            'x2': 'y',
            'x3': 'z'
        },
        'polar': {
            'x1': 'r',
            'x2': 'z'
        },
        'cylindrical': {
            'x1': 'r',
            'x2': r'\phi',
            'x3': 'z'
        },
        'spherical': {
            'x1': 'r',
            'x2': r'\theta',
            'x3': r'\phi'
        }
    }
    if coordinates not in mappings:
        raise NotImplementedError(f'Tex mappings for {coordinates} not implemented')
    mapping = mappings[coordinates]
    velocities = {}
    for key, value in mapping:
        velocities[f"v{key}"] = f"v_{value}"
    mapping.update(velocities)
    mapping['rho'] = r'\rho'
    mapping['prs'] = 'p'
    return mapping

def generate_coordinate_mesh(coordinates, x1, x2):
    if coordinates == 'cartesian':
        return x1, x2
    elif coordinates == 'spherical':
        r, theta = np.meshgrid(x1, x2)
        x = r * np.sin(theta)
        y = r * np.cos(theta)
        return x, y
    elif coordinates == 'cylindrical':
        r, phi = np.meshgrid(x1, x2)
        x = r * np.cos(phi)
        y = r * np.sin(phi)
        return x, y