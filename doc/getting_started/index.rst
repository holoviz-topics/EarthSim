***************
Getting started
***************


Installation
------------

EarthSim supports Python 3.5-3.7 on Linux, Windows, or Mac.

To run the GSSHA-based examples in topics/, you'll need to use Linux
or Mac Python 3.5, because ``gssha`` and ``gssha-py`` packages are not yet
available for Windows or other Python versions.

Installable ``earthsim`` packages will be created at some point, but
at present, the recommended way to install Earthsim is based on conda
`conda <http://conda.pydata.org/docs>`_ environments and 
`git <https://git-scm.com>`_:


1. Install Python 3 `miniconda <http://conda.pydata.org/miniconda.html>`_ or 
`anaconda <http://docs.continuum.io/anaconda/install>`_, if you don't already have it on your system.

2. Clone the EarthSim git repository if you do not already have it::

    git clone git://github.com/pyviz/EarthSim.git

3. Set up an environment with all of the dependencies needed to run the examples::
    
    cd EarthSim
    conda env create --quiet --force -n earthsim -f ./environment.yml
    source activate earthsim

4. Put the `earthsim` directory into the Python path in this environment::
    
    pip install -e .

5. Download the sample files::

    cd examples
    python download_sample_data.py
    cd ..

    
Usage
-----

Once you've installed EarthSim as above and are in the EarthSim directory, you can
run the examples shown on the website using
`Jupyter <http://jupyter.org>`_::

    cd examples
    jupyter notebook --NotebookApp.iopub_data_rate_limit=1e8

(Increasing the rate limit in this way is `required for the 5.0 Jupyter version
<http://holoviews.org/user_guide/Installing_and_Configuring.html>`_,
but should not be needed in earlier or later Jupyter releases.)

You should now be able to select one of the ``user-guide`` or
``topics`` notebooks and run it in Jupyter.


Exploring Further
-----------------

You can look through the `User Guide <https://github.com/pyviz/EarthSim/issues>`_
and the `Topics <https://github.com/pyviz/EarthSim/issues>`_ to see examples, but
most of the documentation is at the sites for the packages like
`HoloViews <http://holoviews.org>`_ that are used in the examples.  A
good way to get comfortable with those tools is to work through the tutorials at 
`PyViz.org <http://pyviz.org>`_.

If you find any bugs or have any feature suggestions please file a 
`GitHub issue <https://github.com/pyviz/EarthSim/issues>`_
or submit a `pull request <https://help.github.com/articles/about-pull-requests>`_.
