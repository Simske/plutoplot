import os
import numpy as np
import matplotlib.pyplot as plt

class PlutoData:
    _coordinate_systems = {'cartesian': ['x', 'y', 'z'],
                          'cylindrical': ['R', 'z'],
                          'polar': ['r', 'phi', 'z'],
                          'spherical': ['r', 'theta', 'phi']}

    def __init__(self, n: int=-1, wdir: str="", coordinates: str='cartesian',
                vars: tuple=None,
                grid: tuple=None,
                dims: list=None):
        """
        Read PLUTO output file
        n: output step number. Default: -1, uses last picture
        wdir: path to data directory
        coordinates: 'cartesian', 'cylindrical', 'polar', or 'spherical', only for names

        Remaining arguments are for constructing object with preloaded data:
        vars: tuple(list, int, float, float, int) = (vars, n, t, dt, nstep)
        grid: tuple(list(numpy.array), list(numpy.array)) = ([xi], [dxi])
        """
        self.wdir = wdir
        # Read all information in if object is not an child to Simulation
        if vars is None:
            # read info about data file
            self.read_vars(n)

            try:
                self.coordinate_system = coordinates
                self.coord_names = self._coordinate_systems[coordinates]
            except KeyError:
                raise KeyError('Coordinate system not recognized')

            # read grid data
            self.read_grid()
            # read data
            self.read_data()

        else:
            # construct object from preloaded information
            # vars
            self.vars, self.n, self.t, self.dt, self.nstep = vars
            # coordinate names
            self.coordinate_system = coordinates
            self.coord_names = self._coordinate_systems[coordinates]
            # grid
            self.dims = dims
            self.grid = grid

            for i in range(len(grid[0])):
                j = i + 1
                setattr(self, f"x{j}", grid[0][i])
                setattr(self, f"dx{j}", grid[1][i])
                setattr(self, self.coord_names[i], getattr(self, f'x{j}'))

            self.read_data()


    def read_vars(self, n: int=-1) -> None:
        """Read simulation step data and written variables"""
        with open(os.path.join(self.wdir, 'dbl.out'), 'r') as f:
            lines = f.readlines()
            # find last saved step
            if n == -1:
                n = int(lines[-1].split()[0])

            n, t, dt, nstep, _, _, *self.vars = lines[n].split()
            self.n, self.t, self.dt, self.nstep = int(n), float(t), float(dt), int(nstep)

    def read_grid(self) -> None:
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

    def read_data(self) -> None:
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

        self.data = {}
        # reshape data and save them under varname
        for i, var in enumerate(self.vars):
            self.data[var] = shaped[i].reshape(newshape)
            setattr(self, var, self.data[var])
            if var[0] == 'v':
                new_name = f"v{self.coord_names[int(var[2])-1]}"
                self.data[new_name] = self.data[var]
                setattr(self, new_name, self.data[var])

    def __getitem__(self, var: str) -> np.ndarray:
        return self.data[var]

    def _latex(self, coord: str, tags: bool=True) -> str:
        latex_map = {
            'phi': r'\phi',
            'theta': r'\theta',
            'rho': r'\rho',
        }

        try:
            if coord[0] == 'v':
                return f"$v_{{{self._latex(self.coord_names[int(coord[2])-1], 0)}}}$"
            if tags:
                return f'${latex_map[coord]}$'
            else:
                return latex_map[coord]
        except KeyError:
            return coord

    def plot(self, var=None, ax=None, figsize=(10, 10), cbar=True, vmin=None, vmax=None, cmap=None) -> None:
        """Simple colorplot for 2-dim data"""
        if var is None:
            var = self.vars[0]
        if isinstance(var, str):
            varname = var
            var = getattr(self, var)
        else:
            varname = None
        if ax is None:
            self.fig, self.ax = plt.subplots(figsize=figsize)
            ax = self.ax

        im = ax.pcolormesh(self.x1, self.x2, var, vmin=vmin, vmax=vmax, cmap=cmap)
        ax.set_xlabel(self._latex(self.coord_names[0]))
        ax.set_ylabel(self._latex(self.coord_names[1]))
        ax.set_aspect(1)
        plt.colorbar(im, label=self._latex(varname))

    def __str__(self) -> None:
        return f"""PlutoData, wdir: '{self.wdir}'
resolution: {self.dims}, {self.coordinate_system} coordinates
file nr: {self.n}, time: {self.t}, simulation step: {self.nstep}
Variables: {self.vars}"""


    def __repr__(self) -> None:
        return f"PlutoData({self.n}, wdir='{self.wdir}'" + \
                (f", coordinates='{self.coordinate_system}'" if self.coordinate_system != 'cartesian' else "") + ")"
