"""Ponte para o motor de scraping existente (pasta detran-pa-consultas).

Mantemos o motor intacto e apenas o importamos. Se um dia o motor virar um
pacote instalavel, basta trocar este modulo.
"""

import os
import sys

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(os.path.dirname(_THIS_DIR))  # .../DETRAN
ENGINE_DIR = os.path.join(_ROOT, "detran-pa-consultas")

if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)

# Reexporta as classes do motor para o resto do backend
from services.sistransito import SistransitoService  # noqa: E402
from services.renach import RenachService            # noqa: E402
from services.captcha_solver import CaptchaSolver     # noqa: E402

__all__ = ["SistransitoService", "RenachService", "CaptchaSolver"]
