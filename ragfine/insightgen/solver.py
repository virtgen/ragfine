from __future__ import annotations
from typing import Any, Dict, List
import re

from ..core.pipebase import State
from ..core.registry import register_step
from ..steps.validators import validate_io
from .io_models import SolverInput, SolverOutput

Variant = Dict[str, Any]

class Solver:
    """
    Produces naive answers aligned with state.data['questions'].
    Writes state.data['answers'].
    """
    def __init__(self, name: str = "Solver"):
        self.name = name

    @validate_io(input_model=SolverInput, output_model=SolverOutput)
    def run(self, state: State, variant: Variant) -> State:
        qs: List[str] = state.data.get("questions", []) or []
        answers: List[str] = []

        for q in qs:
            m = re.search(r"'([^']+)'", q)
            token = m.group(1) if m else None

            if token and "@" in token:
                answers.append(f"'{token}' appears to be a contact detail (email).")
            elif token and token.startswith("http"):
                answers.append(f"'{token}' is a referenced web link (URL).")
            else:
                cap = re.search(r"\b([A-ZÀ-ÖØ-öø-ÿ][\w'-]+)\b", q)
                if cap:
                    answers.append(f"{cap.group(1)} looks like a named entity mentioned in the text.")
                else:
                    answers.append("It refers to a key point inferred from the sentence.")

        state.data["answers"] = answers
        return state

register_step("Solver", lambda **kw: Solver(**kw))

def solve(name: str = "Solver") -> Solver:
    return Solver(name=name)

register_step("solve", lambda **kw: solve(**kw))