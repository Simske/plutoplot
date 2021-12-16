# Data Access
After [creating the simulation object](loading.md) all simulation data can be accessed via this object.
Here the different ways to access data are explored.

If not explicitly specified, all examples assume an simulation object `sim` is available
```python
import plutoplot as pp

sim = pp.Simulation("path/to/simulation")
```


The data for the individual timesteps is encapsulated in `PlutoData`-object, which the `Simulation`-object will create on demand.
The data arrays for the variables can be accessed from there.

## Accessing Steps
### Direct access
To get the `PlutoData`-object for a specific step can be accessed using the `[]`-operator or `get()` function like this:
```python
step_data = sim[10]
step_data = sim.get(10, keep=False)
# or direct acces to variables:
sim[10].rho
```
`get()` also has an additional parameter `keep`, which chooses if the resulting object should be kept im memory after use.
??? info "`Simulation.get()` docs"
    ::: plutoplot.Simulation.get

### Iteration and `reduce`
It is also possible to iterate over all (or some steps for processing)
```python
for step_data in sim:
    # process data here

# or for more control over the range
for step_data in sim.iter(start, stop, step):
    # process data
```
??? info "`Simulation.iter()` reference"
    ::: plutoplot.Simulation.iter

If each step should be reduced to into an array of values the `reduce` and `reduce_parallel` helpers can be used.
For example, if the mean density of each step is needed:
```python
mean_rho = sim.reduce(lambda step: step.rho.mean())
# result: mean_rho.shape == len(sim)
```
More complex reductions with n-dimensional outputs are also supported. The shape of the output can be either given as an argument, or will be deduced from the first calculation:
```python
column_density = sim.reduce(lambda step: step.rho.sum(axis=2))
# Result: column_density.shape == (n1, n2)
```
`reduce_parallel` is equivalent, but will use `multiprocessing` to parallelise this operation. Be aware that because of the overhead of multiprocessing this is not necessarily faster than a serial `reduce()`, especially with an optimized `numpy`-installation.

??? info "`reduce()` reference"
    ::: plutoplot.Simulation.reduce
??? info "`reduce_parallel()` reference"
    ::: plutoplot.Simulation.reduce_parallel


## Accessing data

The available data variables of a simulation can be accessed from `simulation.vars` or `plutodata.vars`:
```python

```
