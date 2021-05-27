"""Classes for PLUTO simulation Metadata and parsing of input files.

- :obj:`SimulationMetadata` reads PLUTO `*.out` files
- :obj:`PlutoIni` reads `pluto.ini` initialization files
- :obj:`Definitions_h` reads `definitions.h` compile time PLUTO configuration

"""
from collections import OrderedDict
from itertools import zip_longest
from pathlib import Path
from typing import Dict, List

import numpy as np


class SimulationMetadata:
    """Pluto simulation metadata reader and parser

    Read metadata from `format.out` files (e.g. `dbl.out`, `flt.out`).

    Attributes:
        path (Path): path to outputfile
        file_mode (str): PLUTO output in `"single"` or `"multiple"` files.
        vtk_offsets (:obj:`dict` of :obj:`int`): Byte offsets of data in VTK file
        t (:obj:`numpy.ndarray` of `numpy.float64`): simulation time of outputs
        dt (:obj:`numpy.ndarray` of `numpy.float64`): simulation time difference of outputs
        sim_dt (:obj:`numpy.ndarray` of `numpy.float64`): simulation timestep at outputs
        nstep (:obj:`numpy.ndarray` of `numpy.float64`): simulation step at outputs
        file_mode (str): `"single"` or `"multiple"`, PLUTO output mode for format
        vars (:obj:`list` of :obj:`str`): Variables available in output
        charsize (int): size of floating point number in bytes (4 or 8)
        binformat (str): binary format descriptor
    """

    def __init__(self, path: Path, format: str):
        """Read PLUTO simulation metadata from file

        Args:
            path (Path): path to outputfile or data directory. If this is a directory
                path, then the file at `{path}/{format}.out` will be read.
            format (Path): output format, e.g. `dbl`, `flt`, `vtk`
            length (int): number of outputs

        """
        self.path = Path(path)
        self.format = format
        if self.path.is_dir():
            self.path = self.path / f"{format}.out"
        self.data_path = self.path.parent

        self.read_vars(self.path, format)

        # read VTK offsets in file
        if format == "vtk":
            if self.file_mode == "single":
                self.vtk_offsets = vtk_offsets(self.path.parent / "data.0000.vtk")
            else:
                self.vtk_offsets = {}
                for var in self.vars:
                    self.vtk_offsets.update(
                        vtk_offsets(self.path.parent / f"{var}.0000.vtk")
                    )

    def read_vars(self, path: Path, format: str) -> None:
        """Read simulation step data and written variables

        Attributes set in this method are described in class docstring.

        Args:
            path (path): path to output file (`format.out`)
            format (str): PLUTO output format
        """
        with path.open() as f:
            lines = f.readlines()
            self.length = len(lines)
            # prepare arrays
            self.t = np.empty(self.length, float)
            self.sim_dt = np.empty(self.length, float)
            self.nstep = np.empty(self.length, int)

            # this information should be the same for all outputs
            file_mode, endianness, *self.vars = lines[0].split()[4:]
            self.file_mode = "single" if file_mode == "single_file" else "multiple"
            # binary format
            self.charsize = 8 if format == "dbl" else 4
            endianness = "<" if endianness == "little" else ">"
            if format == "vtk":
                endianness = ">"  # VTK has always big endian
            self.binformat = "{}f{}".format(endianness, self.charsize)

            # metadata for single timesteps
            for i, line in enumerate(lines):
                self.t[i], self.sim_dt[i], self.nstep[i] = line.split()[1:4]
            self.dt = self.t[1:] - self.t[:-1]

    def __repr__(self):
        return f"{type(self).__name__}('{self.path}','{self.format}')"


