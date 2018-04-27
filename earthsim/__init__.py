import param
__version__ = str(param.version.Version(fpath=__file__, archive_commit="$Format:%h$",reponame="EarthSim"))

# make pvutil's install_examples() and download_data() available if possible
from functools import partial
try:
    from pvutil.cmd import install_examples as _examples, download_data as _data
    install_examples = partial(_examples,'earthsim')
    download_data = partial(_data,'earthsim')
except ImportError:
    def _missing_cmd(*args,**kw): return("install pvutil to enable this command")
    _data = _examples = _missing_cmd
    def _err(): raise ValueError(_missing_cmd())
    download_data = install_examples = _err
del partial, _examples, _data
