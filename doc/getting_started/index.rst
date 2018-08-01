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

2. Clone the EarthSim git repository if you do not already have it::

    git clone git://github.com/pyviz/EarthSim.git

3. Set up an environment with all of the dependencies needed to run the examples::
    
    cd EarthSim
    conda create -n earthsim -c pyviz/label/earthsim -c conda-forge --file=dependencies.txt conda-forge::python=3.6

4. Activate the earthsim environment::
	 
    activate earthsim

   for Windows; MacOS and Linux users should instead run::

    source activate earthsim

5. Install the ``earthsim`` module into this environment::
    
    pip install -e .

6. Download the sample files::

    earthsim examples

    
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


Updates
-------

Assuming you are in the EarthSim directory, and the ``earthsim`` conda
environment is active, you can update to the latest version of
EarthSim as follows:

1. Get updated code and examples from git::

    git pull

2. Update the earthsim conda environment::

    conda install -c pyviz/label/earthsim -c conda-forge --file=dependencies.txt

3. Get a new copy of the examples to work on, and download new or updated data::

    earthsim examples	 


Developers
----------    
    
If you are actively developing EarthSim and want to try out the latest
pyviz work (which is not necessarily functional or stable), run the
following after creating or updating (and activating) your earthsim
environment::

  conda install -c pyviz/label/dev -c conda-forge --file=dependencies-dev-overrides.txt

