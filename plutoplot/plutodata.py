import os
import numpy as np
import matplotlib.pyplot as plt

class PlutoData:
    _coordinate_systems = {'cartesian': ['x', 'y', 'z'],
                          'cylindrical': ['R', 'z'],
                          'polar': ['r', 'phi', 'z'],
                          'spherical': ['r', 'theta', 'phi']}

    def __init__(self, n: int=-1, wdir: str="", coordinates: str='cartesian', part_of_sim=False):
        """
        Read PLUTO output file
        n: output step number. Default: -1, uses last picture
        wdir: path to data directory
        part_of_sim: flag for alternative initialization
        coordinates: 'cartesian', 'cylindrical', 'polar', or 'spherical', only for names
        """
        self.wdir = wdir
        if not part_of_sim:
            # read info about data file
            self.read_vars(n)
            # read grid data
            self.read_grid()
            # read data
            self.read_data()
            try:
                self.coordinate_system = coordinates
                self.coord_names = self.coordinate_systems[coordinates]
                self.coord_names = self._coordinate_systems[coordinates]
            except KeyError:
                raise KeyError('Coordinate system not recognized')

            for i, (_, coord_name) in enumerate(zip(self.dims, self.coord_names), start=1):
                setattr(self, coord_name, getattr(self, f'x{i}'))

    def read_vars(self, n: int=-1):
        """Read simulation step data and written variables"""
        with open(os.path.join(self.wdir, 'dbl.out'), 'r') as f:
            lines = f.readlines()
            # find last saved step
            if n == -1:
                n = int(lines[-1].split()[0])

            n, t, dt, nstep, _, _, *self.vars = lines[n].split()
            self.n, self.t, self.dt, self.nstep = int(n), float(t), float(dt), int(nstep)

    def read_grid(self):
        """
        Read PLUTO gridfile and calculate center of cells
        wdir: Data directory, if empty object data directory is used
        """
        x = []
        self.dims = []
        with open(os.path.join(self.wdir, 'grid.out'), 'r') as gf:
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
                    self.dims.append(dim)
                    # read all data from dimension, moves file pointer
                    data = np.fromfile(gf, sep=' ', count=dim*3).reshape(-1, 3)
                    # calculate center of cell, and difference between cells
                    x.append((np.sum(data[:, 1:], axis=1)/2, data[:, 2] - data[:, 1]))

        self.grid = ([], [])
        for i, (xn, coord_name) in enumerate(zip(x, self.coord_names), start=1):
            setattr(self, f"x{i}", xn[0])
            setattr(self, f"dx{i}", xn[1])
            self.grid[0].append(getattr(self, f"x{i}"))
            self.grid[1].append(getattr(self, f"dx{i}"))
            setattr(self, coord_name, getattr(self, f'x{i}'))

    def read_data(self):
        """
        Read actual data file. Requires information from read_vars(), read_grid()
        (which are run by __init__)
        """
        # load binary file into 1d-array
        raw = np.fromfile(os.path.join(self.wdir, f"data.{self.n:04d}.dbl"), dtype='<f8')
        # seperate variables
        shaped = raw.reshape(len(self.vars), -1)
        # determine shape of data array, depending on used dimensions and resolution
        newshape = []
        if self.dims[2] > 1:
            newshape.append(self.dims[2])
        if self.dims[1] > 1:
            newshape.append(self.dims[1])
        if self.dims[0] > 1:
            newshape.append(self.dims[0])

        # reshape data and save them under varname
        for i, var in enumerate(self.vars):
            setattr(self, var, shaped[i].reshape(newshape))

    def _latex(self, coord: str):
        map = {'phi': r'$\phi$', 'theta': r'$\theta$'}
        try:
            return map[coord]
        except KeyError:
            return coord

    def plot(self, var=None, ax=None, figsize=(10, 10), cbar=True, vmin=None, vmax=None, cmap=None):
        """Simple colorplot for 2-dim data"""
        if var is None:
            var = self.vars[0]
        if isinstance(var, str):
            var = getattr(self, var)
        if ax is None:
            self.fig, self.ax = plt.subplots(figsize=figsize)
            ax = self.ax

        im = ax.pcolormesh(self.x1, self.x2, var, vmin=vmin, vmax=vmax, cmap=cmap)
        ax.set_xlabel(self._latex(self.coord_names[0]))
        ax.set_ylabel(self._latex(self.coord_names[1]))
        ax.set_aspect(1)
        plt.colorbar(im)
