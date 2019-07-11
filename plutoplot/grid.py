import numpy as np

from .coordinates import generate_coordinate_mesh


class Grid:
    """
    dims: dimensions
    shape: shape of arrays
    size: total cells
    """

    def __init__(self, gridfile):
        self.coordinates = None
        self.mappings = {}
        self.mappings_tex = {}
        self.read_gridfile(gridfile)

    def set_coordinate_system(self, coordinates, mappings={}, mappings_tex={}):
        self.coordinates = coordinates
        self.mappings = mappings
        self.mappings_tex = mappings_tex

    def read_gridfile(self, gridfile_path) -> None:
        x = []
        dims = []
        with open(gridfile_path, 'r') as gf:
            # read all dimensions
            while True:
                # read line by line, stop if EOF
                line = gf.readline()
                if not line:
                    break
                # ignore comments
                if line[0] == '#':
                    continue
                # find line with resolution in dimension
                splitted = line.split()
                if len(splitted) == 1:
                    dim = int(splitted[0])
                    dims.append(dim)
                    # read all data from dimension, moves file pointer
                    data = np.fromfile(gf, sep=' ', count=dim*3).reshape(-1, 3)
                    # calculate center of cell, and difference between cells
                    x.append((np.sum(data[:, 1:], axis=1)/2, data[:, 2] - data[:, 1]))

        # save in grid datastructure
        for i, xn in enumerate(x, start=1):
            setattr(self, "x{}".format(i), xn[0])
            setattr(self, "dx{}".format(i), xn[1])
        self.dims = tuple(dims)

        shape = []
        if self.dims[2] > 1:
            shape.append(self.dims[2])
        if self.dims[1] > 1:
            shape.append(self.dims[1])
        if self.dims[0] > 1:
            shape.append(self.dims[0])
        self.data_shape = tuple(shape)

        self.size = np.product(self.dims)

    def mesh(self):
        return generate_coordinate_mesh(self.coordinates, self.x1, self.x2)

    def __getattr__(self, name):
        try:
            mappings = object.__getattribute__(self, 'mappings')
            return object.__getattribute__(self, mappings[name])
        except KeyError:
            raise AttributeError("{} has no attribute '{}'".format(type(self), name))

    def __str__(self):
        return "PLUTO Grid, Dimensions {}".format(self.dims)
    __repr__ = __str__
