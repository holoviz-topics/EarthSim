import param

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
    with parambokeh and control the workflow from the command line.
    """
    name = kwargs.get('name', 'Parameters')
    params = params_from_kwargs(**kwargs)
    params['name'] = param.String(default=name)
    return type(name, (param.Parameterized,), params)
