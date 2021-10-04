from pathlib import Path
from typing import Dict

import numpy as np

from plutoplot.misc import Slicer, cached_property

from .coordinates import mapping_grid, mapping_tex, mapping_vars, transform_mesh


class Grid:
    """Grid datastructure to be initialized from gridfile

    Attributes:
        gridfile_path (Path): Path to gridfile
        coordinates (str): Name of coordinate system
        mapping_grid (:obj:`dict` of :obj:`str`): mapping from coordinate system variable
            name to PLUTO variable names.
            (e.g. for spherical coordinates `r`->`x1`, `theta`->`x2`, `phi`->`x3`, )
        mapping_vars (:obj:`dict` of :obj:`str`): mapping from coordinate system variable
            attribute name to PLUTO variable names.
            (e.g. for spherical coordinates `vr`->`vx1`, `vtheta`->`vx2`, `vphi`->`vx3`)
        mapping_tex (:obj:`dict` of :obj:`str`): mapping from variable name to LaTeX names.

        dims (:obj:`tuple` of :obj:`int`): domain dimensions
        size (int): total size of data arrays (product of dims)

        x1, x2, x3 (numpy.ndarray): cell centered grid (1d, not as mesh)
        x1i, x2i, x3i (numpy.ndarray): cell interface coordinates (1d, not as mesh)
        dx1, dx2, dx3 (numpy.ndarray): cell sizes (1d, not as mesh)

        r, z (numpy.ndarray): available if `coordinates == 'cylindrical'`, maps to x1, x2
        ri, zi (numpy.ndarray): available if `coordinates == 'cylindrical'`, maps to x1i, x2i
        dr, dz (numpy.ndarray): available if `coordinates == 'cylindrical'`, maps to dx1, dx2

        r, phi, z (numpy.ndarray): available if `coordinates == 'polar'`, maps to x1, x2, x3
        ri, phii, zi (numpy.ndarray): available if `coordinates == 'polar'`, maps to x1i, x2i, x3i
        dr, dphi, dz (numpy.ndarray): available if `coordinates == 'polar'`, maps to dx1, dx2, dx3

        r, theta, phi (numpy.ndarray): available if `coordinates == 'spherical'`, maps to x1, x2, x3
        ri, thetai, phii (numpy.ndarray): available if `coordinates == 'spherical'`, maps to x1i, x2i, x3i
        dr, dtheta, dphi (numpy.ndarray): available if `coordinates == 'spherical'`, maps to dx1, dx2, dx3

    Todo:
        * Generalize and document meshgrid functions
    """

    def __init__(self, gridfile: Path, coordinates: str = None, indexing="ijk"):
        """Initialize Grid from gridfile

        Args:
            gridfile (:obj:`str` or :obj:`Pathlike`): path to gridfile
            coordinates (:obj:`str`, optional): name of coordinate system (cartesian, polar,
                cylindrical, spherical). If not set this will be read from gridfile.
            indexing (:obj:`str`, optional): index order for arrays. 'ijk' or 'kji'
        """
        self.gridfile_path: Path = Path(gridfile)
        self.coordinates: str = None
        self.mapping_grid: Dict[str, str] = None
        self.mapping_vars: Dict[str, str] = None
        self.mapping_tex: Dict[str, str] = None

        # helper function to transpose arrays if necessary
        if indexing == "ijk":
            self.T = lambda x: x.T  # transpose
        elif indexing == "kji":
            self.T = lambda x: x  # do nothing
        else:
            raise RuntimeError(f"Pluto Grid: indexing {indexing} not supported")
        self.indexing = indexing

        # read gridfile, get coordinate system if necessary
        self.read_gridfile(gridfile, coordinates)

        if coordinates is not None:
            self.set_coordinate_system(coordinates)

        self.slicer = Slicer(GridSlice, grid=self)
        self.slice = slice(None)

    def set_coordinate_system(self, coordinates: str) -> None:
        """Set coordinate system of grid and get name mapping

        Args:
            coordinates (str): name of coordinate system (cartesian, polar,
                                                          cylindrical, spherical)
        """
        self.coordinates = coordinates
        self.mapping_grid = mapping_grid(coordinates)
        self.mapping_vars = mapping_vars(coordinates)
        self.mapping_tex = mapping_tex(coordinates)

    def read_gridfile(self, gridfile_path: Path, coordinates: str = None) -> None:
        """Read and parse gridfile

        Args:
            gridfile_path (:obj:`str` or :obj:`Pathlike`): Path to PLUTO gridfile `grid.out`
            coordinates (:obj:`str`, optional): coordinate system name
                                                If not set this will be read from gridfile

        Sets Attributes:
            x1, x2, x3 (numpy.ndarray): cell centered grid (1d, not as mesh)
            x1i, x2i, x3i (numpy.ndarray): cell interfaces (1d, not as mesh)
            dx1, dx2, dx3 (numpy.ndarray): cell sizes (1d, not as mesh)
            Lx1, Lx2, Lx3 (numpy.ndarray): Domain width
            dims (:obj:`tuple` of :obj:`int`): domain dimensions
            data_shape (:obj:`tuple` of :obj:`int`): shape of data array.
                                                     Depends on index order
            size (int): total size of data arrays (product of dims)
        """
        # to be filled with left and right cell interfaces
        x = []
        dims = []
        with gridfile_path.open() as gf:
            # Gridfile header
            header = False  # marker if gf pointer is in header
            while True:
                line = gf.readline()
                if line.startswith("# *****"):
                    # header starts and ends with # *****...
                    # toggle marker when entering header
                    # and exit when header is finished
                    header = not header
                    if not header:
                        break
                # set coordinate system from gridfile if not explicitly set
                elif coordinates is None and line.startswith("# GEOMETRY"):
                    self.set_coordinate_system(line[11:].strip().lower())

            # read all dimensions
            while True:
                # read line by line, stop if EOF
                line = gf.readline()
                if not line:
                    break
                # find line with resolution in dimension
                splitted = line.split()
                if len(splitted) == 1:
                    dim = int(splitted[0])
                    dims.append(dim)
                    # read all data from dimension, moves file pointer
                    data = np.fromfile(gf, sep=" ", count=dim * 3).reshape(-1, 3)
                    # save left and right cell interface
                    x.append((data[:, 1], data[:, 2]))

        # cell centers
        self.xn = tuple((xn[0] + xn[1]) / 2 for xn in x)
        # cell interfaces
        self.xni = tuple(np.append(xn[0], xn[1][-1]) for xn in x)
        # cell widths
        self.dxn = tuple(x[1:] - x[:-1] for x in self.xni)
        # domain widths
        self.L = tuple(x[-1] - x[0] for x in self.xni)

        # reference in named attributes
        for i in range(3):
            setattr(self, f"x{i+1}", self.xn[i])
            setattr(self, f"x{i+1}i", self.xni[i])
            setattr(self, f"dx{i+1}", self.dxn[i])
            setattr(self, f"Lx{i+1}", self.L[i])

        self.dims = tuple(dims)
        # indices of dims which are not 1
        self.rdims = tuple(dim for dim in dims if dim > 1)
        self.rdims_ind = tuple(i for i, dim in enumerate(dims) if dim > 1)

        self.data_shape = tuple(reversed(dims))
        if self.indexing == "ijk":
            self.shape = self.dims
            self.rmask = tuple(slice(None) if dim > 1 else 0 for dim in self.dims)
        else:
            self.shape = tuple(reversed(self.dims))
            self.rmask = tuple(slice(None) if dim > 1 else 0 for dim in self.data_shape)

        self.size = np.product(self.dims)

    @cached_property
    def mesh_center(self):
        """n.dohrmann1300@gmail.com
        2D cell center mesh in native coordinates
        Returns:
        X, Y with shape for each: (dim[1],dim[0])
        """
        if len(self.rdims) == 1:
            return self.xn[self.rdims_ind[0]]
        elif len(self.rdims) == 2:
            X, Y = np.meshgrid(self.xn[self.rdims_ind[0]], self.xn[self.rdims_ind[1]])
            return self.T(X), self.T(Y)
        else:
            raise NotImplementedError("3D mesh not implemented yet")

    @cached_property
    def mesh_edge(self):
        """
        2D cell edge mesh in native coordinates
        Returns:
        X, Y with shape for each: (dim[1]+1,dim[0]+1)
        """
        if len(self.rdims) == 1:
            return self.xn[self.rdims_ind[0]]
        elif len(self.rdims) == 2:
            X, Y = np.meshgrid(self.xni[self.rdims_ind[0]], self.xni[self.rdims_ind[1]])
            return self.T(X), self.T(Y)
        else:
            raise NotImplementedError("3D mesh not implemented yet")

    @cached_property
    def mesh_center_cartesian(self):
        """TODO"""
        if len(self.rdims) != 2:
            raise NotImplementedError(
                "Projection to cartesian grid only implemented in 2D"
            )
        return transform_mesh(self, *self.mesh_center)

    @cached_property
    def mesh_edge_cartesian(self):
        """TODO"""
        if len(self.rdims) != 2:
            raise NotImplementedError(
                "Projection to cartesian grid only implemented in 2D"
            )
        return transform_mesh(self, *self.mesh_edge)

    def __getattr__(self, name: str):
        if name.startswith("_"):
            raise AttributeError(f"{type(self).__name__} has no attribute '{name}'")
        try:
            return getattr(self, self.mapping_grid[name])
        except KeyError:
            pass
        raise AttributeError(f"{type(self).__name__} has no attribute '{name}'")

    def __str__(self) -> str:
        return (
            f"PLUTO Grid, Dimensions {self.dims}, Coordinate System: {self.coordinates}"
        )

    def __repr__(self) -> str:
        return f'{type(self).__name__}("{self.gridfile_path}", "{self.coordinates}")'

    def _repr_markdown_(self) -> str:
        """Jupyter pretty print"""
        return (
            f"**PLUTO Grid** Dimensions {self.dims}, {self.coordinates} coordinate system\n\n"
            "|   |   |   | L | N |\n"
            "|---|---|---|---|---|\n"
            f"|${self.mapping_tex['x1']}$|{self.x1i[0]:.2f}|{self.x1i[-1]:.2f}|{self.Lx1:.2f}|{self.dims[0]}|\n"
            f"|${self.mapping_tex['x2']}$|{self.x2i[0]:.2f}|{self.x2i[-1]:.2f}|{self.Lx2:.2f}|{self.dims[1]}|\n"
            f"|${self.mapping_tex['x3']}$|{self.x3i[0]:.2f}|{self.x3i[-1]:.2f}|{self.Lx3:.2f}|{self.dims[2]}|\n"
        )

    def __dir__(self):
        return object.__dir__(self) + list(self.mapping_grid.keys())


