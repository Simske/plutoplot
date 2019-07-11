import numpy as np

from .coordinates import transform_mesh


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
        # to be filled with left and right cell interfaces
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
                    # save left and right cell interface
                    x.append((data[:,1], data[:,2]))

        # save in grid datastructure
        for i, xn in enumerate(x, start=1):
            # cell interfaces
            setattr(self, "x{}l".format(i), xn[0])
            setattr(self, "x{}r".format(i), xn[1])
            # cell centers
            setattr(self, "x{}".format(i), (xn[0] + xn[1])/2)
            # cell width
            setattr(self, "dx{}".format(i), xn[1] - xn[0])
        self.dims = tuple(dims)

        self.data_shape = tuple((self.dims[i] for i in range(2,-1,-1) if self.dims[i] > 1))

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
        return np.meshgrid(np.append(self.x1l, self.x1r[-1]),
                           np.append(self.x2l, self.x2r[-1]))

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

    def __getattr__(self, name):
        try:
            mappings = object.__getattribute__(self, 'mappings')
            return object.__getattribute__(self, mappings[name])
        except KeyError:
            raise AttributeError("{} has no attribute '{}'".format(type(self), name))

    def __str__(self):
        return "PLUTO Grid, Dimensions {}".format(self.dims)
    __repr__ = __str__
