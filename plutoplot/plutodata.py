import os
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import ScalarFormatter

class PlutoData(object):
    _coordinate_systems = {'cartesian': ['x', 'y', 'z'],
                          'cylindrical': ['R', 'z'],
                          'polar': ['r', 'phi', 'z'],
                          'spherical': ['r', 'theta', 'phi']}

    def __init__(self, n: int=-1, wdir: str="", coordinates: str='cartesian',
                vars: tuple=None,
                grid: tuple=None,
                dims: list=None,
                format: str='dbl'):
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
        self.data = {}
        self.format = format
        # Read all information in if object is not an child to Simulation
        if vars is None:
            # read info about data file
            self._read_vars(n)

            try:
                self.coordinate_system = coordinates
                self.coord_names = self._coordinate_systems[coordinates]
            except KeyError:
                raise KeyError('Coordinate system not recognized')

            # read grid data
            self._read_grid()

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

    def __getattribute__(self, name):
        """Get grid/data attributes from corresponding dict, or load it"""
        # normal attributes
        try:
            return object.__getattribute__(self, name)
        except AttributeError:
            pass

        # grid
        try:
            return self.grid[name]
        except:
            pass

        # data
        try:
            return self.data[name]
        except KeyError:
            if name in self.vars:
                self._load_var(name)
                return self.data[name]
        
        raise AttributeError(f"Plutoplot has no attribute '{name}'")

    def _read_vars(self, n: int=-1) -> None:
        """Read simulation step data and written variables"""
        with open(os.path.join(self.wdir, f'{self.format}.out'), 'r') as f:
            lines = f.readlines()
            # find last saved step
            if n == -1:
                n = int(lines[-1].split()[0])

            # save/tranform into wanted variables
            n, t, dt, nstep, file_mode, endianness, *self.vars = lines[n].split()
            self.n, self.t, self.dt, self.nstep = int(n), float(t), float(dt), int(nstep)
            if file_mode == 'single_file':
                self._file_mode = 'single'
            elif file_mode == 'multiple_files':
                self._file_mode = 'multiple'

            # format of binary files
            if self.format in ['dbl', 'flt']:
                self.charsize = 8 if self.format == 'dbl' else 4
                endianness = '<' if endianness == 'little' else '>'
                self._binformat = f"{endianness}f{self.charsize}"

    def _read_grid(self) -> None:
        """
        Read PLUTO gridfile and calculate center of cells
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

        # save in grid datastructure
        self.grid = {}
        for i, (xn, coord_name) in enumerate(zip(x, self.coord_names), start=1):
            self.grid[f"x{i}"] = xn[0]
            self.grid[f"dx{i}"] = xn[1]
            self.grid[coord_name] = self.grid[f"x{i}"]
            self.grid[f"d{coord_name}"] = self.grid[f"dx{i}"]
        
        # find shape of data
        self.shape = []
        if self.dims[0] > 1:
            self.shape.append(self.dims[0])
        if self.dims[1] > 1:
            self.shape.append(self.dims[1])
        if self.dims[2] > 1:
            self.shape.append(self.dims[2])

        self.size = 1
        for dim in self.dims: self.size *= dim

    def _load_var(self, var):
        """Load data for var into memory. Read either var dbl file (multiple_files mode),
        or, slice data from single dbl file"""
        if self._file_mode == 'single':
            filename = f"data.{self.n:04d}.{self.format}"
            # byte offset of variable in dbl file
            offset = self.charsize * self.size * self.vars.index(var)
        elif self._file_mode == 'multiple':
            filename = f"{var}.{self.n:04d}.{self.format}"
            offset = 0
                
        with open(os.path.join(self.wdir, filename), 'rb') as f:
            f.seek(offset)
            shape = tuple(reversed(self.shape))
            self.data[var] = np.fromfile(f, dtype=self._binformat, count=self.size).reshape(shape).T

    def __getitem__(self, var: str) -> np.ndarray:
        return self.data[var]

    def _latex(self, coord: str, tags: bool=True) -> str:
        if coord is None:
            return ''
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

        im = ax.pcolormesh(self.x1, self.x2, var.T, vmin=vmin, vmax=vmax, cmap=cmap)
        ax.set_xlabel(self._latex(self.coord_names[0]))
        ax.set_ylabel(self._latex(self.coord_names[1]))
        ax.set_aspect(1)
        if cbar:
            formatter = ScalarFormatter()
            formatter.set_powerlimits((-2,2))
            plt.colorbar(im, label=self._latex(varname), format=formatter)

    def __str__(self) -> None:
        return f"""PlutoData, wdir: '{self.wdir}'
resolution: {self.dims}, {self.coordinate_system} coordinates
file nr: {self.n}, time: {self.t}, simulation step: {self.nstep}
Variables: {self.vars}"""


    def __repr__(self) -> None:
        return f"PlutoData({self.n}, wdir='{self.wdir}'" + \
                (f", coordinates='{self.coordinate_system}'" if self.coordinate_system != 'cartesian' else "") + ")"
