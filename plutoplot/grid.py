from pathlib import Path
from typing import Dict

import numpy as np

from plutoplot.misc import cached_property

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
        x1l, x2l, x3l (numpy.ndarray): left interfaces of grid (1d, not as mesh)
        x1r, x2r, x3r (numpy.ndarray): right interface of grid (1d, not as mesh)
        dx1, dx2, dx3 (numpy.ndarray): cell sizes (1d, not as mesh)

        r, z (numpy.ndarray): available if `coordinates == 'cylindrical'`, maps to x1, x2
        rl, zl (numpy.ndarray): available if `coordinates == 'cylindrical'`, maps to x1l, x2l
        rr, zr (numpy.ndarray): available if `coordinates == 'cylindrical'`, maps to x1r, x2r
        dr, dz (numpy.ndarray): available if `coordinates == 'cylindrical'`, maps to dx1, dx2

        r, phi, z (numpy.ndarray): available if `coordinates == 'polar'`, maps to x1, x2, x3
        rl, phil, zl (numpy.ndarray): available if `coordinates == 'polar'`, maps to x1l, x2l, x3l
        rr, phir, zr (numpy.ndarray): available if `coordinates == 'polar'`, maps to x1r, x2r, x3r
        dr, dphi, dz (numpy.ndarray): available if `coordinates == 'polar'`, maps to dx1, dx2, dx3

        r, theta, phi (numpy.ndarray): available if `coordinates == 'spherical'`, maps to x1, x2, x3
        rl, thetal, phil (numpy.ndarray): available if `coordinates == 'spherical'`, maps to x1l, x2l, x3l
        rr, thetar, phir (numpy.ndarray): available if `coordinates == 'spherical'`, maps to x1r, x2r, x3r
        dr, dtheta, dphi (numpy.ndarray): available if `coordinates == 'spherical'`, maps to dx1, dx2, dx3

    Todo:
        * Generalize and document meshgrid functions
    """

    def __init__(self, gridfile: Path, coordinates: str = None):
        """Initialize Grid from gridfile

        Args:
            gridfile (:obj:`str` or :obj:`Pathlike`): path to gridfile
            coordinates (:obj:`str`, optional): name of coordinate system (cartesian, polar,
                cylindrical, spherical). If not set this will be read from gridfile.
        """
        self.gridfile_path: Path = Path(gridfile)
        self.coordinates: str = None
        self.mapping_grid: Dict[str, str] = None
        self.mapping_vars: Dict[str, str] = None
        self.mapping_tex: Dict[str, str] = None

        # read gridfile, get coordinate system if necessary
        self.read_gridfile(gridfile, coordinates)

        if coordinates is not None:
            self.set_coordinate_system(coordinates)

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
            x1l, x2l, x3l (numpy.ndarray): left interfaces of grid (1d, not as mesh)
            x1r, x2r, x3r (numpy.ndarray): right interface of grid (1d, not as mesh)
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

        # save in grid datastructure
        for i, xn in enumerate(x, start=1):
            # cell interfaces
            setattr(self, f"x{i}l", xn[0])
            setattr(self, f"x{i}r", xn[1])
            # cell centers
            setattr(self, f"x{i}", (xn[0] + xn[1]) / 2)
            # cell widths
            setattr(self, f"dx{i}", xn[1] - xn[0])
            # domain width
            setattr(self, f"Lx{i}", xn[1][-1] - xn[0][0])
        self.dims = tuple(dims)

        self.data_shape = tuple(
            (self.dims[i] for i in range(2, -1, -1) if self.dims[i] > 1)
        )

        self.size = np.product(self.dims)

    def mesh_center(self):
        """
        2D cell center mesh in native coordinates
        Returns:
        X, Y with shape for each: (dim[1],dim[0])
        """
        return np.meshgrid(self.x1, self.x2)

    def mesh_edge(self):
        """
        2D cell edge mesh in native coordinates
        Returns:
        X, Y with shape for each: (dim[1]+1,dim[0]+1)
        """
        return np.meshgrid(
            np.append(self.x1l, self.x1r[-1]), np.append(self.x2l, self.x2r[-1])
        )

    def mesh_center_cartesian(self):
        """
        2D cell center mesh trasformed to cartesian coordinates
        Returns:
        X, Y with shape for each: (dim[1],dim[0])
        """
        return transform_mesh(self.coordinates, *self.mesh_center())

    def mesh_edge_cartesian(self):
        """
        2D cell edge mesh trasformed to cartesian coordinates
        Returns:
        X, Y with shape for each: (dim[1]+1,dim[0]+1)
        """
        return transform_mesh(self.coordinates, *self.mesh_edge())

    def __getattr__(self, name: str):
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

    def _repr_markdown_(self):
        return (
            f"**PLUTO Grid** Dimensions {self.dims}, {self.coordinates} coordinate system\n\n"
            "|   |   |   | L |\n"
            "|---|---|---|---|\n"
            f"|{self.mapping_tex['x1']}|{self.x1l[0]:.2f}|{self.x1r[-1]:.2f}|{self.Lx1:.2f}|\n"
            f"|{self.mapping_tex['x2']}|{self.x2l[0]:.2f}|{self.x2r[-1]:.2f}|{self.Lx2:.2f}|\n"
            f"|{self.mapping_tex['x3']}|{self.x3l[0]:.2f}|{self.x3r[-1]:.2f}|{self.Lx3:.2f}|\n"
        )

    def __dir__(self):
        return object.__dir__(self) + list(self.mapping_grid.keys())
