import os
import numpy as np
import matplotlib.pyplot as plt
from .plutodata import PlutoData

class Simulation:
    """
    Container class for PLUTO (http://plutocode.ph.unito.it/) outputself.
    Reads the metadata of all files in working directory (wdir), and
    loads individual files when needed.
    Simulation is subscriptable and iterable.
    """
    def __init__(self, wdir: str='', coordinates: str='cartesian'):
        self.wdir = wdir
        try:
            self.read_vars()
        except FileNotFoundError:
            self.wdir = os.path.join(wdir, 'data')
            self.read_vars()

        try:
            self.coordinate_system = coordinates
            self.coord_names = PlutoData._coordinate_systems[coordinates]
        except KeyError:
            raise KeyError('Coordinate system not recognized')

        self.read_grid()

        # dict for individual data frames
        self._data = {}

    def read_vars(self) -> None:
        """Read simulation step data and written variables"""
        with open(os.path.join(self.wdir, 'dbl.out'), 'r') as f:
            lines = f.readlines()
            self.n = len(lines)
            # prepare arrays
            self.t = np.empty(self.n, float)
            self.dt = np.empty(self.n, float)
            self.nstep = np.empty(self.n, int)

            self.vars = lines[0].split()[6:]

            for i, line in enumerate(lines):
                split = line.split()
                self.t[i], self.dt[i], self.nstep[i] = split[1:4]


    # Use read_grid() from PlutoData object
    read_grid = PlutoData.read_grid

    def _index(self, key: int) -> int:
        """Check if index is in range and implements negative indexing"""
        if not isinstance(key, int):
            raise IndexError("Data index has to be int")
        elif key >= self.n:
            raise IndexError("Data index out of range")
        elif key < 0:
            key = self._index(self.n + key)
            if key < 0:
                raise IndexError("Data index out of range")
        return key

    def __getitem__(self, key: int) -> PlutoData:
        """
        Access individual data frames, returns them as PlutoData
        If file is already loaded, object is returned, otherwise data is loaded
        """
        key = self._index(key)
        try:
            return self._data[key]
        except KeyError:
            # load data frame
            self._data[key] = self._load_data(key)
            return self._data[key]

    def _load_data(self, key: int) -> PlutoData:
        """Load data frame"""
        key = self._index(key)

        D = PlutoData(wdir=self.wdir, coordinates=self.coordinate_system,
                      vars=(self.vars, key, self.t[key], self.dt[key], self.nstep[key]),
                      grid=self.grid,
                      dims=self.dims)

        return D

    def __iter__(self):
        """Iterate over all data frames"""
        for i in range(self.n):
            yield self[i]

    def memory_iter(self, start=0, stop=-1, step=1):
        """
        Iterate over all data frames, deleting each after loop
        Takes arguments for start, stop, step
        """
        start = self._index(start)
        stop = self._index(stop)
        for i in range(start, stop+1, step):
            yield self._load_data(i)

    def __len__(self):
        return self.n

    def __delitem__(self, key: int) -> None:
        """Delete data object to free memory"""
        del self._data[key]

    def clear(self) -> None:
        """Clear loaded data frames"""
        self._data.clear()

    def __str__(self) -> str:
        return f"""PLUTO simulation, wdir: {self.wdir}
resolution: {self.dims},
data files: {self.n}, last time: {self.t[-1]}
Variables: {self.vars}"""

    def __repr__(self) -> str:
        return f"Simulation('{self.wdir}')"
