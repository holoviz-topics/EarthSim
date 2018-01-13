DOIT_CONFIG = {'verbosity': 2}

from ioamdoit import *

# The aim would be to not have anything much here, but right now
# that's usually not possible because of awkward/non-standard ways of
# installing dependencies, running tests, downloading data, etc,
# across projects.

def task_develop_install():
    return {'actions': []}

def task_all_tests():
    return {'actions': []}

def task_install_doc_dependencies():
    # would not need to exist if nbsite had conda package
    # (assumes notebook, ipython, etc already installed)
    return {
        'actions': [
            'conda install -y -q -c conda-forge sphinx beautifulsoup4 graphviz selenium phantomjs',
            'pip install nbsite sphinx_ioam_theme'],
        }
    

def task_docs():
    # TODO: could do better than this, or nbsite could itself use doit
    # (providing a dodo file for docs, or using doit internally).
    return {'actions': [
        'nbsite_nbpagebuild.py pyviz earthsim ./examples ./doc',
        'sphinx-build -b html ./doc ./doc/_build/html',
        'nbsite_fix_links.py ./doc/_build/html',
        'touch ./doc/_build/html/.nojekyll',
        'nbsite_cleandisthtml.py ./doc/_build/html take_a_chance']}
