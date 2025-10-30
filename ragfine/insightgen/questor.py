from __future__ import annotations
from typing import Any, Dict, List
import re

from ..core.pipebase import State
from ..core.registry import register_step
from ..steps.validators import validate_io
from .io_models import QuestorInput, QuestorOutput
from .utils import split_sentences, unique

Variant = Dict[str, Any]

class Questor:
    """
    Generates naive questions about entities or per sentence.
    Stores state.data['questions'] (list[str]).
    """
    def __init__(self, name: str = "Questor"):
        self.name = name

    @validate_io(input_model=QuestorInput, output_model=QuestorOutput)
    def run(self, state: State, variant: Variant) -> State:
        text = state.data.get("text", "") or ""
        ents: List[str] = state.data.get("entities", []) or []
        sents = split_sentences(text)

        qs: List[str] = []
        if ents:
            for e in ents:
                if "@" in e:
                    qs.append(f"Who uses the email '{e}'?")
                elif e.startswith("http"):
                    qs.append(f"What is the purpose of the URL '{e}'?")
                else:
                    qs.append(f"What is {e}?")
        else:
            qs = [f"What is the main point of: '{s}'?" for s in sents]

        state.data["questions"] = unique(qs)
        return state

register_step("Questor", lambda **kw: Questor(**kw))

def quest(name: str = "Questor") -> Questor:
    return Questor(name=name)

register_step("quest", lambda **kw: quest(**kw))