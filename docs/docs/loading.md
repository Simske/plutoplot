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

The coordinate system will be read from the gridfile if not specified. More information on the coordinate system can be found in the [Grid section](#grid).

??? info "plutoplot.Simulation initialization reference"
    ::: plutoplot.Simulation.__init__

After loading the `Simulation`-object has the following attributes:

??? info "`Simulation` attributes"
    ::: plutoplot.Simulation
        selection:
          members: false
        rendering:
          heading_level: 4
          show_root_toc_entry: false

To show information about the simulation, just use the string representation:
```python
print(sim)
```
```
PLUTO Simulation: path: 'path/to/simulation', data directory '$sim_path/.'
Data vars: rho, vx1, vx2, vx3
Data files: Format `flt`: 2 files, last time 1.0, data timestep 1.00e+00  
PLUTO Grid Dimensions: (128, 1, 384), spherical coordinate system
r: 0.40..2.50, Lx1=2.10, N1=128
theta: 1.45..1.57, Lx1=0.12, N1=1
phi: 0.00..6.28, Lx1=6.28, N1=384
```
or use the Jupyter Notebook formatting
```python
sim
```
> **PLUTO Simulation** path: `/home/simeon/masterproject/PLUTO/test-problems/HD/Disk_Planet/03_0`, data directory `$sim_path/.`  
> Data vars: `rho` `vx1` `vx2` `vx3`  
> Data files: Format `flt`: 2 files,last time 1.0, data timestep 1.00e+00  
> **PLUTO Grid** Dimensions (128, 1, 384), spherical coordinate system
>
> |   |   |   | L | N |
> |---|---|---|---|---|
> |$r$|0.40|2.50|2.10|128|
> |$\theta$|1.45|1.57|0.12|1|
> |$\phi$|0.00|6.28|6.28|384|


## Slicing simulations

## Accessing simulation steps
Each simulation output step is represented by a `PlutoData` object, which will be generated on demand by the `Simulation`.  The `PlutoData`-object then gives access to the actual data arrays.
The data from the simulation output steps can be accessed from the `Simulation`-object with:

- direct access using the `[]`-operator or `get()` functions
```python
step_data = sim[10]
step_data = sim.get(10, keep=False)
```
- iteration
```python
for step in sim:
    # process data
```
- reduced data with `reduce()` and `reduce_parallel()` (over each time step)
```python
mean_density = sim.reduce(lambda step: step.rho.mean())
```

More details in [Data Access](data-access.md)

## Grid
The `Grid` object contains all the information of the simulation grid.

??? info "`Grid` reference"
    ::: plutoplot.Grid
