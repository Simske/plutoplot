import os
from os.path import join
import multiprocessing
import warnings
from typing import Generator, Tuple
import numpy as np
import matplotlib.pyplot as plt
# local imports
from .plutodata import PlutoData
from .grid import Grid
from .io import Pluto_ini, Definitions_h, SimulationMetadata
from .coordinates import generate_coord_mapping, generate_tex_mapping

# warnings.simplefilter("always")

class Simulation:
    """
    Container class for PLUTO (http://plutocode.ph.unito.it/) output.
    Reads the metadata of all files in working directory (wdir), and
    loads individual files when needed.
    Simulation is subscriptable and iterable.
    """
    supported_formats = ('dbl', 'flt', 'vtk')
    DataObject = PlutoData

    def __init__(self, sim_dir: str='', format: str=None, coordinates: str=None) -> None:
        self.sim_dir = sim_dir

        ## Find data directory ##
        if os.path.exists(join(sim_dir, 'grid.out')):
            self.data_dir = sim_dir
        elif os.path.exists(join(sim_dir, 'data', 'grid.out')):
            self.data_dir = join(sim_dir, 'data')
        else:
            try:
                from_ini = join(sim_dir, self.ini['Static Grid Output']['output_dir'], 'grid.out')
                if os.path.exists(from_ini):
                    self.data_dir = join(sim_dir)
                else:
                    raise FileNotFoundError()
            except FileNotFoundError:
                raise FileNotFoundError("Data directory with gridfile not found")

        ## Read grid ##
        self.grid = Grid(join(self.data_dir, 'grid.out'))

        # dict for individual data frames
        self._data = {}

        ## Find data format
        if format is None:
            for f in self.supported_formats:
                if os.path.exists(join(self.data_dir, f+'.out')):
                    self.format = f
                    break
            try:
                self.format
            except AttributeError:
                raise FileNotFoundError("No Metadata file for formats "
                    "{} found in {}".format(self.supported_formats, self.data_dir))
        else:
            if format not in self.supported_formats:
                raise NotImplementedError("Format '{}' not supported".format(format))
            if os.path.exists(join(self.data_dir, '{}.out'.format(format))):
                self.format = format
            else:
                raise FileNotFoundError("Metadata file {} "
                "for format {} not found".format(join(self.data_dir, format+'.out'), format))

        ## Read metadata ##
        self.metadata = SimulationMetadata(join(self.data_dir), self.format)
        self.vars = self.metadata.vars

        ## Read grid coordinate system ##
        if coordinates is None:
            coordinates = self.definitions['geometry']

        self.grid.set_coordinate_system(coordinates,
                                        mappings=generate_coord_mapping(coordinates),
                                        mappings_tex=generate_tex_mapping(coordinates))

    @property
    def ini(self) -> Pluto_ini:
        """Read access to PLUTO runtime initialization file 'pluto.ini'"""
        try:
            return self._ini
        except AttributeError:
            self._ini = Pluto_ini(join(self.sim_dir, 'pluto.ini'))
            return self._ini

    @property
    def definitions(self):
        """Read access to PLUTO compile time 'definitions.h' file"""
        try:
            return self._definitions
        except AttributeError:
            self._definitions = Definitions_h(join(self.sim_dir, 'definitions.h'))
            return self._definitions

    def __getattr__(self, name):
        """Resolve attributes to metadata/data/grid attributes"""
        getattribute = object.__getattribute__

        # metadata
        try:
            return getattr(getattribute(self, 'metadata'), name)
        except:
            pass

        # grid
        grid = getattribute(self, 'grid')
        try:
            return getattr(grid, name)
        except AttributeError:
            pass
        try:
            return getattribute(grid, 'mappings')[name]
        except KeyError:
            pass

        # vars
        try:
            if name in self.vars:
                return getattr(self[-1], name)
        except AttributeError:
            raise

        raise AttributeError("{} has no attribute '{}'".format(type(self), name))

    def _index(self, key: int) -> int:
        """Checks if index is in range and implements negative indexing"""
        if not isinstance(key, int):
            raise IndexError("Data index has to be int")
        elif key >= self.n:
            raise IndexError("Data index out of range")
        elif key < 0:
            key = self._index(self.n + key)
            if key < 0:
                raise IndexError("Data index out of range")
        return key

    def __getitem__(self, key: int) -> DataObject:
        """
        Access individual data frames, return them as PlutoData
        If file is already loaded, object is returned, otherwise data is loaded and returned
        """
        return self.get(key)

    def get(self, key: int, keep: bool=True) -> DataObject:
        """
        Access individual data frames, return them as PlutoData
        If file is already loaded, object is returned, otherwise data is loaded and returned
        if `keep=True`, object is kept in memory
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

    def _load_data(self, key: int) -> DataObject:
        """Load data frame"""
        return self.DataObject(n=self._index(key), simulation=self)

    def __iter__(self) -> Generator[DataObject, None, None]:
        """Iterate over all data frames"""
        return self.iter()

    def iter(self, start: int=0, stop: int=None, step: int=1, memory_keep: bool=False) -> Generator[DataObject, None, None]:
        """
        Iterate over data frames in range, (or all).
        start, stop, step [int]: works like range (start inclusive, stop exclusive)
        memory_keep [bool]: whether object should be kept in memory
        """
        start = self._index(start)
        stop = len(self) if stop is None else self._index(stop)
        for i in range(start, stop, step):
            yield self.get(i, memory_keep)

    def memory_iter(self, start=0, stop=-1, step=1) -> Generator[DataObject, None, None]:
        """Deprecated, use Simulation.iter() instead"""
        warnings.warn(
            "plutoplot.Simulation.memory_iter() is deprecated, use plutoplot.Simulation.iter()",
            DeprecationWarning)
        return self.iter()

    def reduce(self, func, dtype=None):
        """
        Reduce all simulation steps with function.
        shape and dtype are taken from return of func.
        Parameters:
         - func: function which takes a PlutoData object and returns scalar or numpy array.
         - dtype: forced data type for result array (if None func() implies dtype)
        Returns:
         - numpy.ndarray with datatype and shape implied from func
        """
        first = np.array(func(self[0]))
        if dtype is None:
            dtype = first.dtype
        if first.shape == () or first.shape == (1,):
            return np.fromiter((func(d) for d in self), dtype=dtype, count=len(self))
        else:
            shape = (len(self), *first.shape)
            res = np.empty(shape, dtype=dtype)
            for i, d in enumerate(self):
                res[i] = func(d)
            return res

    def reduce_parallel(self, func, processes=None, dtype=None):
        """
        Reduce all simulation steps with function in parallel.
        shape and dtype are taken from return of func.
        Parameters:
         - func: function which takes a PlutoData object and returns scalar or numpy array.
                 cannot be lambda function! (function needs to be pickled)
         - processes: number of processes for parallel computation
         - dtype: forced data type for result array (if None func() implies dtype)
        Returns:
         - numpy.ndarray with datatype and shape implied from func
        """
        first = np.array(func(self[0]))
        if dtype is None:
            dtype = first.dtype

        shape = (len(self), *first.shape)
        res = np.empty(shape, dtype=dtype)
        with multiprocessing.Pool(processes) as p:
            for i, d in enumerate(p.imap(func, self.iter())):
                res[i] = d
        return res

    def plot(self, *args, n: int=-1,  **kwargs) -> None:
        """
        Plot last data file, or data file n. All other arguments forwarded to PlutoData.plot()
        No return, because it would interfere with interactive output in Jupyter Notebook
        """

        # Use widget to choose timestep if inside Jupyter Notebook
        try:
            get_ipython
            import ipywidgets as widgets
            def handler(i):
                self[i].plot(*args, **kwargs)
            plot = widgets.interactive(handler, i=widgets.IntSlider(min=0,
                                                         max=len(self)-1,
                                                         value=self._index(n)))
            plot.children[0].description = "Simulation frame"
            plot.children[0].layout.width = "40%"
            display(plot)

        except (NameError, ImportError):
            self[n].plot(*args, **kwargs)

    def __len__(self) -> int:
        return self.n

    def __delitem__(self, key: int) -> None:
        """Delete data object to free memory"""
        del self._data[key]

    def clear(self) -> None:
        """Clear loaded data frames"""
        self._data.clear()

    def __str__(self) -> str:
        return """PLUTO simulation, sim_dir: '{sim_dir}',
        data_dir: '{data_dir}'
resolution: {dims}, {coord} coordinates
data files: {n}, last time: {t}
Variables: {self.vars}""".format(sim_dir=self.sim_dir, data_dir=self.data_dir,
        dims=self.dims, coord=self.grid.coordinates, n=self.n, t=self.t[-1],
        vars=self.vars)

    def __repr__(self) -> str:
        return "Simulation('{sim_dir}', format='{format}', coordinates='{coord}')".format(
            sim_dir=self.sim_dir, format=self.format, coord=self.grid.coordinates)

    def __dir__(self) -> list:
        return object.__dir__(self) + self.vars + dir(self.metadata) + dir(self.grid)

    def minmax(self, var: str='rho', range_: tuple=()) -> Tuple[float, float]:
        """
        Calculate minimum and maximum of var for sequence.
        var: pluto variable name
        range_: tuple of length <= 3, (start, stop, step) from iter()
        """
        min_ = np.inf
        max_ = -np.inf
        for frame in self.iter(*range_):
            temp_min = np.min(getattr(frame, var))
            temp_max = np.max(getattr(frame, var))
            if temp_min < min_: min_ = temp_min
            if temp_max > max_: max_ = temp_max
        return min_, max_
