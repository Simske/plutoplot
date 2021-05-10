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
    output = "PLUTO simulation at '{}'\n".format(sim.sim_dir)
    output += "Data directory at '$SIM_DIR/{}'\n".format(
        sim.data_dir.relative_to(sim.sim_dir)
    )
    output += "{} grid with dimensions {}\n".format(
        sim.grid.coordinates.capitalize(), sim.dims
    )
    output += "Domain: x1: {:.2e} .. {:.2e} (Lx1 = {:.2e})\n".format(
        sim.x1l[0], sim.x1r[-1], sim.x1r[-1] - sim.x1l[0]
    )
    output += "        x2: {:.2e} .. {:.2e} (Lx2 = {:.2e})\n".format(
        sim.x2l[0], sim.x2r[-1], sim.x2r[-1] - sim.x2l[0]
    )
    output += "        x2: {:.2e} .. {:.2e} (Lx3 = {:.2e})\n".format(
        sim.x3l[0], sim.x3r[-1], sim.x3r[-1] - sim.x3l[0]
    )
    output += "Available variables: {}\n".format(" ".join(sim.vars))
    output += "Data files:\n"
    for sim in sims:
        dt = sim.t[1:] - sim.t[:-1]
        output += (
            "    Format {}: {} files, last time {}, data timestep {:.2e}\n".format(
                sim.format, len(sim), sim.t[-1], dt.mean(), dt.std()
            )
        )

    return output


if __name__ == "__main__":
    main()
