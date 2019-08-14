import os
import numpy as np

from .grid import Grid
from .plotting import plot


class PlutoData(object):
    def __init__(self, n: int = -1, simulation=None):
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
        self.wdir, self.grid, self.vars = (
            simulation.data_dir,
            simulation.grid,
            simulation.vars,
        )
        self.n, self.t, self.dt, self.nstep = (
            n,
            simulation.t[n],
            simulation.dt[n],
            simulation.nstep[n],
        )

        self.data = {}

    def __getattr__(self, name):
        """Get grid/data attributes from corresponding dict, or load it"""
        if name.startswith("_"):
            raise AttributeError("{} has no attribute '{}'".format(type(self), name))

        # grid
        try:
            return getattr(self.grid, name)
        except AttributeError:
            pass

        # data
        try:
            return self.data[name]
        except KeyError:
            if name in self.vars:
                self._load_var(name)
                return self.data[name]

        try:
            return getattr(self, self.grid.mapping_vars[name])
        except KeyError:
            pass

        # simulation
        try:
            return getattr(self.simulation, name)
        except AttributeError:
            pass

        raise AttributeError("{} has no attribute '{}'".format(type(self), name))

    def _load_var(self, var):
        """Load data for var into memory. Read either var dbl file (multiple_files mode),
        or, slice data from single dbl file"""
        if self.format in ("dbl", "flt"):
            if self.file_mode == "single":
                filename = "data.{n:04d}.{format}".format(n=self.n, format=self.format)
                # byte offset of variable in dbl file
                offset = self.charsize * self.size * self.vars.index(var)
            else:
                filename = "{var}.{:04d}.{format}".format(
                    var=var, n=self.n, format=self.format
                )
                offset = 0
        elif self.format == "vtk":
            offset = self.simulation.metadata.vtk_offsets[var]
            if self.file_mode == "single":
                filename = "data.{n:04d}.vtk".format(n=self.n)
            else:
                filename = "{var}.{n:04d}.vtk".format(var=var, n=self.n)

        self.data[var] = self._post_load_process(
            var,
            np.memmap(
                os.path.join(self.wdir, filename),
                dtype=self.binformat,
                mode="c",
                offset=offset,
                shape=self.data_shape,
            ),
        )
        setattr(self, var, self.data[var])

    def _post_load_process(self, varname, data):
        """
        User method to process data after loading from disk. Called by _load_var().
        varname: variable name of loaded data
        data: array with data

        returns: modified data array
        """
        return data

    def _latex(self, coord: str, tags: bool = True) -> str:
        if coord is None:
            return ""
        latex_map = {"phi": r"\phi", "theta": r"\theta", "rho": r"\rho"}

        try:
            if coord[0] == "v":
                return "$v_{{{}}}$".format(
                    self._latex(self.coord_names[int(coord[2]) - 1], 0)
                )
            if tags:
                return "${}$".format(latex_map[coord])
            else:
                return latex_map[coord]
        except KeyError:
            return coord

    def plot(self, var=None, grid=None, label: str = None, **kwargs):
        if var is None:
            var = self.vars[0]
        if isinstance(var, str):
            varname = var
            var = getattr(self, var)
        else:
            varname = None
        if grid is None:
            grid = self.grid

        if label is None:
            label = "${}$".format(self.grid.mapping_tex.get(varname, varname))

        return plot(var, grid, label=label, **kwargs)

    def __str__(self) -> None:
        return """PlutoData, wdir: '{wdir}'
resolution: {dims}, {cords} coordinates
file nr: {n}, time: {t}, simulation step: {nstep}
Variables: {vars}""".format(
            wdir=self.wdir,
            dims=self.dims,
            coord=self.grid.coordinates,
            n=self.n,
            t=self.t,
            nstep=self.nstep,
            vars=self.vars,
        )

    def __repr__(self) -> None:
        return "PlutoData({n}, wdir='{wdir}', coordinates='{coords}')".format(
            n=self.n, wdir=self.wdir, coords=self.grid.coordinates
        )

    def __dir__(self) -> list:
        return (
            object.__dir__(self)
            + self.vars
            + list(filter(lambda x: not x.startswith("_"), dir(self.grid)))
            + list(self.grid.mapping_vars)
        )
