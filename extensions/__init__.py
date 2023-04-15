import importlib
import os


def scan_extensions():
    names = ['.' + os.path.splitext(f)[0] for f in os.listdir(os.path.dirname(__file__)) if
             f.endswith('.py') and not f.startswith('__')]

    for name in names:
        m = importlib.import_module(name, '.extensions')
        for sub in dir(m):
            if sub.endswith('Extension'):
                extensions.append(getattr(m, sub))


extensions = []
scan_extensions()
