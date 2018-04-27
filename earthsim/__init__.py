import param
__version__ = str(param.version.Version(fpath=__file__, archive_commit="$Format:%h$",reponame="EarthSim"))

# make pvutil's install_examples() and download_data() available if possible
from functools import partial
try:
    from pvutil.cmd import install_examples as _examples, download_data as _data
    install_examples = partial(_examples,'datashader')
    download_data = partial(_data,'datashader')
except ImportError:
    def _examples(*args,**kw): print("install examples package to enable this command (`conda install datashader-examples`)")
    _data = _examples
    def err(): raise ValueError(_data())
    download_data = install_examples = err
del partial, _examples, _data
