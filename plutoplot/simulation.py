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
    def __init__(self, wdir: str=''):
        self.wdir = wdir
        self.read_vars()
        self.read_grid()

        # dict for individual data frames
        self.data = {}

    def read_vars(self):
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

        self.x1, self.dx1 = x[0]
        self.x2, self.dx2 = x[1]
        self.x3, self.dx3 = x[2]

    def __getitem__(self, key):
        """
        Access individual data frames, returns them as PlutoData
        If file is already loaded, object is returned, otherwise data is loaded
        """
        try:
            return self.data[key]
        except KeyError:
            if key >= self.n:
                raise IndexError('Data index out of range')

            # Construct PlutoData object manually
            D = PlutoData(wdir=self.wdir, part_of_sim=True)
            # vars
            D.vars = self.vars
            D.n, D.t, D.dt, D.nstep = key, self.t[key], self.dt[key], self.nstep[key]
            # grid
            D.x1, D.x2, D.x3 = self.x1, self.x2, self.x3
            D.dx1, D.dx2, D.dx3 = self.dx1, self.dx2, self.dx3
            D.dims = self.dims
            # read Data
            D.read_data()
            self.data[key] = D
            return D

    def __iter__(self):
        """Iterate over all data frames"""
        for i in range(self.n):
            yield self[i]
