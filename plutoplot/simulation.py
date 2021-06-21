import multiprocessing
from pathlib import Path

import numpy as np

from .grid import Grid
from .metadata import Definitions_h, Pluto_ini, SimulationMetadata
from .misc import cached_property
from .plutodata import PlutoData


class Simulation:
    """
    Container class for PLUTO (http://plutocode.ph.unito.it/) output.
    Reads the metadata of all files in working directory (wdir), and
    loads individual files when needed.
    Simulation is subscriptable and iterable.

    Attributes:
        path (pathlib.Path): Path to simulation directory
            (directory with `pluto.ini`, `definitions.h`, etc)
        data_path (pathlib.Path): path to data directory (with `*.out` and data files)
        format (str): simulation format
        metadata (plutoplot.io.SimulationMetadata): Simulation metadata
        grid (plutoplot.grid.Grid): Simulation grid
    """

    supported_formats = ("dbl", "flt", "vtk", "dbl.h5", "flt.h5")
    DataObject = PlutoData

    def __init__(self, path: Path = ".", format: str = None, coordinates: str = None):
        self.path = Path(path)

        ## Find data directory ##
        if (self.path / "grid.out").exists():
            self.data_path = self.path
        elif (self.path / "data" / "grid.out").exists():
            self.data_path = self.path / "data"
        else:
            try:
                from_ini = self.path / self.ini["Static Grid Output"]["output_dir"]
                if (from_ini / "grid.out").exists():
                    self.data_path = from_ini
                else:
                    raise FileNotFoundError()
            except FileNotFoundError:
                raise FileNotFoundError(
                    "Data directory with gridfile not found"
                ) from None

        # dict for individual data frames
        self._data = {}

        ## Find data format
        self.format = None
        if format is None:
            for format in self.supported_formats:
                if (self.data_path / f"{format}.out").exists():
                    self.format = format
                    break
            if self.format is None:
                raise FileNotFoundError(
                    f"No Metadata file for formats {self.supported_formats} found in {self.data_path}"
                )
        else:
            if format not in self.supported_formats:
                raise NotImplementedError(f"Format '{format}' not supported")
            if (self.data_path / f"{format}.out").exists():
                self.format = format
            else:
                raise FileNotFoundError(
                    f"Metadata file {self.data_path / f'{format}.out'} not found."
                )

        ## Read metadata ##
        self.metadata = SimulationMetadata(self.data_path, self.format)

        ## Read grid ##
        # coordinate system will be read from gridfile if `coordinates is None`
        self.grid = Grid(self.data_path / "grid.out", coordinates)

    @cached_property
    def ini(self) -> Pluto_ini:
        """Read access to PLUTO runtime initialization file 'pluto.ini'"""
        return Pluto_ini(self.path / "pluto.ini")

    @cached_property
    def definitions(self) -> Definitions_h:
        """Read access to PLUTO compile time 'definitions.h' file"""
        return Definitions_h(self.path / "definitions.h")

    def __getattr__(self, attr: str):
        """Resolve attributes to metadata/data/grid attributes"""
        # Don't resolve private attributes
        if attr.startswith("_"):
            raise AttributeError(f"{type(self).__name__} has no attribute '{attr}'")

        try:  # grid
            return getattr(self.grid, attr)
        except AttributeError:
            pass
        try:  # metadata
            return getattr(self.metadata, attr)
        except AttributeError:
            pass
        try:  # data from last simulation step
            return self[-1][attr]
        except KeyError:
            pass

        raise AttributeError(f"{type(self).__name__} has no attribute '{attr}'")

    def _index(self, key: int) -> int:
        """Checks if index is in range and implements negative indexing"""
        if not isinstance(key, (int, np.integer)):
            raise IndexError("Data index has to be an integer")
        elif key >= len(self):
            raise IndexError("Data index out of range")
        elif key < 0:
            key = self._index(len(self) + key)
            if key < 0:
                raise IndexError("Data index out of range")
        return key

    def __getitem__(self, key: int) -> DataObject:
        """Access individual data frames, return them as PlutoData

        If file is already loaded, object is returned, otherwise data is loaded and returned
        """
        return self.get(key)

    def get(self, key: int, keep: bool = True) -> DataObject:
        """Get PLUTO output

        Access individual data frames as PlutoData object. If `keep=True` the object is cached.

        Args:
            key (int): Output number
            keep (:obj:`bool`, optional): Keep output step in memory

        Returns:
            :obj:`Simulation.DataObject` (by default: :obj:`PlutoData`)
        """
        key = self._index(key)

        try:
            return self._data[key]
        except KeyError:
            # load data frame
            data = self._load_data(key)
            if keep:
                self._data[key] = data
            return data

    def __delitem__(self, key: int):
        """Delete data object to free memory"""
        key = self._index(key)
        try:
            del self._data[key]
        except KeyError:
            pass

    def _load_data(self, key: int) -> DataObject:
        """Load data frame"""
        return self.DataObject(
            self._index(key), metadata=self.metadata, grid=self.grid, simulation=self
        )

    def __iter__(self) -> "SimulationIterator":
        """Iterate over all data frames"""
        return self.iter()

    def iter(self, *range_, keep: bool = False) -> "SimulationIterator":
        """Iterate over simulation

        Range argument definition the same as `range()`.

        Attributes:
            simulation (plutoplot.simulation.Simulation): Simulation to iterate
            keep (bool): Whether to keep the PlutoData objects in memory
            start (int): Iteration start
            stop (int): Iteration stop (exclusive)
            step (int): Iteration step

        Returns:
            SimulationIterator
        """
        return SimulationIterator(self, *range_, keep=keep)

    def reduce(
        self,
        func,
        range=(),
        dtype=None,
    ):
        """Reduce all simulation steps with function.

        Shape and dtype are implied from return value of `func()`.

        Args:
            func (function): function which takes a PlutoData object and returns scalar or numpy array.
            dtype (numpy.dtype): forced data type for result array (if None func() implies dtype)
            range (tuple): range tuple for iterator.

        Returns:
            numpy.ndarray: reduced data array
        """
        # run on first element to get shape and dtype
        first = np.array(func(self[0]))
        if dtype is None:
            dtype = first.dtype
        #
        if first.shape == () or first.shape == (1,):
            return np.fromiter(
                (func(d) for d in self.iter(*range)),
                dtype=dtype,
                count=len(self.iter(*range)),
            )
        else:
            shape = (len(self.iter(*range)), *first.shape)
            res = np.empty(shape, dtype=dtype)
            for i, d in enumerate(self.iter(*range)):
                res[i] = func(d)
            return res

    def reduce_parallel(self, func, range=(), processes=None, dtype=None):
        """Reduce all simulation steps with function in parallel

        Shape and dtype are implied from return value of `func()`.

        Args:
            func (function): function which takes a PlutoData object and returns scalar or numpy array.
            dtype (numpy.dtype): forced data type for result array (if None func() implies dtype)
            range (tuple): range tuple for iterator.

        Returns:
            numpy.ndarray: reduced data array
        """
        first = np.array(func(self[0]))
        if dtype is None:
            dtype = first.dtype

        shape = (len(self.iter(*range)), *first.shape)
        res = np.empty(shape, dtype=dtype)
        with multiprocessing.Pool(processes) as p:
            for i, d in enumerate(p.imap(func, self.iter(*range))):
                res[i] = d
        return res

    def plot(self, *args, n: int = -1, **kwargs) -> None:
        """
        Plot last data file, or data file n. All other arguments forwarded to PlutoData.plot()
        """
        return self[n].plot(*args, **kwargs)

    def iplot(self, *args, n: int = -1, **kwargs) -> None:
        """
        Plot simulation interactively. All other arguments forwarded to PlutoData.plot()
        No return, because it would interfere with interactive output in Jupyter Notebook
        """

        # Use widget to choose timestep if inside Jupyter Notebook
        try:
            get_ipython
            import ipywidgets as widgets

            def handler(i):
                self[i].plot(*args, **kwargs)

            plot = widgets.interactive(
                handler,
                i=widgets.IntSlider(min=0, max=len(self) - 1, value=self._index(n)),
            )
            plot.children[0].description = "Simulation frame"
            plot.children[0].layout.width = "40%"
            display(plot)

        except NameError:
            raise RuntimeError(
                "Code has to be run in Jupyter Notebook for interactive plotting"
            )

    def __len__(self) -> int:
        return self.metadata.length

    def clear(self) -> None:
        """Clear loaded data frames"""
        self._data.clear()

    def __str__(self) -> str:
        return (
            f"PLUTO simulation at '{self.path}'\n"
            f"Data directory at '$SIM_DIR/{self.data_path.relative_to(self.path)}'\n"
            f"{self.grid.coordinates.capitalize()} grid with dimensions {self.dims}\n"
            f"Domain: x1: {self.x1l[0]:.2e} .. {self.x1r[-1]:.2e} (Lx1 = {self.Lx1:.2e})\n"
            f"        x2: {self.x2l[0]:.2e} .. {self.x2r[-1]:.2e} (Lx2 = {self.Lx2:.2e})\n"
            f"        x2: {self.x3l[0]:.2e} .. {self.x3r[-1]:.2e} (Lx3 = {self.Lx3:.2e})\n"
            f"Available variables: {' '.join(self.vars)}\n"
            "Data files:\n"
            f"    Format {self.format}: {len(self)} files, "
            f"last time {self.t[-1]}, data timestep {self.dt.mean():.2e}\n"
        )

    def __repr__(self) -> str:
        return (
            f"{type(self).__name__}('{self.path}', format='{self.metadata.format}', "
            f"coordinates='{self.grid.coordinates}')"
        )

    def _repr_markdown_(self) -> str:
        """Jupyter pretty print"""
        return (
            f"**PLUTO simulation** path: `{self.path}`, "
            f"data directory `$sim_path/{self.data_path.relative_to(self.path)}`  \n"
            f"Data vars: `{'` `'.join(self.metadata.vars)}`  \n"
            f"Data files: Format `{self.format}`: {len(self)} files,"
            f"last time {self.t[-1]}, data timestep {self.dt.mean():.2e}  \n"
        ) + self.grid._repr_markdown_()

    def __dir__(self) -> list:
        return (
            object.__dir__(self)
            + self.metadata.vars
            + [attr for attr in dir(self.grid) if not attr.startswith("_")]
            + [attr for attr in dir(self.metadata) if not attr.startswith("_")]
            + list(self.grid.mapping_vars)
        )


