import argparse
from pathlib import Path

from . import __version__
from .simulation import Simulation


def main():
    parser = argparse.ArgumentParser(description="Show information on PLUTO simulation")
    parser.add_argument(
        "paths", help="Path to PLUTO simulation", default=["."], nargs="*"
    )
    parser.add_argument(
        "--version", action="version", version="%(prog)s {}".format(__version__)
    )

    args = parser.parse_args()

    for path in args.paths:
        print(info(path))


def info(simulationpath):
    """Print info on simulation"""
    sims = []
    for format_ in Simulation.supported_formats:
        try:
            sims.append(Simulation(simulationpath, format=format_))
        except FileNotFoundError:
            pass
    if not sims:
        return "No simulation found at '{}'".format(simulationpath)

    sim = sims[0]
    output = (
        f"PLUTO simulation at '{sim.path}'\n"
        f"Data directory at '$SIM_DIR/{sim.data_path.relative_to(sim.path)}'\n"
        f"{sim.grid.coordinates.capitalize()} grid with dimensions {sim.dims}\n"
        f"Domain: x1: {sim.x1l[0]:.2e} .. {sim.x1r[-1]:.2e} (Lx1 = {sim.Lx1:.2e})\n"
        f"        x2: {sim.x2l[0]:.2e} .. {sim.x2r[-1]:.2e} (Lx2 = {sim.Lx2:.2e})\n"
        f"        x2: {sim.x3l[0]:.2e} .. {sim.x3r[-1]:.2e} (Lx3 = {sim.Lx3:.2e})\n"
        f"Available variables: {' '.join(sim.vars)}\n"
        "Data files:\n"
    )
    for sim in sims:
        output += (
            f"    Format {sim.format}: {len(sim)} files, "
            f"last time {sim.t[-1]}, data timestep {sim.dt.mean():.2e}\n"
        )

    return output


if __name__ == "__main__":
    main()
