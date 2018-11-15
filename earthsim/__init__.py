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


def params_from_kwargs(**kwargs):
    """
    Utility to promote keywords with literal values to the appropriate
    parameter type with the specified default value unless the value is
    already a parameter.
    """
    params = {}
    for k, v in kwargs.items():
        kws = dict(default=v)
        if isinstance(v, param.Parameter):
            params[k] = v
        elif isinstance(v, bool):
            params[k] = param.Boolean(**kws)
        elif isinstance(v, int):
            params[k] = param.Integer(**kws)
        elif isinstance(v, float):
            params[k] = param.Number(**kws)
        elif isinstance(v, str):
            params[k] = param.String(**kws)
        elif isinstance(v, dict):
            params[k] = param.Dict(**kws)
        elif isinstance(v, tuple):
            params[k] = param.Tuple(**kws)
        elif isinstance(v, list):
            params[k] = param.List(**kws)
        elif isinstance(v, np.ndarray):
            params[k] = param.Array(**kws)
        else:
            params[k] = param.Parameter(**kws)
    return params


def parameters(**kwargs):
    """
    Utility to easily define a parameterized class with a chosen set of
    parameters specified as keyword arguments. The resulting object can
    be used to parameterize a notebook, display corresponding widgets
    with panel and control the workflow from the command line.
    """
    name = kwargs.get('name', 'Parameters')
    params = params_from_kwargs(**kwargs)
    params['name'] = param.String(default=name)
    return type(name, (param.Parameterized,), params)
