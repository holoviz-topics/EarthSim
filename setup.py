from setuptools import setup, find_packages
import os
import shutil
import sys

# TODO: build time deps to declare when we start packaging
import pyct.build
import param.version

########## dependencies ##########

# NOTE: This is just a start; you should ignore these for now. We are
# currently using dependencies.txt, which can only be installed using
# conda. The split between required and extras is also currently
# arbitrary.

install_requires = [
    'bokeh',
    'datashader',
    'geoviews >1.4',
    'jupyter',
    'numpy',
    'param',
    'parambokeh',
    'paramnb',
    'colorcet'
]

extras_require = {
    'recommended': [
        'ioam-lancet',
        'pyct[cmd]',
        'cartopy',
        'filigree',
        'fiona',
        'gdal',
        'geopandas',
        'gsshapy',
        'gssha',
        'quest',
        'xarray',
        'descartes',
        'scikit-image',
        'opencv',
        'nodejs'
    ],
    'tests': [
        'nbsmoke',
        'flake8',
    ],
    'docs': [
        'nbsite',
        'sphinx_ioam_theme'
    ]
}

########## metadata for setuptools ##########

setup_args = {'name':'earthsim'}

setup_args.update(dict(
    version=param.version.get_setup_version(__file__,"EarthSim",setup_args['name'],archive_commit="$Format:%h$"),
    packages = find_packages(),
    entry_points={
          'console_scripts': [
              'param = earthsim.__main__:param_main',
              'earthsim = earthsim.__main__:main'
    ]},
    include_package_data = True,
    install_requires = install_requires,
    extras_require = extras_require,
    tests_require = extras_require['tests'],
    python_requires = ">=3.5",
    url = "https://earthsim.pyviz.org",
    license = "BSD",
    description = "Tools for working with and visualizing environmental simulations"
))

if __name__=="__main__":
    example_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                'earthsim','examples')
    if 'develop' not in sys.argv:
        pyct.build.examples(example_path, __file__, force=True)
    
    setup(**setup_args)

    if os.path.isdir(example_path):
        shutil.rmtree(example_path)
