import json
import pytest
from ragfine.core.pipebase import State
from ragfine.core.builder import pipeline_from_yaml, pipeline_from_json

def test_pipeline_from_yaml_text():
    spec = """
steps:
  - use: UpperStep
  - use: ExclaimStep
"""
    # The basic steps are registered in test_pipeline_basic.py on import,
    # but to keep this test independent, we re-register them here too:
    from ragfine.core.registry import register_step
    from ragfine.core.pipebase import State as _S

    class UpperStep:
        def __init__(self, name="UpperStep"): self.name = name
        def run(self, s: _S, v: dict) -> _S:
            s.data["text"] = s.data.get("text", "").upper(); return s
    class ExclaimStep:
        def __init__(self, name="ExclaimStep"): self.name = name
        def run(self, s: _S, v: dict) -> _S:
            s.data["text"] = s.data.get("text", "") + "!!!"; return s

    register_step("UpperStep", lambda **kw: UpperStep(**kw))
    register_step("ExclaimStep", lambda **kw: ExclaimStep(**kw))

    pipe, defaults = pipeline_from_yaml(spec)
    final = pipe.run(State(data={"text": "ok"}))[0].final_state.data
    assert final["text"] == "OK!!!"

def test_pipeline_from_json_text():
    spec = {
        "steps": [
            {"use": "UpperStep"},
            {"use": "ExclaimStep"},
        ]
    }
    pipe, defaults = pipeline_from_json(json.dumps(spec))
    final = pipe.run(State(data={"text": "go"}))[0].final_state.data
    assert final["text"] == "GO!!!"