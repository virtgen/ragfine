from __future__ import annotations
from .pipebase import *
from .pipebase import _normalize_step, _run_step_async
from itertools import product
import time, copy
from .registry import register_step
# --- Async helpers and imports ---
import asyncio, inspect


class Pipeline:
    def __init__(self, steps: List[Step]):
        self.steps = [_normalize_step(s) for s in steps]

    # --- batch run over iterable of Variants ---
    def run(
        self,
        state: "Optional[State]" = None,
        *,
        variants: "Union[Variant, Iterable[Variant], None]" = None,
        defaults: "Optional[Variant]" = None,  # merged into each item
        async_mode: bool = False,
        step_timeout: "Optional[float]" = None,
        overall_timeout: "Optional[float]" = None,
        variant_concurrency: "Optional[int]" = None,
    ) -> "List[PipelineReport]":
        # Normalize Variants to a list
        if variants is None:
            Variants_list: "List[Variant]" = [{}]
        elif isinstance(variants, dict):
            Variants_list = [variants]
        else:
            Variants_list = list(variants)

        defaults = defaults or {}

        # Synchronous mode (backward compatible)
        if not async_mode:
            reports: "List[PipelineReport]" = []
            for v in Variants_list:
                variant = {**defaults, **v}  # per-run Variant params
                report: "List[Dict[str, Any]]" = []
                st = copy.deepcopy(state or State())  # isolate each run

                for step_obj in self.steps:
                    t0 = time.perf_counter()
                    ok, err = True, None
                    try:
                        res = step_obj.run(st, variant)
                        # Guard: do not allow awaitables in sync mode
                        if inspect.isawaitable(res):
                            raise RuntimeError(
                                f"Step '{getattr(step_obj, 'name', step_obj.__class__.__name__)}' returned awaitable in sync mode. Set async_mode=True."
                            )
                        st = res
                    except Exception as e:
                        ok, err = False, repr(e)
                        raise
                    finally:
                        report.append({
                            "name": getattr(step_obj, "name", step_obj.__class__.__name__),
                            "ok": ok,
                            "error": err,
                            "duration_s": round(time.perf_counter() - t0, 6),
                        })
                reports.append(PipelineReport(report, st))
            return reports

        # Async mode: run steps with await/timeout; optionally parallelize variants
        async def _run_one_variant(v: "Variant") -> "PipelineReport":
            variant = {**defaults, **v}
            report: "List[Dict[str, Any]]" = []
            st = copy.deepcopy(state or State())

            async def _execute_all():
                nonlocal st
                for step_obj in self.steps:
                    t0 = time.perf_counter()
                    ok, err = True, None
                    try:
                        st = await _run_step_async(step_obj, st, variant, step_timeout)
                    except Exception as e:
                        ok, err = False, repr(e)
                        raise
                    finally:
                        report.append({
                            "name": getattr(step_obj, "name", step_obj.__class__.__name__),
                            "ok": ok,
                            "error": err,
                            "duration_s": round(time.perf_counter() - t0, 6),
                        })

            if overall_timeout is not None:
                await asyncio.wait_for(_execute_all(), timeout=overall_timeout)
            else:
                await _execute_all()

            return PipelineReport(report, st)

        sem = asyncio.Semaphore(variant_concurrency) if variant_concurrency else None

        async def _run_all_async():
            async def _guard(v: "Variant") -> "PipelineReport":
                if sem:
                    async with sem:
                        return await _run_one_variant(v)
                return await _run_one_variant(v)
            tasks = [asyncio.create_task(_guard(v)) for v in Variants_list]
            return await asyncio.gather(*tasks)

        return asyncio.run(_run_all_async())

def _is_expandable(value: Any) -> bool:
    """Traktuj jako rozwijalne, jeśli to iterowalne i nie jest str/bytes/dict."""
    if isinstance(value, (str, bytes, dict)):
        return False
    try:
        iter(value)
        return True
    except TypeError:
        return False

def combine(
    params: Dict[str, Any],
    defaults: Dict[str, Any] | None = None,
    *,
    mode: str = "cartesian"
) -> List[Variant]:
    """
    Rozwija słownik parametrów w listę słowników wariantów.

    mode:
        - "cartesian" (domyślnie): iloczyn kartezjański po wszystkich iterowalnych wartościach.
        - "zip": łączy wartości parami (jak zip), skracając do najkrótszej listy.

    Wartości nieiterowalne traktowane są jako stałe.
    Parametr `defaults` (opcjonalny) zostanie dołączony do każdego wariantu.

    Przykład:
        params = {"style": ["A", "B"], "answer": ["Yes", "No"], "meta": True}
        defaults = {"lang": "en"}
        combine(params, defaults)
        -> [
            {'style': 'A', 'answer': 'Yes', 'meta': True, 'lang': 'en'},
            {'style': 'A', 'answer': 'No',  'meta': True, 'lang': 'en'},
            {'style': 'B', 'answer': 'Yes', 'meta': True, 'lang': 'en'},
            {'style': 'B', 'answer': 'No',  'meta': True, 'lang': 'en'}
        ]
    """
    defaults = defaults or {}

    # Podział na klucze rozwijalne (listy/iterowalne) i stałe
    expand_keys = []
    expand_values = []
    fixed_items = {}

    for k, v in params.items():
        if _is_expandable(v):
            expand_keys.append(k)
            expand_values.append(list(v))  # materializacja generatorów/range
        else:
            fixed_items[k] = v

    # Jeśli nie ma czego rozwijać → zwróć pojedynczą kombinację (defaults + params)
    if not expand_keys:
        merged = dict(defaults)
        merged.update(params)
        return [merged]

    # Iloczyn kartezjański po wartościach kluczy rozwijalnych
    combos: List[Variant] = []
    for combo in product(*expand_values):
        c = dict(defaults)         # defaults na start
        c.update(fixed_items)      # stałe parametry
        c.update(zip(expand_keys, combo))  # rozwinięte wartości
        combos.append(c)
    return combos


