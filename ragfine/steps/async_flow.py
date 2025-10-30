from ..core.registry import register_step
from ..core.pipebase import _normalize_step, _run_steps_inline, _run_step_async
from typing import Any, Dict, List, Callable, Protocol, Iterable, Optional, Union
import copy
# --- Async helpers and imports ---
import asyncio, inspect

# --- Async Branch (then/else) ---------------------------------------------
class AsyncBranchStep:
    def __init__(
        self,
        name: str,
        predicate: "Callable[[State, Variant], Any]",
        then_steps: "List[Step]",
        else_steps: "List[Step] | None" = None,
        nested_step_timeout: "Optional[float]" = None,
    ):
        self.name = name
        self._pred = predicate
        self._then = then_steps
        self._else = else_steps or []
        self._nested_step_timeout = nested_step_timeout

    async def run(self, state: "State", variant: "Variant") -> "State":
        # predicate may be sync or async
        res = self._pred(state, variant)
        decision = await res if inspect.isawaitable(res) else res
        steps = self._then if decision else self._else

        s = state
        for st in steps:
            # use the async helper defined at top of file
            s = await _run_step_async(st, s, variant, self._nested_step_timeout)
        return s

# --- Async Fan-Out/Fan-In with optional concurrency -----------------------
class AsyncSplitMerge:
    def __init__(
        self,
        name: str,
        items_fn: "Callable[[State, Variant], Any]",
        sub_steps: "List[Step]",
        map_item_to_state: "Callable[[Any, State], State] | None" = None,
        variant_per_item_fn: "Callable[[Any, Variant], Variant] | None" = None,
        aggregate_fn: "Callable[[State, List[State], Variant], Any] | None" = None,
        isolate_parent: bool = True,
        item_concurrency: "Optional[int]" = None,
        per_substep_timeout: "Optional[float]" = None,
        per_item_timeout: "Optional[float]" = None,
    ):
        self.name = name
        self._items_fn = items_fn
        self._sub_steps = sub_steps
        self._map_item_to_state = map_item_to_state or self._default_map_item_to_state
        self._variant_per_item_fn = variant_per_item_fn or (lambda item, v: v)
        self._aggregate_fn = aggregate_fn or self._default_aggregate
        self._isolate_parent = isolate_parent
        self._item_concurrency = item_concurrency
        self._per_substep_timeout = per_substep_timeout
        self._per_item_timeout = per_item_timeout

    @staticmethod
    def _default_map_item_to_state(item: Any, parent_state: "State") -> "State":
        s = copy.deepcopy(parent_state)
        s.data = dict(s.data)
        s.data["item"] = item
        return s

    @staticmethod
    def _default_aggregate(parent_state: "State", sub_states: "List[State]", variant: "Variant") -> "State":
        parent_state.data = dict(parent_state.data)
        parent_state.data["fan_results"] = [ss.data for ss in sub_states]
        return parent_state

    async def run(self, state: "State", variant: "Variant") -> "State":
        parent = copy.deepcopy(state) if self._isolate_parent else state

        # items_fn may be sync or async
        items_val = self._items_fn(parent, variant)
        items = list(await items_val) if inspect.isawaitable(items_val) else list(items_val)

        results: "List[State]" = []
        lock = asyncio.Lock()
        sem = asyncio.Semaphore(self._item_concurrency) if self._item_concurrency else None

        async def process_item(item: Any):
            sub_state = self._map_item_to_state(item, parent)
            v_val = self._variant_per_item_fn(item, variant)
            sub_variant = await v_val if inspect.isawaitable(v_val) else v_val

            async def run_substeps():
                s = sub_state
                for st in self._sub_steps:
                    s = await _run_step_async(st, s, sub_variant, self._per_substep_timeout)
                return s

            s_final = await asyncio.wait_for(run_substeps(), timeout=self._per_item_timeout) \
                      if self._per_item_timeout else await run_substeps()

            async with lock:
                results.append(s_final)

        async def guard(item: Any):
            if sem:
                async with sem:
                    await process_item(item)
            else:
                await process_item(item)

        await asyncio.gather(*(asyncio.create_task(guard(it)) for it in items))

        agg = self._aggregate_fn(parent, results, variant)
        return await agg if inspect.isawaitable(agg) else agg


register_step(
    "branch_async",
    lambda *,
        name,
        predicate,
        then_steps,
        else_steps=None,
        nested_step_timeout=None: AsyncBranchStep(
            name,
            predicate,
            then_steps,
            else_steps,
            nested_step_timeout
        )
)

register_step(
    "split_merge_async",
    lambda *,
        name,
        items_fn,
        sub_steps,
        map_item_to_state=None,
        variant_per_item_fn=None,
        aggregate_fn=None,
        isolate_parent=True,
        item_concurrency=None,
        per_substep_timeout=None,
        per_item_timeout=None: AsyncSplitMerge(
            name,
            items_fn,
            sub_steps,
            map_item_to_state,
            variant_per_item_fn,
            aggregate_fn,
            isolate_parent,
            item_concurrency,
            per_substep_timeout,
            per_item_timeout
        )
)