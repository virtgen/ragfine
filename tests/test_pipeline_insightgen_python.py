import pytest
from ragfine.core.pipeline import Pipeline
from ragfine.core.pipebase import State
import ragfine.steps

def _ensure_insightgen():
    try:
        ragfine.steps.load_insightgen()
        from ragfine import insightgen  # noqa: F401
        return True
    except ModuleNotFoundError:
        return False

@pytest.mark.skipif(not _ensure_insightgen(), reason="ragfine.insightgen not available")
def test_insightgen_python_pipeline():
    # Import after loading insightgen so symbols are present
    from ragfine.insightgen import Entifier, Questor, Solver, Integrator, Refiner, Rebaser

    pipe = Pipeline([
        Entifier(),
        Questor(),
        Solver(),
        Integrator(),
        Refiner(),
        Rebaser(),
    ])

    initial = State(data={"text": "Alice emailed Bob via https://example.com"})
    reports = pipe.run(initial)
    final = reports[0].final_state.data

    assert "entities" in final and len(final["entities"]) >= 2  # Alice, Bob, URL/email, etc.
    assert "questions" in final and len(final["questions"]) >= 1
    assert "answers" in final and len(final["answers"]) == len(final["questions"])
    assert isinstance(final.get("result", ""), str) and final["result"]