from setuptools import setup, find_packages
import os
import shutil
import sys

# TODO: build time deps to declare when we start packaging
import pyct.build
import param.version

setup_args = {'name':'earthsim'}

setup_args.update(dict(
    version=param.version.get_setup_version(__file__,"EarthSim",setup_args['name'],archive_commit="$Format:%h$"),
    packages = find_packages(),
    # TODO: when we start packaging, switch to rules in MANIFEST.in +
    # include_package_data=True instead of specifying package_data
    # here (e.g. package_data below won't end up in sdist).
    package_data={'earthsim': ['*.ts']},
    entry_points={
          'console_scripts': [
              'param = earthsim.__main__:param_main',
              'earthsim = earthsim.__main__:main'
    ]},
    include_package_data = True,
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
