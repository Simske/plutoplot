import matplotlib.pyplot as plt
import multiprocessing
import os
import subprocess
# local imports
from .plutodata import PlutoData
from .simulation import Simulation

def parameter_generator(sim: Simulation, plot_func, output_path,
                        plot_args: dict={'vmin': None, 'vmax': None},
                        save_args: dict={'bbox_inches': 'tight'}):
    for i in range(sim.n):
        yield (sim, i, plot_func, output_path, plot_args, save_args)

def generate_frame(sim, i, plot_func, output_path, plot_args, save_args):
    fig = plot_func(sim[i], **plot_args)
    fig.savefig(f"{output_path}{i:04d}.png", **save_args)
    plt.close(fig)

def render_frames_parallel(sim: Simulation, plot_func, output_path: str='',
                  plot_args: dict={'vmin': None, 'vmax': None},
                  save_args: dict={'bbox_inches': 'tight'}):
    with multiprocessing.Pool() as p:
        p.starmap(generate_frame, parameter_generator(sim, plot_func, output_path,
                        plot_args, save_args))

def generate_animation(sim: Simulation, plot_func, output_name: str='animation.mp4',
                  framerate: int=25,
                  plot_args: dict={'vmin': None, 'vmax': None},
                  save_args: dict={'bbox_inches': 'tight'}):
    os.mkdir('tmp')
    render_frames_parallel(sim, plot_func, 'tmp/', plot_args, save_args)
    subprocess.run(['ffmpeg', '-framerate', f'{framerate:d}', '-i', 'tmp/%04d.png', output_name])
    subprocess.run(['rm', '-r', 'tmp'])
