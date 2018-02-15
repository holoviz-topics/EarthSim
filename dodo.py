DOIT_CONFIG = {'verbosity': 2}

import shutil
from doit import action
from ioamdoit import *

# The aim would be to not have anything much here, but right now
# that's usually not possible because of awkward/non-standard ways of
# installing dependencies, running tests, downloading data, etc,
# across projects.

def task_test_nb():
    return {'actions': ['pytest --nbsmoke-run examples/']}

def task_all_tests():
    return {'actions': [],
            'task_dep': ['test_nb']}


############################################################
# Website building tasks
#
# More complex than necessary because nbsite doesn't yet have a conda
# package (assumes notebook, ipython, etc already installed), and because
# nbsite itself does not use doit internally (or provide a dodo file for docs).

def task_install_doc_dependencies():
    return {
        'actions': [
            'conda install -y -c pyviz/label/dev -c conda-forge nbsite sphinx_ioam_theme']}

def task_download_sample_data():
    return {
        'actions': [
            action.CmdAction('python download_sample_data.py', cwd='./examples')
        ]}

def task_docs():
    return {'actions': [
        'nbsite_nbpagebuild.py pyviz earthsim ./examples ./doc',
        'sphinx-build -b html ./doc ./doc/_build/html',
        'nbsite_fix_links.py ./doc/_build/html',
        'touch ./doc/_build/html/.nojekyll',
        'nbsite_cleandisthtml.py ./doc/_build/html take_a_chance']}
