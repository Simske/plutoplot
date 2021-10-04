import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import ScalarFormatter
from mpl_toolkits.axes_grid1 import make_axes_locatable

from .grid import Grid, GridSlice


def plot(
    data: np.ndarray,
    grid: Grid,
    *,
    ax=None,
    label: str = None,
    figsize=None,
    cbar=True,
    projection: bool = True,
    **mpl_kwargs,
) -> None:
    """Simple colorplot for 2-dim data"""

    if isinstance(grid, GridSlice) and data.shape == grid.shape:
        data = data[grid.slice]
    elif data.shape == grid.shape:
        pass
    else:
        raise RuntimeError("Plotting: Grid shape not compatible with data")

    if len(grid.rdims) == 1:
        if ax is None:
            if figsize is None:
                figsize = (16, 10)
            _, ax = plt.subplots(figsize=figsize)

        ax.set_xlabel(f"${grid.mapping_tex[f'x{grid.rdims_ind[0]+1}']}$")
        ax.set_ylabel(label)
        ax.grid()

        ax.plot(grid.xn[grid.rdims_ind[0]], data[grid.rmask], label=label, **mpl_kwargs)

    elif len(grid.rdims) == 2:
        if projection:
            (xlabel, ylabel), (X, Y) = grid.mesh_edge_cartesian

        else:
            xlabel = f"{grid.mapping_tex[f'x{grid.rdims_ind[0]+1}']}"
            ylabel = f"{grid.mapping_tex[f'x{grid.rdims_ind[1]+1}']}"
            X, Y = grid.mesh_edge

        if ax is None:
            if figsize is None:
                # set a figsize depending on aspect ratio
                ratio = (X.max() - X.min()) / (Y.max() - Y.min())
                if ratio < 16 / 9:
                    y_size = 10
                    x_size = y_size / ratio * 1.1
                else:
                    x_size = 16
                    y_size = x_size * ratio / 1.1
                figsize = (x_size, y_size)
            _, ax = plt.subplots(figsize=figsize)

        ax.set_xlabel(f"${xlabel}$")
        ax.set_ylabel(f"${ylabel}$")

        im = ax.pcolormesh(X, Y, data[grid.rmask], **mpl_kwargs)
        ax.set_aspect(1)
        if cbar:
            formatter = ScalarFormatter()
            formatter.set_powerlimits((-2, 2))
            divider = make_axes_locatable(ax)
            cax = divider.append_axes("right", size=0.05, pad=0.05)
            plt.colorbar(im, label=label, format=formatter, cax=cax)

            # plt.colorbar(im, label=label, format=formatter, ax=ax, pad=0.05)

    elif len(grid.rdims) == 3:
        raise NotImplementedError("3D plotting not supported (yet)")

    return ax.figure, ax
