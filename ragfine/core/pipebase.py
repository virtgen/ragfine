from dataclasses import dataclass, field
from typing import Any, Dict, List, Callable, Protocol, Iterable, Optional, Union
from .registry import register_step

# ---------- Core ----------
@dataclass
class State:
    data: Dict[str, Any] = field(default_factory=dict)
    meta: Dict[str, Any] = field(default_factory=dict)

Variant = Dict[str, Any]

# --- Async helpers and imports ---
import asyncio, inspect

async def _maybe_await(obj):
    return await obj if inspect.isawaitable(obj) else obj

async def _run_step_async(step_obj: "Step", state: "State", variant: "Variant", step_timeout: "Optional[float]" = None) -> "State":
    coro = _maybe_await(step_obj.run(state, variant))
    if step_timeout is not None:
        return await asyncio.wait_for(coro, timeout=step_timeout)
    return await coro

# fix _run_steps_inline to normalize before running
def _run_steps_inline(state: "State", variant: "Variant", steps: List["Step"]) -> "State":
    """Uruchamia listę kroków bez użycia Pipeline (wprost, sekwencyjnie)."""
    s = state
    # normalize once
    norm_steps = [_normalize_step(st) for st in steps]
    for st in norm_steps:
        s = st.run(s, variant)
    return s

class _CallableStep:
    """Adapter so a bare callable(state, variant) can be used as a Step."""
    def __init__(self, fn: Any, name: str | None = None):
        self.fn = fn
        self.name = name or getattr(fn, "__name__", fn.__class__.__name__)
    def run(self, state, variant):
        return self.fn(state, variant)

def _normalize_step(s: Any):
    """Accepts instances with .run, classes with run (no-arg ctor), or bare callables."""
    # already an instance with .run
    if hasattr(s, "run") and callable(getattr(s, "run")):
        return s
    # class with run -> try to instantiate
    if isinstance(s, type) and hasattr(s, "run"):
        try:
            return s()   # no-arg ctor
        except TypeError as e:
            raise TypeError(
                f"Step class {getattr(s,'__name__',s)} requires constructor args; "
                "pass an instance instead."
            ) from e
    # bare callable(state, variant)
    if callable(s):
        return _CallableStep(s)
    raise TypeError(f"Unsupported step type: {type(s)}")

class Step(Protocol):
    def run(self, state, variant): ...

class FnStep:
    def __init__(self, fn: Callable[[Any, Any], Any], name: str | None = None):
        self.fn = fn
        self.name = name or fn.__name__
    def run(self, state, variant):
        return self.fn(state, variant)

def step(name: str | None = None):
    """Decorator: registers a pure function as a Step."""
    def deco(fn: Callable[[Any, Any], Any]):
        step_name = name or fn.__name__
        register_step(step_name, lambda **kw: FnStep(fn, step_name))
        return fn
    return deco

@dataclass
class PipelineReport:
    steps: List[Dict[str, Any]]
    final_state: State