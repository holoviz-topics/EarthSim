[![linux mac build Status](https://travis-ci.org/pyviz/EarthSim.svg?branch=master)](https://travis-ci.org/pyviz/EarthSim)
[![win build status](https://ci.appveyor.com/api/projects/status/cdhrrks36kr32545/branch/master?svg=true)](https://ci.appveyor.com/project/pyviz/earthsim/branch/master)

# EarthSim

Python-based tools for specifying, launching, visualizing, and analyzing environmental simulations, such as those for hydrology modeling.

EarthSim is designed as a lightweight "overview" site and project, relying on core code maintained in other general-purpose [PyViz](http://pyviz.org) projects:

- [Bokeh](http://bokeh.pydata.org): Interactive browser-based plotting
- [HoloViews](http://holoviews.org): Easy construction of Bokeh plots for datasets
- [Datashader](https://github.com/bokeh/datashader): Rendering large datasets into images for display in browsers
- [Param](https://github.com/ioam/param): Specifying parameters of interest, e.g. to make widgets
- [GeoViews](http://geoviews.org): HoloViews with earth-specific projections

As such, this repository primarily consists of three things:

- [earthsim](https://github.com/pyviz/EarthSim/tree/master/earthsim): A Python package with a small amount of code specific to environmental simulation
- [examples](https://github.com/pyviz/EarthSim/tree/master/examples): A set of Jupyter notebooks that show how to use the various PyViz tools to solve earth-science problems
- [website](https://pyviz.github.io/EarthSim): The example notebooks already run and rendered to HTML for simple exploration

In most cases, the examples (as notebooks or as the webstite) represent the main form of documentation, even for the Python package, so please see [pyviz.github.io/EarthSim](https://pyviz.github.io/EarthSim>) for more information, including installation and usage instructions.
