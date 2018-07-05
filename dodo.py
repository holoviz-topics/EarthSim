import os
if "PYCTDEV_ECOSYSTEM" not in os.environ:
    os.environ["PYCTDEV_ECOSYSTEM"] = "conda"

from pyctdev import *  # noqa: api


############################################################
# Website building tasks; will move out to pyct

def task_docs():
    return {'actions': [
        'nbsite_nbpagebuild.py pyviz earthsim ./examples ./doc',
        'sphinx-build -b html ./doc ./doc/_build/html',
        'nbsite_fix_links.py ./doc/_build/html',
        'touch ./doc/_build/html/.nojekyll',
        'nbsite_cleandisthtml.py ./doc/_build/html take_a_chance']}
