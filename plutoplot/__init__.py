try:
    import importlib.metadata

    __version__ = importlib.metadata.version("plutoplot")
    del importlib
except ImportError:  # Python <3.8
    import pkg_resources

    __version__ = pkg_resources.get_distribution("plutoplot").version
    del pkg_resources


from . import misc
from .grid import Grid
from .metadata import Definitions_h, Pluto_ini
from .plutodata import PlutoData
from .simulation import Simulation
