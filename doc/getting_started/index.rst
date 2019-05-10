***************
Getting started
***************


Installation
------------

EarthSim supports Python 3.6 on Linux, Windows, or Mac.

EarthSim itself is a pure Python package that itself would be easy to install, but it depends on several packages (gdal, geos, and others) that are linked against binary-code geospatial libraries.  Unfortunately, incompatibly compiled versions of those libraries are available from different sources, which can make it difficult to assemble an appropriate environment for safely running EarthSim.  For this reason, EarthSim is currently provided via a special set of installation steps based on `conda <http://conda.pydata.org/docs>`_ and 
`git <https://git-scm.com>`_ that ensure only a compatible set of packages is used.  Specifically:

1. Install Python 3 `Miniconda <http://conda.pydata.org/miniconda.html>`_ or 
`Anaconda <http://docs.continuum.io/anaconda/install>`_, if you don't already have it on your system.

2. Install the EarthSim package via conda.

    conda install -c conda-forge earthsim

3. Download the sample files.
    python -c "import earthsim ; earthsim examples"


Developer Installation
----------------------

If you are actively collaborating with the EarthSim developers and
want to try out the latest pyviz work as it first appears (which is
not necessarily functional or stable), you can install EarthSim
from GitHub.

2. Clone the EarthSim git repository::

    git clone git://github.com/pyviz/EarthSim.git

3. Set up an environment with all of the dependencies needed to run the examples::

    cd EarthSim
    doit env_create -c pyviz/label/earthsim -c pyviz/label/dev -c defaults -c erdc -c conda-forge --name=earthsim --python=3.6

4. Activate the earthsim environment::

    activate earthsim

5. Install the ``earthsim`` module into this environment::

    pip install -e .

6. Download the sample files::

    earthsim examples

If you *really* want to be on the bleeding edge, you can instead get
the absolute latest changes by cloning the earthsim, holoviews,
geoviews, datashader, param, and panel Github repositories and
running `pip install -e .` inside each one, pulling new changes from
each of these libraries as needed.  That's what the main developers
do, but it isn't recommended for other users unless you are very
skilled at debugging the broken environments that are likely to appear
as packages change unpredictably over time.

    
Usage
-----

Once you've installed EarthSim as above and are in the EarthSim directory, you can
run the examples shown on the website using
`Jupyter <http://jupyter.org>`_::

    cd earthsim-examples
    jupyter notebook

You should now be able to select one of the ``user-guide`` or
``topics`` notebooks and run it in Jupyter.


Exploring Further
-----------------

You can look through the `User Guide <../user_guide>`_
and the `Topics <../topics>`_ to see examples, but
most of the documentation is at the sites for the packages like
`HoloViews <http://holoviews.org>`_ that are used in the examples.  A
good way to get comfortable with those tools is to work through the tutorials at 
`PyViz.org. <http://pyviz.org>`_

If you find any bugs or have any feature suggestions please file a 
`GitHub issue <https://github.com/pyviz/EarthSim/issues>`_
or submit a `pull request <https://help.github.com/articles/about-pull-requests>`_.
