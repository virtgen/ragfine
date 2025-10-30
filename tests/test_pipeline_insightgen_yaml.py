import pytest
from ragfine.core.pipebase import State
from ragfine.core.builder import pipeline_from_yaml
import ragfine.steps

YAML_SPEC = """
defaults:
  meta: true
steps:
  - use: Entifier
  - use: Questor
  - use: Solver
  - use: Integrator
  - use: Refiner
  - use: Rebaser
"""

def _ensure_insightgen():
    try:
        ragfine.steps.load_insightgen()
        from ragfine import insightgen  # noqa: F401
        return True
    except ModuleNotFoundError:
        return False

@pytest.mark.skipif(not _ensure_insightgen(), reason="ragfine.insightgen not available")
def test_insightgen_yaml_pipeline():
    pipe, defaults = pipeline_from_yaml(YAML_SPEC)
    initial = State(data={"text": "Carol sent an email to Dave: carol@example.org"})
    reports = pipe.run(initial, defaults=defaults or {})
    final = reports[0].final_state.data

    assert "entities" in final and any("@" in e for e in final["entities"])
    assert "questions" in final and len(final["questions"]) > 0
    assert "answers" in final and len(final["answers"]) == len(final["questions"])
    assert "result" in final and "→" in final["result"]