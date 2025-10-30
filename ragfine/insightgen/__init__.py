"""
ragfine.insightgen
------------------
Insight generation steps (entity→Q→A→integrate→refine→rebase).
Importing this package registers its steps via module side-effects.
"""

from .entifier import Entifier, entify
from .questor import Questor, quest
from .solver import Solver, solve
from .integrator import Integrator, integrate
from .refiner import Refiner, refine
from .rebaser import Rebaser, rebase

from . import utils, io_models

__all__ = [
    "Entifier", "entify",
    "Questor", "quest",
    "Solver", "solve",
    "Integrator", "integrate",
    "Refiner", "refine",
    "Rebaser", "rebase",
    "utils", "io_models",
]