class SimulationIterator:
    """Iterator for Simulation

    Range definition the same as `range()`.

    Attributes:
        simulation (plutoplot.simulation.Simulation): Simulation to iterate
        keep (bool): Whether to keep the PlutoData objects in memory
        start (int): Iteration start
        stop (int): Iteration stop (exclusive)
        step (int): Iteration step

    Yields:
        PlutoData
    """

    def __init__(self, simulation: Simulation, *range_, keep: bool = False):
        """Create SimulationIterator

        Args:
            simulation (plutoplot.simulation.Simulation): Simulation to iterate
            *range_ (int): (), `stop` or `start, stop` or `start, stop, step`
            keep (bool): Whether to keep the PlutoData objects in memory
        """
        self.simulation = simulation
        self.keep = keep
        self.start, self.stop, self.step = 0, len(self.simulation), 1
        if len(range_) == 1:
            self.stop = self.simulation._index(range_[0])
        elif len(range_) == 2:
            self.start = self.simulation._index(range_[0])
            self.stop = self.simulation._index(range_[1])
        elif len(range_) == 3:
            self.start = self.simulation._index(range_[0])
            self.stop = self.simulation._index(range_[1])
            self.step = self.simulation._index(range_[2])
        elif len(range_) > 3:
            raise TypeError("Too many arguments for SimulationRange")

        self._iterator = iter(range(self.start, self.stop, self.step))

    def __len__(self):
        return len(range(self.start, self.stop, self.step))

    def __next__(self):
        return self.simulation.get(next(self._iterator), keep=self.keep)

    def __iter__(self):
        return self

    def __repr__(self) -> str:
        return (
            f"{type(self).__name__}({repr(self.simulation)}, {self.start}, "
            f"{self.stop}, {self.step}, keep={self.keep})"
        )
