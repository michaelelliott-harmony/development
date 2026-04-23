# Harmony Spatial Operating System — Pillar I — Spatial Substrate
#
# Path bootstrap for the API layer.
#
# The registry, alias, and cell-key packages live outside the
# services/api tree and are not currently distributed as pip-installable
# packages. This module prepends their src/ directories to sys.path so
# their modules can be imported as top-level names:
#
#     import registry
#     import alias_service
#     import derive
#
# This keeps the registry and alias services as the single source of
# truth — the API layer imports them directly rather than duplicating
# their code.

import os
import sys

_HERE = os.path.abspath(os.path.dirname(__file__))
_PROJECT_ROOT = os.path.abspath(os.path.join(_HERE, "..", "..", ".."))

_PKG_SRC_DIRS = [
    os.path.join(_PROJECT_ROOT, "harmony", "packages", "registry", "src"),
    os.path.join(_PROJECT_ROOT, "harmony", "packages", "alias", "src"),
    os.path.join(_PROJECT_ROOT, "harmony", "packages", "cell-key", "src"),
]

for _src in _PKG_SRC_DIRS:
    if _src not in sys.path:
        sys.path.insert(0, _src)
