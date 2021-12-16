from ._version import get_versions

__version__ = get_versions()["version"]
del get_versions

from matplotlib.pyplot import show

from . import misc
from .grid import Grid
from .metadata import Definitions_h, Pluto_ini
from .plutodata import PlutoData
from .simulation import Simulation
