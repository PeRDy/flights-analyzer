"""Loaded settings module on runtime to conveniently configure it through an environment variable.
"""
import os
from importlib import import_module

__all__ = ['settings']


def load_settings(path):
    try:
        try:
            m, c = path.rsplit(':', 1)
            module = import_module(m)
            s = getattr(module, c)
        except ValueError:
            s = import_module(path)
    except ImportError:
        raise ImportError("Settings not found '{}'".format(path))

    return s


settings = load_settings(os.environ['APP_SETTINGS'])
