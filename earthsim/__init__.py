import param
__version__ = str(param.version.Version(fpath=__file__, archive_commit="$Format:%h$",reponame="EarthSim"))

# make pyct's example/data commands available if possible
from functools import partial
try:
    from pyct.cmd import copy_examples as _copy, fetch_data as _fetch, examples as _examples
    copy_examples = partial(_copy,'earthsim')
    fetch_data = partial(_fetch,'earthsim')
    examples = partial(_examples, 'earthsim')
except ImportError:
    def _missing_cmd(*args,**kw): return("install pyct to enable this command (e.g. `conda install -c pyviz pyct`)")
    _copy = _fetch = _examples = _missing_cmd
    def _err(): raise ValueError(_missing_cmd())
    fetch_data = copy_examples = examples = _err
del partial, _examples, _copy, _fetch
