import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import ScalarFormatter
from mpl_toolkits.axes_grid1 import make_axes_locatable

from .grid import Grid


def plot(
    data: np.ndarray,
    grid: Grid,
    ax=None,
    label: str = None,
    figsize=None,
    cbar=True,
    vmin=None,
    vmax=None,
    cmap=None,
    projection: bool = True,
) -> None:
    """Simple colorplot for 2-dim data"""

    if len(grid.rdims) == 1:
        if ax is None:
            if figsize is None:
                figsize = (16, 10)
            _, ax = plt.subplots(figsize=figsize)

        ax.set_xlabel(f"${grid.mapping_tex[f'x{grid.rdims_ind[0]+1}']}$")
        ax.set_ylabel(label)
        ax.grid()

        ax.plot(grid.xn[grid.rdims_ind[0]], data[grid.rmask], label=label)

    elif len(grid.rdims) == 2:
        if ax is None:
            if figsize is None:
                y_size = 10
                x_size = y_size * grid.rdims[0] / grid.rdims[1] * 1.1
                figsize = (x_size, y_size)
            _, ax = plt.subplots(figsize=figsize)

        if projection:
            raise NotImplementedError("Projected plotting not implemented")
        else:
            ax.set_xlabel(f"${grid.mapping_tex[f'x{grid.rdims_ind[0]+1}']}$")
            ax.set_ylabel(f"${grid.mapping_tex[f'x{grid.rdims_ind[1]+1}']}$")
            X, Y = grid.xni[grid.rdims_ind[0]], grid.xni[grid.rdims_ind[1]]

        im = ax.pcolormesh(X, Y, data[grid.rmask], vmin=vmin, vmax=vmax, cmap=cmap)
        ax.set_aspect(1)
        if cbar:
            formatter = ScalarFormatter()
            formatter.set_powerlimits((-2, 2))
            divider = make_axes_locatable(ax)
            cax = divider.append_axes("right", size="10%", pad=0.05)
            plt.colorbar(im, label=label, format=formatter, cax=cax)

    elif len(grid.rdims) == 3:
        raise NotImplementedError("3D plotting not supported (yet)")

    return ax.figure, ax
