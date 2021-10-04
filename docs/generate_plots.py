#!/usr/bin/env python3
"""
Script to generate sample plots for documentation from PLUTO test problems
"""
import os
from pathlib import Path

import plutoplot as pp

base_path = Path(os.getenv("PLUTO_TEST_PROBLEMS"))
dest_path = Path("docs/img")

# Plots for quick start
sim = pp.Simulation(
    "/home/simeon/masterproject/PLUTO/test-problems/HD/Disk_Planet/03_0", format="flt"
)
fig, _ = sim.plot("rho")
fig.savefig(dest_path / "quick_start_plot_projected.jpg", bbox_inches="tight", dpi=75)

fig, _ = sim.plot("rho", projection=False)
fig.savefig(
    dest_path / "quick_start_plot_not-projected.jpg", bbox_inches="tight", dpi=75
)


print("Plots generated")
