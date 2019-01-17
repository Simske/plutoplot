import numpy as np
from collections import OrderedDict
from itertools import zip_longest

from .coordinates import generate_coordinate_mesh

class Grid:
    """
    dims: dimensions
    shape: shape of arrays
    size: total cells
    """

    def __init__(self, gridfile):
        self.coordinates = None
        self.mappings = {}
        self.mappings_tex = {}
        self.read_gridfile(gridfile)

    def set_coordinate_system(self, coordinates, mappings={}, mappings_tex={}):
        self.coordinates = coordinates
        self.mappings = mappings
        self.mappings_tex = mappings_tex

    def read_gridfile(self, gridfile_path) -> None:
        x = []
        dims = []
        with open(gridfile_path, 'r') as gf:
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
                    dims.append(dim)
                    # read all data from dimension, moves file pointer
                    data = np.fromfile(gf, sep=' ', count=dim*3).reshape(-1, 3)
                    # calculate center of cell, and difference between cells
                    x.append((np.sum(data[:, 1:], axis=1)/2, data[:, 2] - data[:, 1]))

        # save in grid datastructure
        for i, xn in enumerate(x, start=1):
            setattr(self, f"x{i}", xn[0])
            setattr(self, f"dx{i}", xn[1])
        self.dims = tuple(dims)

        shape = []
        if self.dims[0] > 1:
            shape.append(self.dims[0])
        if self.dims[1] > 1:
            shape.append(self.dims[1])
        if self.dims[2] > 1:
            shape.append(self.dims[2])
        self.data_shape = tuple(shape)

        self.size = np.product(self.dims)

    def mesh(self):
        return generate_coordinate_mesh(self.coordinates, self.x1, self.x2)

    def __getattr__(self, name):
        try:
            mappings = object.__getattribute__(self, 'mappings')
            return object.__getattribute__(self, mappings[name])
        except KeyError:
            raise AttributeError(f"{type(self)} has no attribute '{name}'")

    def __str__(self):
        return f"PLUTO Grid, Dimensions {self.dims}"
    __repr__ = __str__


class SimulationMetadata:
    def __init__(self, path, format) -> None:
        self.read_vars(path, format)

    def read_vars(self, path, format) -> None:
        """Read simulation step data and written variables"""
        with open(path, 'r') as f:
            lines = f.readlines()
            self.n = len(lines)
            # prepare arrays
            self.t = np.empty(self.n, float)
            self.dt = np.empty(self.n, float)
            self.nstep = np.empty(self.n, int)
            # information for all steps the same
            file_mode, endianness, *self.vars = lines[0].split()[4:]

            for i, line in enumerate(lines):
                self.t[i], self.dt[i], self.nstep[i] = line.split()[1:4]

            if file_mode == 'single_file':
                self.file_mode = 'single'
            elif file_mode == 'multiple_files':
                self.file_mode = 'multiple'

            self.charsize = 8 if format == 'dbl' else 4
            endianness = '<' if endianness == 'little' else '>'
            self.binformat = f"{endianness}f{self.charsize}"

class Pluto_ini(OrderedDict):
    """Parser for Plutocode initialization file pluto.ini"""

    class Section(OrderedDict):
        def __init__(self, name):
            super().__init__()
            self.name = name

        def _align(self):
            length = []
            for key, value in self.items():
                if isinstance(value, str):
                    length.append((len(key), len(value)))
                else:
                    length.append((len(key), *[len(v) for v in value]))
            return [max(i) for i in zip_longest(*length, fillvalue=0)]

        def __str__(self):
            colwidth = self._align()
            out = "[{}]\n".format(self.name)
            for key, value in self.items():
                out += "{}{}\n".format(rpad([key], colwidth), lpad(value, colwidth[1:]))
            return out


    def __init__(self, path):
        super().__init__()
        self.path = path

        self.parse()

    def parse(self, txt=None):
        if txt is None:
            with open(self.path, 'r') as f:
                lines = [l.strip() for l in f.readlines()]
        else:
            lines = [l.strip() for l in txt.split("\n")]

        section = None
        for line in lines:
            if not line:
                continue
            elif line[0] == '[' and line[-1] == ']':
                section = line[1:-1]
                self[section] = self.Section(section)
            else:
                segments = line.split()
                if len(segments) > 2:
                    self[section][segments[0]] = segments[1:]
                else:
                    self[section][segments[0]] = segments[1]

    def __str__(self):
        out = ""
        for section in self.values():
            out += str(section) + "\n\n"
        return out

    def write(self, path=None):
        if path is None:
            path = self.path

        with open(path, 'w') as f:
            f.write(str(self))


def rpad(text, colwidth):
    if isinstance(text, str):
        text = [text]
    out = ""
    for txt, col in zip(text, colwidth):
        pad = col - len(txt) + 1
        out += txt + " " * pad
    return out

def lpad(text, colwidth, spacer=2):
    if isinstance(text, str):
        text = [text]
    out = ""
    for txt, col in zip(text, colwidth):
        pad = col - len(txt) + spacer
        out += " " * pad + txt
    return out


class Definitions_h(OrderedDict):

    base_opt = ['physics', 'dimensions', 'components', 'geometry', 'body_force',
                'forced_turb', 'cooling', 'reconstruction', 'time_stepping',
                'dimensional_splitting', 'ntracer', 'user_def_parameters']
    physics_dep = {'hd': ['eos', 'entropy_switch', 'thermal_conduction', 'viscosity', 'rotating_frame'],
                   'rhd': ['eos', 'entropy_switch'],
                   'mhd': ['eos', 'entropy_switch', 'divb_control', 'background_field',
                           'ambipolar_diffusion', 'resistivity', 'hall_mhd',
                           'thermal_conduction', 'viscosity', 'rotating_frame'],
                   'rmhd': ['eos', 'entropy_switch', 'divb_control', 'resistivity'],
                   'cr_transport': ['eos', 'anisotropy'],
                   'advection': []}


    def __init__(self, path: str):
        super().__init__()
        self.path = path
        self.parse()

    def parse(self, txt: str=None) -> None:
        with open(self.path, 'r') as f:
            lines = [l.strip() for l in f.readlines()]


        for line in lines:
            if not line:
                continue
            segments = line.split()
            if segments[0] == "#define":
                self[segments[1].lower()] = segments[2].lower()

    def __getitem__(self, key):
        return super().__getitem__(key.lower())

    def __setitem__(self, key, value):
        super().__setitem__(key.lower(), value)
