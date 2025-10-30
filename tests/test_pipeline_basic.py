import pytest
from ragfine.core.pipeline import Pipeline
from ragfine.core.pipebase import State
from ragfine.core.registry import register_step

# --- Two minimal steps (no insightgen) -------------------------------------

class UpperStep:
    def __init__(self, name="UpperStep"):
        self.name = name
    def run(self, state: State, variant: dict) -> State:
        text = state.data.get("text", "")
        state.data["text"] = text.upper()
        return state

class ExclaimStep:
    def __init__(self, name="ExclaimStep"):
        self.name = name
    def run(self, state: State, variant: dict) -> State:
        text = state.data.get("text", "")
        state.data["text"] = text + "!!!"
        return state

# Optional: register (useful if later tested via YAML)
register_step("UpperStep", lambda **kw: UpperStep(**kw))
register_step("ExclaimStep", lambda **kw: ExclaimStep(**kw))

def test_basic_pipeline_inline_steps():
    pipe = Pipeline([UpperStep(), ExclaimStep()])
    initial = State(data={"text": "hello world"})
    reports = pipe.run(initial)

    final = reports[0].final_state.data
    assert final["text"] == "HELLO WORLD!!!"