**********
User Guide
**********

Most of the functionality developed in the EarthSim project is in the
various general-purpose open-source Python packages like `Bokeh
<http://bokeh.pydata.org>`_, `HoloViews <http://holoviews.org>`_, and
`Datashader <http://datashader.org>`_. This User Guide focuses on
documenting the small amount of code that's actually in `earthsim`
itself.

So far, what is documented here shows how to use the
drawing/annotation tools that were added to Bokeh and HoloViews
as part of this project, along with the specific application of those
tools to specifying the generation of irregular triangular meshes used
for variable-resolution simulations.

There is also some support in the `earthsim` module for running the
GSSHA hydrology simulator, which is currently illustrated in the separate
`Topics <../topics/>`_ section.


Drawing/annotation tools:


* `Drawing Tools <Drawing_Tools.html>`_
  Introduction to the drawing tools used to draw, edit and annotate data.

* `Adding Annotations <Annotators.html>`_
  Introduces a number of classes useful for annotating point, line and polygon data.


Making and using triangular meshes:


* `Specifying meshes with Filigree <Specifying_Meshes.html>`_
  Using draw tools to generate inputs to the Filigree mesh generator.

* `Visualizing meshes <Visualizing_Meshes.html>`_
  Demonstrates how to load large static and time-varying trimesh data
  and using datashader to interpolate it.

* `Analyzing Meshes <Analyzing_Meshes.html>`_
  Analyzing meshes by plotting data across multi-segment line cross-sections.


.. toctree::
    :titlesonly:
    :hidden:
    :maxdepth: 2

    Drawing Tools <Drawing_Tools>
    Adding Annotations <Annotators>
    Specifying Meshes <Specifying_Meshes>
    Visualizing Meshes <Visualizing_Meshes>
    Analyzing Meshes <Analyzing_Meshes>
