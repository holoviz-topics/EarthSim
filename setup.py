from setuptools import setup, find_packages

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


########## dependencies ##########

# TODO: need to sort through these, and what's the split between
# required/recommended? I made a fairly random cut...

install_requires = [
    'bokeh',
    'datashader',
    'geoviews',  # TODO > ?
    'holoviews', # TODO > ?
    'jupyter',
    'numpy',
    'param >=1.6.1',
    'parambokeh',
    'paramnb',
]

extras_require = {
    'recommended': [
    # quest?
    'fiona',
    'rasterio',
    'gdal',
    'json-rpc',
    'ulmo >=0.8.3.2',
    'pyyaml',
    'matplotlib',
    'click',
    'werkzeug',
    'peewee',
    'geopandas',
    'psutil',
    'pint',
    'pony',
    'scikit-image',
    'go-spatial',
    'descartes',
    'gsshapy',
    'gssha',
    'cartopy',
    'xarray',
    'filigree',
    'pvutil',
    # ?
    ### dependencies for pip installed packages
    # for quest
    'stevedore'
    ],
    'tests': [
        'nbsmoke',
        'flake8', # TODO: not a dependency of nbsmoke?
        #pytest-cov
    ],
    'docs': [
        'nbsite'
    ]
}

########## metadata for setuptools ##########

setup_args = {'name':'earthsim'}

setup_args.update(dict(
    version=get_setup_version("EarthSim",pkgname=setup_args['name']),
    packages = find_packages(),
    include_package_data=True,
    install_requires = install_requires,
    extras_require = extras_require,
    tests_require = extras_require['tests'],
    python_requires = ">=3.5",
    entry_points={
        'console_scripts': [
            'earthsim = earthsim.__main__:main'
        ]
    },
))

if __name__=="__main__":
    setup(**setup_args)
