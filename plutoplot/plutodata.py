import os
import numpy as np

from .io import Grid
from .plotting import plot

class PlutoData(object):

    def __init__(self, n: int=-1, simulation=None):
        """
        Read PLUTO output file
        n: output step number. Default: -1, uses last picture
        wdir: path to data directory
        coordinates: 'cartesian', 'cylindrical', 'polar', or 'spherical', only for names

        vars [dict]: variables for manual construction
        simulation [Simulation]: parent Simulation, missing attributes are tried to fetch from there
        """
        # construct object from simulation simulation
        self.simulation = simulation
        self.format = simulation.format
        self.binformat = simulation.metadata.binformat
        self.file_mode = simulation.metadata.file_mode
        self.wdir, self.grid, self.vars = simulation.data_dir, simulation.grid, simulation.vars
        self.n, self.t, self.dt, self.nstep = n, simulation.t[n], simulation.dt[n], simulation.nstep[n]
        
        self.data = {}


    def __getattr__(self, name):
        """Get grid/data attributes from corresponding dict, or load it"""
        # normal attributes
        # grid
        getattribute = object.__getattribute__
        grid = getattribute(self, 'grid')
        try:
            return getattr(grid, name)
        except AttributeError:
            pass

        # data
        data = getattribute(self, 'data')
        try:
            return data[name]
        except KeyError:
            if name in getattribute(self, 'vars'):
                getattribute(self, '_load_var')(name)
                return data[name]

        # simulation
        try:
            return getattr(getattribute(self, 'simulation'), name)
        except AttributeError:
            pass

        raise AttributeError(f"{type(self)} has no attribute '{name}'")

    def _load_var(self, var):
        """Load data for var into memory. Read either var dbl file (multiple_files mode),
        or, slice data from single dbl file"""
        if self.file_mode == 'single':
            filename = f"data.{self.n:04d}.{self.format}"
            # byte offset of variable in dbl file
            offset = self.charsize * self.size * self.vars.index(var)
        elif self.file_mode == 'multiple':
            filename = f"{var}.{self.n:04d}.{self.format}"
            offset = 0

        with open(os.path.join(self.wdir, filename), 'rb') as f:
            f.seek(offset)
            shape = tuple(reversed(self.data_shape))
            self.data[var] = np.fromfile(f, dtype=self.binformat, count=self.size).reshape(shape).T


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
    
    def plot(self, var=None, **kwargs):
        if var is None:
            var = self.vars[0]
        if isinstance(var, str):
            varname = var
            var = getattr(self, var)
        else:
            varname = None
        
        return plot(var, self.grid, label=f"${self.grid.mappings_tex.get(varname, varname)}$", **kwargs)

    def __str__(self) -> None:
        return f"""PlutoData, wdir: '{self.wdir}'
resolution: {self.dims}, {self.coordinate_system} coordinates
file nr: {self.n}, time: {self.t}, simulation step: {self.nstep}
Variables: {self.vars}"""


    def __repr__(self) -> None:
        return f"PlutoData({self.n}, wdir='{self.wdir}'" + \
                (f", coordinates='{self.coordinate_system}'" if self.coordinate_system != 'cartesian' else "") + ")"

    def __dir__(self) -> list:
        return object.__dir__(self) + self.vars + list(self.grid.keys())
