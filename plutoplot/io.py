import numpy as np
from collections import OrderedDict
from itertools import zip_longest
from pathlib import Path

class SimulationMetadata:
    def __init__(self, data_dir: Path, format: str) -> None:
        self.read_vars((Path(data_dir) / format).with_suffix(".out"), format)

        # read VTK offsets in file
        if format == "vtk":
            if self.file_mode == "single":
                self.vtk_offsets = vtk_offsets(data_dir / "data.0000.vtk")
            else:
                self.vtk_offsets = {}
                for var in self.vars:
                    self.vtk_offsets.update(
                        vtk_offsets((data_dir / var).with_suffix(".0000.vtk"))
                    )

    def read_vars(self, path: Path, format) -> None:
        """Read simulation step data and written variables"""
        with path.open() as f:
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

            if file_mode == "single_file":
                self.file_mode = "single"
            elif file_mode == "multiple_files":
                self.file_mode = "multiple"

            self.charsize = 8 if format == "dbl" else 4
            endianness = "<" if endianness == "little" else ">"
            if format == "vtk":
                endianness = ">"  # VTK has always big endian
            self.binformat = "{}f{}".format(endianness, self.charsize)


def vtk_offsets(path: Path) -> dict:
    """
    Read positions of vars in VTK legacy file
    """
    offsets = {}
    with path.open("rb") as f:
        for l in f:
            if not l or l == b"\n":
                continue

            split = l.split()

            # skip coordinates (read in via gridfile)
            if split[0] in [i + b"_COORDINATES" for i in [b"X", b"Y", b"Z"]]:
                f.seek(int(split[1]) * 4 + 1, 1)

            if split[0] == b"CELL_DATA":
                bytesize = int(split[1]) * 4

            # save position of variables
            if split[0] == b"SCALARS":
                var = split[1].decode()
                f.readline()  # skip "LOOKUP_TABLE"
                offsets[var] = f.tell()
                f.seek(bytesize, 1)

    return offsets


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
            out = "[{}]\n\n".format(self.name)
            for key, value in self.items():
                out += "{}{}\n".format(rpad([key], colwidth), lpad(value, colwidth[1:]))
            return out

    def __init__(self, path: Path):
        super().__init__()
        self.path = Path(path)

        self.parse()

    def parse(self, txt=None):
        if txt is None:
            with self.path.open() as f:
                lines = [l.strip() for l in f.readlines()]
        else:
            lines = [l.strip() for l in txt.split("\n")]

        section = None
        for line in lines:
            if not line:
                continue
            elif line[0] == "[" and line[-1] == "]":
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

        with open(path, "w") as f:
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

    base_opt = [
        "physics",
        "dimensions",
        "components",
        "geometry",
        "body_force",
        "forced_turb",
        "cooling",
        "reconstruction",
        "time_stepping",
        "dimensional_splitting",
        "ntracer",
        "user_def_parameters",
    ]
    physics_dep = {
        "hd": [
            "eos",
            "entropy_switch",
            "thermal_conduction",
            "viscosity",
            "rotating_frame",
        ],
        "rhd": ["eos", "entropy_switch"],
        "mhd": [
            "eos",
            "entropy_switch",
            "divb_control",
            "background_field",
            "ambipolar_diffusion",
            "resistivity",
            "hall_mhd",
            "thermal_conduction",
            "viscosity",
            "rotating_frame",
        ],
        "rmhd": ["eos", "entropy_switch", "divb_control", "resistivity"],
        "cr_transport": ["eos", "anisotropy"],
        "advection": [],
    }

    def __init__(self, path: str):
        super().__init__()
        self.path = Path(path)
        self.parse()

    def parse(self, txt: str = None) -> None:
        with self.path.open() as f:
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
