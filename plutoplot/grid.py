from pathlib import Path

import numpy as np

from .coordinates import mapping_grid, mapping_tex, mapping_vars, transform_mesh


class Grid:
    """
    dims: dimensions
    shape: shape of arrays
    size: total cells
    """

    def __init__(self, gridfile: Path, coordinates: str = None):
        # initialize attributes
        self.coordinates = None
        self.mapping_grid = {}
        self.mapping_vars = {}
        self.mapping_tex = {}

        # read gridfile, get coordinate system if necessary
        self.read_gridfile(gridfile, coordinates)

        if coordinates is not None:
            self.set_coordinate_system(coordinates)

    def set_coordinate_system(self, coordinates):
        self.coordinates = coordinates
        self.mapping_grid = mapping_grid(coordinates)
        self.mapping_vars = mapping_vars(coordinates)
        self.mapping_tex = mapping_tex(coordinates)

    def read_gridfile(self, gridfile_path: Path, coordinates: str = None) -> None:
        # to be filled with left and right cell interfaces
        x = []
        dims = []
        with gridfile_path.open() as gf:
            # Gridfile header
            header = False  # marker if gf pointer is in header
            while True:
                line = gf.readline()
                if line.startswith("# *****"):
                    # header starts and ends with # *****...
                    # toggle marker when entering header
                    # and exit when header is finished
                    header = not header
                    if not header:
                        break
                elif coordinates is None and line.startswith("# GEOMETRY"):
                    self.set_coordinate_system(line[11:].strip().lower())

            # read all dimensions
            while True:
                # read line by line, stop if EOF
                line = gf.readline()
                if not line:
                    break
                # find line with resolution in dimension
                splitted = line.split()
                if len(splitted) == 1:
                    dim = int(splitted[0])
                    dims.append(dim)
                    # read all data from dimension, moves file pointer
                    data = np.fromfile(gf, sep=" ", count=dim * 3).reshape(-1, 3)
                    # save left and right cell interface
                    x.append((data[:, 1], data[:, 2]))

        # save in grid datastructure
        for i, xn in enumerate(x, start=1):
            # cell interfaces
            setattr(self, "x{}l".format(i), xn[0])
            setattr(self, "x{}r".format(i), xn[1])
            # cell centers
            setattr(self, "x{}".format(i), (xn[0] + xn[1]) / 2)
            # cell width
            setattr(self, "dx{}".format(i), xn[1] - xn[0])
        self.dims = tuple(dims)

        self.data_shape = tuple(
            (self.dims[i] for i in range(2, -1, -1) if self.dims[i] > 1)
        )

        self.size = np.product(self.dims)

    def mesh_center(self):
        """
        2D cell center mesh in native coordinates
        Returns:
        X, Y with shape for each: (dim[1],dim[0])
        """
        return np.meshgrid(self.x1, self.x2)

    def mesh_edge(self):
        """
        2D cell edge mesh in native coordinates
        Returns:
        X, Y with shape for each: (dim[1]+1,dim[0]+1)
        """
        return np.meshgrid(
            np.append(self.x1l, self.x1r[-1]), np.append(self.x2l, self.x2r[-1])
        )

    def mesh_center_cartesian(self):
        """
        2D cell center mesh trasformed to cartesian coordinates
        Returns:
        X, Y with shape for each: (dim[1],dim[0])
        """
        return transform_mesh(self.coordinates, *self.mesh_center())

    def mesh_edge_cartesian(self):
        """
        2D cell edge mesh trasformed to cartesian coordinates
        Returns:
        X, Y with shape for each: (dim[1]+1,dim[0]+1)
        """
        return transform_mesh(self.coordinates, *self.mesh_edge())

    def __getattr__(self, name: str):
        if name.startswith("_"):
            raise AttributeError("{} has no attribute '{}'".format(type(self), name))
        try:
            return getattr(self, self.mapping_grid[name])
        except KeyError:
            raise AttributeError("{} has no attribute '{}'".format(type(self), name))

    def __str__(self):
        return "PLUTO Grid, Dimensions {}, Coordinate System: '{}'".format(
            self.dims, self.coordinates
        )

    __repr__ = __str__

    def __dir__(self):
        return object.__dir__(self) + list(self.mapping_grid.keys())
