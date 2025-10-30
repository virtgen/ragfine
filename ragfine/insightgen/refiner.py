from __future__ import annotations
from typing import Any, Dict
import re

from ..core.pipebase import State
from ..core.registry import register_step
from ..steps.validators import validate_io
from .io_models import RefinerInput, RefinerOutput

Variant = Dict[str, Any]

class Refiner:
    """
    Light formatting: squeeze blank lines, trim, unify arrows, optional trailing newline.
    """
    def __init__(self, name: str = "Refiner", ensure_trailing_newline: bool = False):
        self.name = name
        self.ensure_trailing_newline = ensure_trailing_newline

    @validate_io(input_model=RefinerInput, output_model=RefinerOutput)
    def run(self, state: State, variant: Variant) -> State:
        result = state.data.get("result", "") or ""

        result = re.sub(r"[ \t]+\n", "\n", result)
        result = re.sub(r"\n{3,}", "\n\n", result)
        result = re.sub(r"\s*→\s*", " → ", result)
        result = result.strip()

        if self.ensure_trailing_newline and not result.endswith("\n"):
            result += "\n"

        state.data["result"] = result
        return state

register_step("Refiner", lambda **kw: Refiner(**kw))

def refine(name: str = "Refiner", *, ensure_trailing_newline: bool = False) -> Refiner:
    return Refiner(name=name, ensure_trailing_newline=ensure_trailing_newline)

register_step("refine", lambda **kw: refine(**kw))