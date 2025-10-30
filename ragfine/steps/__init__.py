"""
Collection of built-in pipeline steps for RAGFine.

Always-on (loaded on import):
- sync_flow.py    → flow control steps (BranchStep, SplitMerge)
- async_flow.py   → async flow steps (AsyncBranchStep, AsyncFanOutFanInStep / AsyncSplitMerge)
- validators.py   → @validate_io decorator for input/output validation
- io_models.py    → Pydantic schemas for step I/O validation

Opt-in (NOT auto-loaded here):
- ragfine.insightgen  → domain steps (Entifier, Questor, Solver, Integrator, Refiner, Rebaser)
  Load explicitly with: `from ragfine.steps import load_insightgen; load_insightgen()`
  or: `import ragfine.insightgen`
"""

# --- Always load built-in flow steps (side-effect: registration) ---
from . import sync_flow   # noqa: F401
from . import async_flow  # noqa: F401

# --- Re-export selected classes & aliases for users (sync + async flow) ---
from .sync_flow import BranchStep, SplitMerge, branch, split_merge
from .async_flow import AsyncBranchStep, AsyncSplitMerge as AsyncSplitMerge

# --- Validation utilities are lightweight; export them directly ---
from .validators import validate_io

# --- Opt-in loader for domain (insight generation) steps ---
def load_insightgen() -> None:
    """
    Explicitly import top-level 'ragfine.insightgen' to register its steps.
    Keeps domain steps independent from the core built-ins.
    """
    import ragfine.insightgen  # noqa: F401


__all__ = [
    # submodules (flow)
    "insightgen",
    "sync_flow",
    "async_flow",

    # sync classes / aliases
    "BranchStep",
    "SplitMerge",
    "branch",
    "split_merge",

    # async classes / aliases
    "AsyncBranchStep",
    "AsyncSplitMerge",

    # validation tools
    "validate_io",

    # opt-in loader for domain steps
    "load_insightgen",
]

# USAGE:
#   import ragfine.steps  # registers built-in flow steps
#   from ragfine.steps import BranchStep, SplitMerge, validate_io
#   # to include domain steps (Entifier, etc.):
#   from ragfine.steps import load_insightgen
#   load_insightgen()  # or: import ragfine.insightgen