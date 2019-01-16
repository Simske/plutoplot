import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import ScalarFormatter
from mpl_toolkits.axes_grid1 import make_axes_locatable

from .io import Grid

def plot(data: np.ndarray, grid: Grid, ax=None, label: str=None, figsize=None,
         cbar=True, vmin=None, vmax=None, cmap=None, projection: bool=True) -> None:
        """Simple colorplot for 2-dim data"""

        if ax is None:
            if figsize is None:
                x_size = 6.4
                y_size = x_size * grid.dims[1] / grid.dims[0] / 1.1
                figsize = (x_size, y_size)
            _, ax = plt.subplots(figsize=figsize)

        if projection:
            X, Y = grid.mesh()
            ax.set_xlabel('$x$')
            ax.set_ylabel('$y$')
        else:
            X, Y = grid.x1, grid.x2
            ax.set_xlabel(f"${grid.mappings_tex['x1']}$")
            ax.set_ylabel(f"${grid.mappings_tex['x2']}$")

        im = ax.pcolormesh(X, Y, data.T, vmin=vmin, vmax=vmax, cmap=cmap)
        ax.set_aspect(1)
        if cbar:
            formatter = ScalarFormatter()
            formatter.set_powerlimits((-2,2))
            divider = make_axes_locatable(ax)
            cax = divider.append_axes("right", size="10%", pad=0.05)
            plt.colorbar(im, label=label, format=formatter, cax=cax)

        return ax.figure, ax
