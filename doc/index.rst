********
EarthSim
********

**Lightweight Python tools for environmental simulation**

EarthSim is a project for developing Python-based workflows for
specifying, launching, visualizing, and analyzing environmental
simulations, such as those for hydrology modeling. EarthSim is
designed to be a lightweight project internally, relying on code and
documentation primarily maintained in other, general-purpose SciPy and
`PyViz <http://pyviz.org>`_ projects:

-  `Bokeh <http://bokeh.pydata.org>`_: Interactive browser-based
   plotting.
-  `HoloViews <http://holoviews.org>`_: Easy construction of Bokeh
   plots for datasets.
-  `Datashader <https://github.com/bokeh/datashader>`_: Rendering large
   datasets into images for display in browsers.
-  `Param <https://github.com/ioam/param>`_: Specifying parameters of
   interest, e.g. to make widgets.
-  `XArray <http://xarray.pydata.org>`_: Processing gridded data structures.
-  `GeoViews <http://geoviews.org>`_: HoloViews with earth-specific
   projections.

This website has three main sections:

- `Getting Started <getting_started>`_: 
   How to install the code, notebooks, and data files needed for the examples.
- `User Guide <user_guide>`_:
   Usage information for the ``earthsim`` Python package, which
   contains a small amount of code specific to environmental
   simulation such as helper functions for annotating plots and
   specifying irregular meshes.
- `Topics <topics>`_:
   A set of Jupyter notebooks that show how to use the various PyViz
   tools together to solve earth-science problems, such as how to run
   various simulators.

If you have any notebooks showing how to use these tools to do useful
work in environmental simulation, we'd love to add them to the Topics!

Please feel free to report `issues
<https://github.com/pyviz/earthsim/issues>`_ or `contribute code.
<https://help.github.com/articles/about-pull-requests>`_

.. toctree::
   :hidden:
   :maxdepth: 2

   Introduction <self>
   Getting Started <getting_started/index>
   User Guide <user_guide/index>
   Topics <topics/index>
   About <about>
