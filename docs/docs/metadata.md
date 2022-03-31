# Reading metadata from pluto.ini & definitions.h

`plutoplot` can read the PLUTO settings files if needed.

## `pluto.ini`
`Pluto_ini` encapsulates the `pluto.ini` file, which is available from the simulation object (if `pluto.ini` is in the simulation directory).
In Jupyter Notebooks the config will be displayed as a table.
It is also possible to edit `Pluto_ini` and write it back to file.

!!! warning "Currently all values are strings and have to be converted to their respective datatype for use"
    This is subject to change, see [Github Issue](https://github.com/Simske/plutoplot/issues/11)


!!! example
    - Access from simulation
    ```python
    sim = pp.Simulation("path/to/simulation")

    sim.ini["Time"]["tstop"]
    sim.ini["Time","tstop"]
    sim.ini["Time/tstop"]
    ```

    - access directly from file and change values
    ```python
    ini = pp.Pluto_ini("path/to/pluto.ini")

    ini["Time/tstop"] = "2.0"
    ini.write("path/to/pluto.ini")
    ```

??? info "`Pluto_ini` reference"
    ::: plutoplot.Pluto_ini


## `definitions.h`
`Definitions.h` is available similarly as a `Definitions_h`-object, which is a `OrderedDict`.
It is also available from the `Simulation`-object or can be read from a file.

The keys are handled case-insensitively for convenience.

!!! example
    ```python
    sim = pp.Simulation("path/to/simulation")

    sim.definitions["cooling"]
    # output example: NO
    ```
    or
    ```python
    defs = pp.Definitions_h("path/to/definitions.h")

    defs["physics"]
    # output example: HD
    ```
Currently `Definitions_h`-files cannot be edited, see progress on this in [Github Issue](https://github.com/Simske/plutoplot/issues/10).

??? info "`Definitions_h` reference"
    ::: plutoplot.Definitions_h