class GridSlice(Grid):
    def __init__(self, grid: Grid, slice_):
        self.slice = normalize_slice(slice_, grid.shape)
        self.slicer = None

        self.gridfile_path = None
        self.set_coordinate_system(grid.coordinates)

        self.T = grid.T
        self.indexing = grid.indexing

        # reverse slice depending on indexing
        slice_ijk = reversed(self.slice) if self.indexing == "kji" else self.slice

        self.xn = tuple(x[sl] for sl, x in zip(slice_ijk, grid.xn))
        self.xni = tuple(
            x[sl.start : sl.stop + sl.step : sl.step]
            for sl, x in zip(slice_ijk, grid.xni)
        )
        self.dxn = tuple(x[1:] - x[:-1] for x in self.xni)
        self.L = tuple(x[-1] - x[0] for x in self.xni)

        # reference in named attributes
        for i in range(3):
            setattr(self, f"x{i+1}", self.xn[i])
            setattr(self, f"x{i+1}i", self.xni[i])
            setattr(self, f"dx{i+1}", self.dxn[i])
            setattr(self, f"Lx{i+1}", self.L[i])

        self.dims = tuple(len(x) for x in self.xn)
        self.rdims = tuple(dim for dim in self.dims if dim > 1)
        self.rdims_ind = tuple(i for i, dim in enumerate(self.dims) if dim > 1)

        self.data_shape = None
        if self.indexing == "ijk":
            self.rmask = tuple(slice(None) if dim > 1 else 0 for dim in self.dims)
            self.shape = self.dims
        else:
            self.rmask = tuple(
                slice(None) if dim > 1 else 0 for dim in reversed(self.dims)
            )
            self.shape = tuple(reversed(self.dims))

        self.size = grid.size

        # TODO repr and str


