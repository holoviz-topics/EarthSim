import os
import hashlib
import json

try:
    from bokeh.util.compiler import AttrDict, get_cache_hook, set_cache_hook
    old_hook = get_cache_hook()
    set_cache_hook(load_compiled_models)
except:
    pass

# Global variables
_CUSTOM_MODELS = {}


def load_compiled_models(custom_model, implementation):
    """
    Custom hook to load cached implementation of custom models.
    """
    compiled = old_hook(custom_model, implementation)
    if compiled is not None:
        return compiled

    model = CUSTOM_MODELS.get(custom_model.full_name)
    if model is None:
        return
    ts_file = model.__implementation__
    json_file = ts_file.replace('.ts', '.json')
    if not os.path.isfile(json_file):
        return
    with io.open(ts_file, encoding="utf-8") as f:
        code = f.read()
    with io.open(json_file, encoding="utf-8") as f:
        compiled = json.load(f)
    hashed = hashlib.sha256(code.encode('utf-8')).hexdigest()
    if compiled['hash'] == hashed:
        return AttrDict(compiled)
    return None
