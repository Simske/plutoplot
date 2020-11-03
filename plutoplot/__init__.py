from ._version import get_versions
__version__ = get_versions()['version']
del get_versions

from .plutodata import PlutoData
from .simulation import Simulation
from . import misc

from matplotlib.pyplot import show

from ._version import get_versions
__version__ = get_versions()['version']
del get_versions
