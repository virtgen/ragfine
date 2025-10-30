from __future__ import annotations
from typing import Callable, Any, Dict

STEP_REGISTRY: Dict[str, Callable[..., Any]] = {}
CALLABLE_REGISTRY: Dict[str, Callable[..., Any]] = {}

def register_step(name: str, factory: Callable[..., Any]) -> None:
    STEP_REGISTRY[name] = factory

def register_fn(name: str, fn: Callable[..., Any]) -> None:
    CALLABLE_REGISTRY[name] = fn