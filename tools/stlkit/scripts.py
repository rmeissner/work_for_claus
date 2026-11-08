"""Loading model scripts by path."""

import importlib.util
import sys
from pathlib import Path
from types import ModuleType


def load_script(path: str | Path) -> ModuleType:
    """Import a ``.py`` file by path under a unique module name and return the module."""
    path = Path(path).resolve()
    name = "_script_" + "_".join(path.with_suffix("").parts[-3:]).replace("-", "_").replace(".", "_")
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module
