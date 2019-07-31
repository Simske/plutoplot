import multiprocessing
import os
import subprocess

import numpy as np
import matplotlib.pyplot as plt

# local imports
from .plutodata import PlutoData
from .simulation import Simulation


def parameter_generator(
    sim: Simulation,
    plot_func,
    output_path,
    plot_args: dict = {"vmin": None, "vmax": None},
    save_args: dict = {"bbox_inches": "tight"},
):
    for i in range(sim.n):
        yield (sim, i, plot_func, output_path, plot_args, save_args)


def generate_frame(args):
    sim, i, plot_func, output_path, plot_args, save_args = args
    fig = plot_func(sim[i], **plot_args)
    fig.savefig("{}{:04d}.png".format(output_path, i), **save_args)
    plt.close(fig)
    del sim[i]


def render_frames_parallel(
    sim: Simulation,
    plot_func,
    output_path: str = "",
    plot_args: dict = {"vmin": None, "vmax": None},
    save_args: dict = {"bbox_inches": "tight"},
    verbose=True,
):
    with multiprocessing.Pool() as p:
        if verbose:
            total = len(sim)
            print(f"Rendering frame 0/{total} (0%)", end="")
            for i, _ in enumerate(
                p.imap_unordered(
                    generate_frame,
                    parameter_generator(
                        sim, plot_func, output_path, plot_args, save_args
                    ),
                )
            ):
                print(f"\rRendering frame {i}/{total} ({i/total*100:.1f}%)", end="")
        else:
            p.starmap(
                generate_frame,
                parameter_generator(sim, plot_func, output_path, plot_args, save_args),
            )


def generate_animation(
    sim: Simulation,
    plot_func,
    output_name: str = "animation.mp4",
    framerate: int = 25,
    plot_args: dict = {"vmin": None, "vmax": None},
    save_args: dict = {"bbox_inches": "tight"},
    verbose=True,
):
    os.mkdir("tmp")
    render_frames_parallel(sim, plot_func, "tmp/", plot_args, save_args, verbose=True)
    subprocess.run(
        [
            "ffmpeg",
            "-f",
            "lavfi",
            "-i",
            "anullsrc=stereo",
            "-framerate",
            "{:d}".format(framerate),
            "-i",
            "tmp/%04d.png",
            "-shortest",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            output_name,
        ]
    )
    subprocess.run(["rm", "-r", "tmp"])
