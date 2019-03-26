#!/usr/bin/env python

import os
import sys
import json
import shutil
import hashlib

from setuptools import setup, find_packages
from setuptools.command.develop import develop
from setuptools.command.install import install

# TODO: build time deps to declare when we start packaging
import pyct.build
import param.version

setup_args = {'name': 'earthsim'}

install_requires = [
    'param>=1.9.0a4,<2.0', 'holoviews>=1.12.0a4', 'datashader>=0.6.9',
    'geoviews>=1.6.2', 'panel>=0.5.0a5', 'bokeh>=1.0.4', 'cartopy>=0.17.0',
    'xarray>=0.11.0', 'colorcet>=1.0.0', 'notebook>=5.5.0',
    'fiona', 'gdal>=2.3.3', 'rasterio==1.0.13']

extras_require = {}

extras_require['recommended'] = [
    'opencv', 'quest==2.6.1', 'gsshapy==2.3.8', 'gssha==7.12+pyviz.0',
    'ulmo==0.8.4', 'lancet>=0.9.0']

# until pyproject.toml/equivalent is widely supported (setup_requires
# doesn't work well with pip)
extras_require['build'] = [
    'param >=1.7.0',
    'pyct >=0.4.4',
    'setuptools >=30.3.0',
    'bokeh >=1.0.0',
    'pyviz_comms >=0.6.0',
    'nodejs >=9.11.1',
]

extras_require['tests'] = (
    extras_require['build'] + extras_require['recommended'] +
    ['pytest', 'pyflakes', 'nbsmoke'])


def build_custom_models():
    """
    Compiles custom bokeh models and stores the compiled JSON alongside
    the original code.
    """
    import earthsim.models.custom_tools
    from earthsim.models import _CUSTOM_MODELS
    from bokeh.util.compiler import _get_custom_models, _compile_models
    custom_models = _get_custom_models(list(_CUSTOM_MODELS.values()))
    compiled_models = _compile_models(custom_models)
    for name, model in custom_models.items():
        compiled = compiled_models.get(name)
        if compiled is None:
            return
        print('\tBuilt %s custom model' % name)
        impl = model.implementation
        hashed = hashlib.sha256(impl.code.encode('utf-8')).hexdigest()
        compiled['hash'] = hashed
        fp = impl.file.replace('.ts', '.json')
        with open(fp, 'w') as f:
            json.dump(compiled, f)

class CustomDevelopCommand(develop):
    """Custom installation for development mode."""
    def run(self):
        try:
            print("Building custom models:")
            build_custom_models()
        except ImportError as e:
            print("Custom model compilation failed with: %s" % e)
        develop.run(self)

class CustomInstallCommand(install):
    """Custom installation for install mode."""
    def run(self):
        try:
            print("Building custom models:")
            build_custom_models()
        except ImportError as e:
            print("Custom model compilation failed with: %s" % e)
        install.run(self)

setup_args.update(dict(
    version=param.version.get_setup_version(__file__,"EarthSim",setup_args['name'],archive_commit="$Format:%h$"),
    packages = find_packages(),
    include_package_data=True,
    install_requires=install_requires,
    extras_require=extras_require,
    python_requires=">=3.6",
    cmdclass={
        'develop': CustomDevelopCommand,
        'install': CustomInstallCommand,
    },
    entry_points={
          'console_scripts': [
              'param = earthsim.__main__:param_main',
              'earthsim = earthsim.__main__:main'
    ]},
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    maintainer="PyViz Developers",
    maintainer_email="developers@pyviz.org",
    platforms=['Windows', 'Mac OS X', 'Linux'],
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
