from __future__ import annotations
from typing import Any, Dict

from ..core.pipebase import State
from ..core.registry import register_step
from ..steps.validators import validate_io
from .io_models import EntifierInput, EntifierOutput
from .utils import WORD_RE, EMAIL_RE, URL_RE, unique

Variant = Dict[str, Any]

class Entifier:
    def __init__(self, name: str = "Entifier"):
        self.name = name

    @validate_io(input_model=EntifierInput, output_model=EntifierOutput)
    def run(self, state: State, variant: Variant) -> State:
        text = state.data.get("text", "") or ""
        words = WORD_RE.findall(text)
        titlecase = [w for w in words if w[:1].isupper() and w.lower() != w]
        emails = EMAIL_RE.findall(text)
        urls = URL_RE.findall(text)
        state.data["entities"] = unique(titlecase + emails + urls)
        return state

register_step("Entifier", lambda **kw: Entifier(**kw))

def entify(name: str = "Entifier") -> Entifier:
    return Entifier(name=name)

register_step("entify", lambda **kw: entify(**kw))