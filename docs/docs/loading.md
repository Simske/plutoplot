# Loading simulations
Loading data from simulations is the central function `plutoplot` serves.

The central object to interact with a PLUTO simulation is the `plutoplot.Simulation` object.
In loads the simulation metadata, the grid and creates the objects for the individual output files.

## Simulation

To load a simulation from disk create a `plutoplot.Simulation` object:
```python
import plutoplot as pp

sim = pp.Simulation("path/to/simulation", format="flt")
```
Additionally the coordinates system and indexing can be set manually.
If no format is given, the first existing format is used (in the order `dbl`, `flt`, `vtk`, `dbl.h5`, `flt.h5`).

!!! info "Simulation init reference"
    ::: plutoplot.Simulation.__init__



# Simulation


# Grid

#
