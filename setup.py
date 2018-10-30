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

setup_args = {'name':'earthsim'}

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
    cmdclass={
        'develop': CustomDevelopCommand,
        'install': CustomInstallCommand,
    },
    entry_points={
          'console_scripts': [
              'param = earthsim.__main__:param_main',
              'earthsim = earthsim.__main__:main'
    ]},
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
