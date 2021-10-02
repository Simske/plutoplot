"""PlutoData: Class to contain a single PLUTO output step"""
import numpy as np

try:
    import h5py
except ImportError:
    pass

from .grid import Grid, GridSlice
from .metadata import SimulationMetadata
from .misc import Slicer
from .plotting import plot


class PlutoData:
    """Object representing single PLUTO output step

    Attributes:
        n (int): Number of output in simulation
        t (float): Simulation time at output
        sim_dt (float): Simulation timestep at output
        nstep (int): Simulation steps at output
        metadata (plutoplot.io.SimulationMetadata): Metadata read from .out file
        grid (plutoplot.grid.Grid): Grid read from grid.out
        simulation (plutoplot.simulation.Simulation): Simulation this data step is part of.
            Can be None, as this doesn't have to be initialized from Simulation.
    """

    def __init__(
        self,
        n: int,
        metadata: SimulationMetadata,
        grid: Grid,
        simulation=None,
    ):
        self.n = n
        self.metadata = metadata
        self.grid = grid
        self.simulation = simulation

        self.t, self.sim_dt, self.nstep = (
            metadata.t[n],
            metadata.sim_dt[n],
            metadata.nstep[n],
        )

        self._data = {}
        self.slicer = Slicer(
            lambda slice_: PlutoDataSlice(self, self.grid.slicer[slice_])
        )

    def __getattr__(self, attr: str):
        """Get data / grid / metadata attributes

        This function only gets called if the PlutoData itself has no attribute with this name.

        Args:
            attr (str): name of attribute

        Returns:
            Any: requested attribute

        Raises:
            AttributeError: if `attr` is not an attribute of either data, grid, or metadata.
        """
        # don't forward private methods
        if attr.startswith("_"):
            raise AttributeError(f"{type(self).__name__} has no attribute '{attr}'")

        try:  # data variables
            return self[attr]
        except KeyError:
            pass
        try:  # grid
            return getattr(self.grid, attr)
        except AttributeError:
            pass
        try:  # simulation
            return self.simulation.__getattribute__(attr)
        except AttributeError:
            pass

        raise AttributeError(f"{type(self).__name__} has no attribute '{attr}'")

    def __delattr__(self, var):
        """Remove data array from memory"""
        try:
            del self[var]
        except KeyError as e:
            raise AttributeError(str(e))

    def __getitem__(self, var: str) -> np.memmap:
        """Get data array for variable

        Returns:
            :obj:`numpy.ndarray` or :obj:`numpy.memmap`
        """
        var_generic = self.grid.mapping_vars.get(var, var)
        try:
            return self._data[var_generic]
        except KeyError:
            if var_generic in self.metadata.vars:
                self._data[var_generic] = self._load_var(var_generic)
                return self._data[var_generic]
        raise KeyError(f"{type(self).__name__}: '{var}' is not a data variable")

    def __delitem__(self, var: str):
        """Delete data arrays to free memory

        Raises:
            KeyError
        """
        var_generic = self.grid.mapping_vars.get(var, var)
        try:
            del self._data[var_generic]
        except KeyError:
            if var_generic not in self.vars:
                raise KeyError(
                    f"{type(self).__name__}: '{var}' is not a data variable"
                ) from None

    def _load_var(self, varname) -> np.memmap:
        """Create memorymap to data

        Args:
            varname (str): variable name

        Returns:
            numpy.memmap: Memorymap to data
        """
        if self.metadata.format in ("dbl.h5", "flt.h5"):
            if self.grid.indexing == "ijk":
                raise NotImplementedError(
                    "ijk indexing not implemented for HDF5 outputs. Use indexing=kji"
                )
            try:
                self.h5file
            except AttributeError:
                try:
                    self.h5file = h5py.File(
                        self.metadata.data_path
                        / f"data.{self.n:04d}.{self.metadata.format}",
                        "r",
                    )
                except NameError:
                    raise ImportError(
                        "plutoplot: Optional dependency 'h5py' not installed, required for reading HDF5 files"
                    ) from None
            finally:
                return self._post_load_process(
                    varname, self.h5file[f"Timestep_{self.n}/vars/{varname}"]
                )

        if self.metadata.format in ("dbl", "flt"):
            if self.metadata.file_mode == "single":
                filename = f"data.{self.n:04d}.{self.metadata.format}"
                # byte offset of variable in binary file
                offset = (
                    self.metadata.charsize
                    * self.grid.size
                    * self.metadata.vars.index(varname)
                )
            else:
                filename = f"{varname}.{self.n:04d}.{self.metadata.format}"
                offset = 0
        elif self.format == "vtk":
            offset = self.metadata.vtk_offsets[varname]
            if self.file_mode == "single":
                filename = "data.{self.n:04d}.vtk"
            else:
                filename = "{var}.{self.n:04d}.vtk"

        return self._post_load_process(
            varname,
            self.grid.T(
                np.memmap(
                    self.metadata.data_path / filename,
                    dtype=self.metadata.binformat,
                    mode="c",
                    offset=offset,
                    shape=self.grid.data_shape,
                )
            ),
        )

    def _post_load_process(self, varname, data: np.ndarray):
        """Process data after loading from disk

        User method to process data after loading it from disk.
        Does nothing by default, can be overwritten in subclass.

        Args:
            varname
        """
        return data

    def plot(
        self, var: str, grid=None, label: str = None, show_title: bool = True, **kwargs
    ):
        """TODO"""
        if isinstance(var, str):
            varname = var
            var = getattr(self, var)
        else:
            varname = None
        if grid is None:
            grid = self.grid

        if label is None:
            label = "${}$".format(self.grid.mapping_tex.get(varname, varname))

        fig, ax = plot(var, grid, label=label, **kwargs)

        if show_title:
            ax.set_title(f"$t={self.t:.2f}$")

        return fig, ax

    def __str__(self) -> str:
        return (
            f"{type(self).__name__}, output nr: {self.n}, time: {self.t}, simulation step: {self.nstep}\n"
            f"data directory: '{self.metadata.data_path}'\n"
            f"resolution: {self.grid.dims}, {self.grid.coordinates} coordinates\n"
            f"Variables: {' '.join(self.metadata.vars)}"
        )

    def __repr__(self) -> str:
        return (
            f"{type(self).__name__}({self.n}, metadata={repr(self.metadata)}, "
            f"grid={repr(self.grid)}, simulation={repr(self.simulation)})"
        )

    def _repr_markdown_(self) -> str:
        """Jupyter pretty print"""
        return (
            f"**{type(self).__name__}**, output nr: {self.n}, time: {self.t}, simulation step: {self.nstep}  \n"
            f"data directory: `{self.metadata.data_path}`  \n"
            f"Data vars: `{'` `'.join(self.metadata.vars)}`  \n"
        ) + self.grid._repr_markdown_()

    def __dir__(self) -> list:
        return (
            object.__dir__(self)
            + self.metadata.vars
            + [attr for attr in dir(self.grid) if not attr.startswith("_")]
            + [attr for attr in dir(self.metadata) if not attr.startswith("_")]
            + list(self.grid.mapping_vars)
        )


class PlutoDataSlice(PlutoData):
    def __init__(self, parent: PlutoData, sliced_grid: Grid = None):
        self.parent = parent
        self.n = parent.n
        self.metadata = parent.metadata
        self.simulation = parent.simulation

        self.t, self.sim_dt, self.nstep = (
            parent.metadata.t[self.n],
            parent.metadata.sim_dt[self.n],
            parent.metadata.nstep[self.n],
        )

        self.grid = sliced_grid

        self.slicer = None

    def __getitem__(self, var: str) -> np.memmap:
        return self.parent[var][self.grid.slice]

    def __delitem__(self, var: str):
        del self.parent[var]

    def _load_var(self, varname):
        raise NotImplementedError("_load_var is only implemented on parent object")
