
# local imports
from .plutodata import PlutoData
from .simulation import Simulation

def render_frames(sim: Simulation, plot_func, output_path: str='', plot_args: dict={'vmin': None, 'vmax': None}, save_args: dict={'bbox_inches': 'tight'}):
    for frame in sim.memory_iter():
        fig = plot_func(frame, **plot_args)
        fig.savefig(f"{output_path}{frame.n:04d}.png", **save_args)
