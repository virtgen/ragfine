# TODOfrom ..registry.registry import register_step
from typing import Any, Dict, List, Callable, Protocol, Iterable, Optional, Union
from ..core.registry import register_step
from ..core.pipebase import _normalize_step, _run_steps_inline
import copy

# -------- 1) BRANCHING: krok rozgałęzienia warunkowego --------
class BranchStep:
    def __init__(self, name, predicate, then_steps, else_steps=None):
        self.name = name
        self._pred = predicate
        self._then = [_normalize_step(s) for s in (then_steps or [])]
        self._else = [_normalize_step(s) for s in (else_steps or [])]

    def run(self, state: "State", variant: "Variant") -> "State":
        if self._pred(state, variant):
            return _run_steps_inline(state, variant, self._then)
        else:
            return _run_steps_inline(state, variant, self._else)
        

def branch(
    name: str,
    predicate: Callable[["State", "Variant"], bool],
    then_steps: List["Step"],
    else_steps: List["Step"] | None = None,
) -> "Step":
    """Fabryka kroku BranchStep (zgodna z interfejsem Step)."""
    return BranchStep(name, predicate, then_steps, else_steps)

# -------- 2) FAN-OUT/FAN-IN: krok, który rozdziela i scala --------
class SplitMerge:
    def __init__(
        self,
        name: str,
        items_fn: Callable[["State", "Variant"], Iterable[Any]],
        sub_steps: List["Step"],
        map_item_to_state: Callable[[Any, "State"], "State"] | None = None,
        variant_per_item_fn: Callable[[Any, "Variant"], "Variant"] | None = None,
        aggregate_fn: Callable[["State", List["State"], "Variant"], "State"] | None = None,
        isolate_parent: bool = True,
    ):
        """
        items_fn:        z parent-state tworzy listę elementów do fan-out'u
        sub_steps:       kroki pod-pipeline'u dla każdego elementu
        map_item_to_state:
            jak przygotować sub-state dla pojedynczego elementu (domyślnie: kopia parenta + data['item']=item)
        variant_per_item_fn:
            jak przygotować per-item variant (domyślnie: ten sam variant)
        aggregate_fn:
            jak scalić listę sub-state'ów do parent-state (domyślnie: zapisze listę pod data['fan_results'])
        isolate_parent:
            czy fan-out pracuje na kopii state (zwykle True)
        """
        self.name = name
        self._items_fn = items_fn
        self._sub_steps = sub_steps
        self._map_item_to_state = map_item_to_state or self._default_map_item_to_state
        self._variant_per_item_fn = variant_per_item_fn or (lambda item, e: e)
        self._aggregate_fn = aggregate_fn or self._default_aggregate
        self._isolate_parent = isolate_parent

    @staticmethod
    def _default_map_item_to_state(item: Any, parent_state: "State") -> "State":
        s = copy.deepcopy(parent_state)
        s.data = dict(s.data)
        s.data["item"] = item
        return s

    @staticmethod
    def _default_aggregate(parent_state: "State", sub_states: List["State"], variant: "Variant") -> "State":
        # domyślnie zbierz całe data z sub-state'ów:
        parent_state.data = dict(parent_state.data)
        parent_state.data["fan_results"] = [ss.data for ss in sub_states]
        return parent_state

    def run(self, state: "State", variant: "Variant") -> "State":
        parent = copy.deepcopy(state) if self._isolate_parent else state
        items = list(self._items_fn(parent, variant))
        sub_states: List["State"] = []

        for item in items:
            sub_state = self._map_item_to_state(item, parent)
            sub_variant = self._variant_per_item_fn(item, variant)
            sub_state = _run_steps_inline(sub_state, sub_variant, self._sub_steps)
            sub_states.append(sub_state)

        # fan-in (agregacja do parenta)
        return self._aggregate_fn(parent, sub_states, variant)
    
def split_merge(
    name: str,
    items_fn: Callable[["State", "Variant"], Iterable[Any]],
    sub_steps: List["Step"],
    map_item_to_state: Callable[[Any, "State"], "State"] | None = None,
    variant_per_item_fn: Callable[[Any, "Variant"], "Variant"] | None = None,
    aggregate_fn: Callable[["State", List["State"], "Variant"], "State"] | None = None,
    isolate_parent: bool = True,
) -> "Step":
    """Fabryka kroku FanOutFanInStep."""
    return SplitMerge(
        name,
        items_fn,
        sub_steps,
        map_item_to_state,
        variant_per_item_fn,
        aggregate_fn,
        isolate_parent,
    )

# --- BranchStep -------------------------------------------------------------
register_step(
    "branch",
    lambda *,
        name,
        predicate,
        then_steps,
        else_steps=None: BranchStep(name, predicate, then_steps, else_steps)
)

# --- FanOutFanInStep --------------------------------------------------------
register_step(
    "split_merge",
    lambda *,
        name,
        items_fn,
        sub_steps,
        map_item_to_state=None,
        variant_per_item_fn=None,
        aggregate_fn=None,
        isolate_parent=True: SplitMerge(
            name,
            items_fn,
            sub_steps,
            map_item_to_state,
            variant_per_item_fn,
            aggregate_fn,
            isolate_parent
        )
)