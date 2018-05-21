import param
__version__ = str(param.version.Version(fpath=__file__, archive_commit="$Format:%h$",reponame="EarthSim"))

# make pyct's install_examples() and download_data() available if possible
from functools import partial
try:
    from pyct.cmd import install_examples as _examples, download_data as _data
    install_examples = partial(_examples,'earthsim')
    download_data = partial(_data,'earthsim')
except ImportError:
    def _missing_cmd(*args,**kw): return("install pvct to enable this command (e.g. `conda install -c pyviz pyct`)")
    _data = _examples = _missing_cmd
    def _err(): raise ValueError(_missing_cmd())
    download_data = install_examples = _err
del partial, _examples, _data