def vtk_offsets(path: Path) -> Dict[str, int]:
    """Read positions of vars in VTK legacy file

    Legacy VTK files contain header und binary data. This function
    extracts the byte offsets for the variables from the header

    Args:
        path (Path): path to VTK file

    Returns:
        :obj:`dict` of :obj:`str`: :obj:`int`: Byte offsets for variable data
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
    """PLUTO runtime initialization parameters pluto.ini

    Parses and writes `pluto.ini` files.
    Access with dict-like interfaces:
    - `ini["section"]["name"]`
    - `ini["section", "name"]`
    - `ini["section/name"]`

    Example:
        >>> ini = Pluto_ini(path)
        >>> ini["Time"]["tstop"]

    Attributes:

    """

    sections = OrderedDict.values

    class Section(OrderedDict):
        """Pluto_ini Section

        Thin wrapper around :obj:`OrderedDict`, with some convenience functions.

        Attributes;
            name (str): name of section
        """

        def __init__(self, name, *args, **kwargs):
            """Create Pluto_ini section

            Args:
                name (str): name of section
                *args, **kwargs: passed to :obj:`OrderedDict` constructor
            """
            super().__init__(*args, **kwargs)
            self.name = name

        def _align(self) -> List[int]:
            """Find column widths for aligned section"""
            length = []
            for key, value in self.items():
                if isinstance(value, str):
                    length.append((len(key), len(value)))
                else:
                    length.append((len(key), *[len(v) for v in value]))
            return [max(i) for i in zip_longest(*length, fillvalue=0)]

        def __str__(self) -> str:
            """Output Section in pluto.ini format with aligned columns"""
            colwidth = self._align()
            out = f"[{self.name}]\n\n"
            for key, values in self.items():
                out += f"{key:<{colwidth[0]}}"
                values = values if isinstance(values, list) else [values]
                for width, value in zip(colwidth[1:], values):
                    out += f"  {value:>{width}}"
                out += "\n"
            return out

        def _repr_html_(self) -> str:
            """Pretty printing in Jupyter"""
            return "<table>" + self._repr_html_inner() + "</table>"

        def _repr_html_inner(self) -> str:
            """Helper function for _repr_html_()"""
            out = f'<thead><tr><th colspan=2 style="text-align: left">{self.name}</th></tr></thead><tbody>'
            for key, value in self.items():
                if isinstance(value, list):
                    value = "&nbsp;&nbsp;".join(value)
                out += f"<tr><td>{key}</td><td>{value}</td></tr>"
            out += "</tbody>"
            return out

    def __init__(self, path: Path):
        """Load pluto.ini from file

        Args:
            path (Path): path to pluto.ini file
        """
        super().__init__()
        self.path = Path(path)

        self.parse()

    def parse(self, txt: str = None) -> None:
        """Parse pluto.ini file

        Args:
            txt (:obj:, optional): parse string instead of file
        """
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

    def __repr__(self) -> str:
        return f"{type(self).__name__}('{self.path}')"

    def _repr_html_(self) -> str:
        """Pretty printing in Jupyter"""
        return (
            f"<table>"
            + "".join(section._repr_html_inner() for section in self.sections())
            + "</table>"
        )

    def __str__(self) -> str:
        """Convert to pluto.ini format, with columns aligned inside sections"""
        return "\n\n".join(str(section) for section in self.sections())

    def __getitem__(self, key):
        """ini[key] with multiple syntaxes:

        - `ini["section"]`
        - `ini["section","key"]
        - `ini["section/key"]
        """
        if isinstance(key, tuple):
            return self[key[0]][key[1]]
        sep = key.find("/")
        if sep > -1:
            return self[key[:sep]][key[sep + 1 :]]
        return super().__getitem__(key)

    def __setitem__(self, key, value):
        """ini[key] = value
        For `key` syntax check `__getitem__()`
        """
        if isinstance(key, tuple):
            self[key[0]][key[1]] = value
        sep = key.find("/")
        if sep > -1:
            self[key[:sep]][key[sep + 1 :]] = value
        super().__setitem__(key, value)

    def write(self, path: Path = None) -> None:
        """Write pluto.ini to file.

        If no path is given, the read file is overwritten

        Args:
            path (:obj:`Path`, optional): Path to write to
        """
        if path is None:
            path = self.path

        with open(path, "w") as f:
            f.write(str(self))


class Definitions_h(OrderedDict):
    """PLUTO compile time definitions from definitions.h

    Todo:
        * Implement file writing (sections need to stay as is)
        * Better string output
    """

    def __init__(self, path: Path):
        """Load definitions.h from file

        Args:
            path (Path): path to definitions.h file
        """
        super().__init__()
        self.path = Path(path)
        self.parse()

    def parse(self, txt: str = None) -> None:
        """Parse defintions.h

        Args:
            txt (:obj:, optional): parse string instead of file
        """
        with self.path.open() as f:
            lines = [l.strip() for l in f.readlines()]

        for line in lines:
            if not line:
                continue
            segments = line.split()
            if segments[0] == "#define":
                self[segments[1]] = segments[2]

    def __repr__(self) -> str:
        return f"{type(self).__name__}('{self.path}')"

    def __str__(self) -> str:
        max_key = max(len(key) for key in self.keys())
        return "".join(f"{key:>{max_key}} = {value}\n" for key, value in self.items())

    def _repr_html_(self) -> str:
        """Pretty printing in Jupyter"""
        return (
            f"<table><tbody>"
            + "".join(
                f"<tr><td>{key}</td><td>{value}</td></tr>"
                for key, value in self.items()
            )
            + "</tbody></table>"
        )
