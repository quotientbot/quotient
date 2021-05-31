import inspect
from .utils import MISSING


def _default_args(func):
    signature = inspect.signature(func)
    return {k: v.default for k, v in signature.parameters.items() if v.default is not inspect.Parameter.empty}


def make_key(func, args, kwargs, ignore=()):
    kwargs.update(zip(func.__code__.co_varnames, args))
    kwargs.update({k: v for k, v in _default_args(func).items() if k not in kwargs})

    keys = []

    if func.__prefix is not None:
        if func.__prefix == MISSING:
            keys.append(func.__name__)
        else:
            keys.append(func.__prefix)

    _sorting = {k: v for v, k in enumerate(func.__code__.co_varnames)}

    for k, v in sorted(kwargs.items(), key=lambda item: _sorting[item[0]]):
        if k not in ignore:
            keys.append(v.__repr__())

    return ":".join(keys)
