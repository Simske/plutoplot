# plutoplot - Plutocode Plotting library

This is a Python 3 library for plotting output data from the [PLUTO code](http://plutocode.ph.unito.it/)

This library is under development and mostly specialized on the functionality I personally need. Nonetheless I will try to make the code as widely applicable and documented as possible.

## Requirements
```
Python >=3.6
numpy
matplotlib
```

## Installation
Install it with pip:
```
pip install git+https://gitlab.mpcdf.mpg.de/sdoetsch/plutoplot.git
```

Or download repository (as archive or with git)
```
python setup.py install
```

If you downloaded via git and want to keep updating via git, you can also use
```
python setup.py develop
```
This way the package is always read in from the git directory.

## Example
```python
import plutoplot as pp

sim = pp.Simulation("path_to_simulation")
print(sim.grid)

# Access to grid coordinates
sim.x1
sim.vx1

# Access to simulation steps
sim[3].rho

# time evolution of mean pressure
mean_prs = sim.reduce(lambda D : D.prs.mean())
```

## Concepts
`plutoplot` offers three main classes for handling simulation data:
 - `Simulation`: for a simulation
 - `PlutoData`: for a single simulation data frame
 - `Grid`: for the PLUTO domain grid

For data loading the user only has to instantiate a `Simulation`, the grid
and the `PlutoData` objects are created from the `Simulation` when needed.
`PlutoData` uses lazy loading for the actual data, which means the data is
loaded when is first needed, not on object instantiation.
Each variable is loaded seperately (independent of PLUTO save format),
e.g. when only density is needed, pressure is never put into memory.

## Simulation instantiation
A `Simulation` can be instantiated with:
```python
Simulation(sim_dir='', format=None, coordinates=None)
```
- `sim_dir`: Simulation directory (directory with `pluto.ini` and `definitions.h`).
  plutoplot searchs for the gridfile and simulation data first in `sim_dir`,
  then in `sim_dir/data`, and then looks up the data directory in `pluto.ini`.
  Default: Current working directory
- `format`: file format of the simulation data, currently supports `dbl`, `flt`, `vtk`
  in both `single_file` and `multiple_files` mode.
  Default: `dbl`, `flt`, `vtk`, are tried in that order
- `coordinates`: coordinate system of the simulation grid.
  Supports `cartesian`, `spherical`, `polar`, `cylindrical`.
  Only necessary for projecting the grind into a cartesian system (e.g. for plotting).
  Default: Read coordinate system from `definitions.h`, using `cartesian` as fallback

## Access `pluto.ini` and `definitions.h`
`plutoplot` can load the PLUTO configuration files:
```python
sim = Simulation('sim_dir')
sim.ini['section']['option']
sim.definitions['options']
```
The returned objects for `pluto.ini` (`Pluto_ini`) and `definitions.h` (`Definitions_H`)
are thin wrappers around `OrderedDict`s.

## Data access
The simulation steps can be optained from the `Simulation` object with the subscript syntax:
```python
sim = Simulation('sim_dir')
initial = sim[0]
last = sim[-1]
```
It supports the Python conventions for indexing (zero indexed, negative numbers
are handled as `len(sim)-i`)

Which variables are saved by PLUTO are accesible with
```python
sim.vars
# or
sim[i].vars
# e.g. ['rho', 'vx1', 'vx2', 'vx3', 'prs']
```

The variable names in this list can be then accessed from the `PlutoData` objects:
```python
sim[0].rho
sim[-1].vx1
```
The data is then returned as Numpy arrays, and can be used as usual.

## Plotting
