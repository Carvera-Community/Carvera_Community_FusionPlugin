import importlib
from pathlib import Path
import sys
import types


_PACKAGE_NAME = "_makera_community_addin"
_REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


def import_addin_module(module_name: str):
    """Import an add-in module with the package root Fusion provides."""
    if _PACKAGE_NAME not in sys.modules:
        package = types.ModuleType(_PACKAGE_NAME)
        package.__path__ = [str(_REPOSITORY_ROOT)]
        package.__package__ = _PACKAGE_NAME
        sys.modules[_PACKAGE_NAME] = package

    return importlib.import_module(f"{_PACKAGE_NAME}.{module_name}")
