from setuptools import setup, find_packages
from collections import defaultdict
import os
import sys
import shutil

########## autover ##########

def embed_version(basepath, ref='v0.2.5'):
    """
    Autover is purely a build time dependency in all cases (conda and
    pip) except for when you use pip's remote git support [git+url] as
    1) you need a dynamically changing version and 2) the environment
    starts off clean with zero dependencies installed.

    This function acts as a fallback to make Version available until
    PEP518 is commonly supported by pip to express build dependencies.
    """
    import io, zipfile, os
    try:    from urllib.request import urlopen
    except: from urllib import urlopen
    response = urlopen('https://github.com/pyviz/autover/archive/{ref}.zip'.format(ref=ref))
    zf = zipfile.ZipFile(io.BytesIO(response.read()))
    ref = ref[1:] if ref.startswith('v') else ref
    embed_version = zf.read('autover-{ref}/autover/version.py'.format(ref=ref))
    with open(os.path.join(basepath, 'version.py'), 'wb') as f:
        f.write(embed_version)


def get_setup_version(reponame, pkgname=None):
    """
    Helper to get the current version from either git describe or the
    .version file (if available). Set pkgname to the package name if it
    is different from the repository name.
    """
    import json, importlib, os
    pkgname = reponame if pkgname is None else pkgname
    basepath = os.path.dirname(os.path.abspath(__file__))
    version_file_path = os.path.join(basepath, pkgname, '.version')
    version = None
    try: version = importlib.import_module("version") # bundled
    except:
        try: from autover import version # available as package
        except:
            try: from param import version # available via param
            except:
                embed_version(basepath) # download
                version = importlib.import_module("version")

    if version is not None:
        return version.Version.setup_version(basepath, reponame, pkgname=pkgname,
                                             archive_commit="$Format:%h$")
    else:
        print("WARNING: autover unavailable. If you are installing a package, this warning can safely be ignored. If you are creating a package or otherwise operating in a git repository, you should refer to autover's documentation to bundle autover or add it as a dependency.")
        return json.load(open(version_file_path, 'r'))['version_string']


########## examples ##########

def examples(path='earthsim-examples', verbose=False, force=False, root=__file__):
    """
    Copies the notebooks to the supplied path.
    """
    filepath = os.path.abspath(os.path.dirname(root))
    example_dir = os.path.join(filepath, './examples')
    if not os.path.exists(example_dir):
        example_dir = os.path.join(filepath, '../examples')
    if os.path.exists(path):
        if not force:
            print('%s directory already exists, either delete it or set the force flag' % path)
            return
        shutil.rmtree(path)
    ignore = shutil.ignore_patterns('.ipynb_checkpoints', '*.pyc', '*~')
    tree_root = os.path.abspath(example_dir)
    if os.path.isdir(tree_root):
        shutil.copytree(tree_root, path, ignore=ignore, symlinks=True)
    else:
        print('Cannot find %s' % tree_root)


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
    version=get_setup_version("EarthSim",pkgname=setup_args['name']),
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
                                'earthsim/examples')
    if 'develop' not in sys.argv:
        examples(example_path, force=True, root=__file__)
    
    setup(**setup_args)

    if os.path.isdir(example_path):
        shutil.rmtree(example_path)
