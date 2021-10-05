# plutoplot - easy and fast loading and plotting of PLUTO output files

`plutoplot` is a Python package for loading, analyzing and plotting data from the [astrophysical gas dynamics simulation code PLUTO](http://plutocode.ph.unito.it/).
By handling simulations as a whole and loading data only when needed (lazy loading), it is fast and easy to use.

It features:

- Loading on data actually needed (by lazy loading in memory mapping)
- easy slicing into large datasets (e.g. plotting 2D slice of 3D dataset)
- plotting non-cartesian coordinates projected into cartesian space
- interactive plotting in Jupyter Notebooks
- CLI tool to quickly acquire information about simulations
- Access to parameters set in `definitions.h` and `pluto.ini`
- Access to simulation metadata and grid properties
- Indexing with `ijk` (like `pyPLUTO`) and `kji` (like PLUTO internally) schemes

There is currently no support for:

- Particles
- Adaptive grids (AMR)
- 3D plotting (only plotting 2D slices of 3D data is supported.)

To get started, check out the [Quick Start Guide](quickstart.md) and the [examples](https://github.com/Simske/plutoplot/tree/main/test).

f you have any questions, suggestions or find a bug, feel free to open an [issue](https://github.com/Simske/plutoplot/issues)
or [Pull Request](https://github.com/Simske/plutoplot/pulls), I am happy to accept contributions to make plutoplot better.
