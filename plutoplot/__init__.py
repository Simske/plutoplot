from ._version import get_versions

__version__ = get_versions()["version"]
del get_versions

from matplotlib.pyplot import show

from . import misc
from .plutodata import PlutoData
from .simulation import Simulation
