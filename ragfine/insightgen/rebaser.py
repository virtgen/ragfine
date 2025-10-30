from __future__ import annotations
from typing import Any, Dict

from ..core.pipebase import State
from ..core.registry import register_step
from ..steps.validators import validate_io
from .io_models import RebaserInput, RebaserOutput

Variant = Dict[str, Any]

class Rebaser:
    """
    Final cosmetic changes driven by Variant (style_prefix/suffix).
    """
    def __init__(self, name: str = "Rebaser"):
        self.name = name

    @validate_io(input_model=RebaserInput, output_model=RebaserOutput)
    def run(self, state: State, variant: Variant) -> State:
        result = state.data.get("result", "") or ""
        prefix = variant.get("style_prefix", "")
        suffix = variant.get("style_suffix", "")
        state.data["result"] = f"{prefix}{result}{suffix}"
        return state

register_step("Rebaser", lambda **kw: Rebaser(**kw))

def rebase(name: str = "Rebaser") -> Rebaser:
    return Rebaser(name=name)

register_step("rebase", lambda **kw: rebase(**kw))