def normalize_slice(slice_: tuple, shape: tuple) -> tuple:
    """Check bounds of 3D slice, and preserve 3d structure of array
    for 1-high direction slice

    Args:
        slice_ (tuple): 3D slice, consisting of `int` and `slice`
        shape (tuple): dimensions of domain

    Returns:
        tuple

    Raises:
        IndexError: if any of the bounds check don't work
    """
    if len(slice_) != 3:
        raise IndexError("Please specify 3D slice for clarity")

    newslice = []
    for dimslice, dimsize in zip(slice_, shape):
        if isinstance(dimslice, slice):
            start, stop, step = dimslice.start, dimslice.stop, dimslice.step

            if start is None:
                start = 0
            elif start >= dimsize or start < -dimsize:
                raise IndexError("Slice out of bounds")
            elif start < 0:
                start = dimsize + dimslice.start

            if stop is None:
                stop = dimsize
            elif stop > dimsize or stop < -dimsize:
                raise IndexError("Slice out of bounds")
            elif stop < 0:
                stop = dimsize + stop

            if step is None:
                step = 1

            newslice.append(slice(start, stop, step))

        else:
            start = dimslice
            if start < 0:
                start = dimsize + dimslice
            if not (0 <= start < dimsize):
                raise IndexError("Slice out of bounds")

            newslice.append(slice(start, start + 1, 1))

    return tuple(newslice)
