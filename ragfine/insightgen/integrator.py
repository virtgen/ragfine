from __future__ import annotations
from typing import Any, Dict, List

from ..core.pipebase import State
from ..core.registry import register_step
from ..steps.validators import validate_io
from .io_models import IntegratorInput, IntegratorOutput

Variant = Dict[str, Any]

class Integrator:
    """
    Stitches Q/A into markdown-ish lines; writes 'summary' and 'result'.
    """
    def __init__(self, name: str = "Integrator"):
        self.name = name

    @validate_io(input_model=IntegratorInput, output_model=IntegratorOutput)
    def run(self, state: State, variant: Variant) -> State:
        qs: List[str] = state.data.get("questions", []) or []
        ans: List[str] = state.data.get("answers", []) or []

        lines: List[str] = []
        for i, q in enumerate(qs):
            a = ans[i] if i < len(ans) else ""
            lines.append(f"- {q} → {a}")

        summary = "\n".join(lines).strip()
        state.data["summary"] = summary
        state.data["result"] = summary
        return state

register_step("Integrator", lambda **kw: Integrator(**kw))

def integrate(name: str = "Integrator") -> Integrator:
    return Integrator(name=name)

register_step("integrate", lambda **kw: integrate(**kw))