import os
if "PYCT_ECOSYSTEM" not in os.environ:
    os.environ["PYCT_ECOSYSTEM"] = "conda"

from pyct import *  # noqa: api


############################################################
# Website building tasks; will move out to pyct

from doit import action

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
