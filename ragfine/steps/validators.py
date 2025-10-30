# validators.py
from functools import wraps
from typing import Type, Callable, Any, Dict
from pydantic import BaseModel, ValidationError
import inspect

def validate_io(
    *,
    input_model: Type[BaseModel],
    output_model: Type[BaseModel],
    # where to read/write in State (defaults assume your State has .data: dict)
    input_from: str = "data",
    output_to: str = "data",
    merge_output: bool = True,  # merge output into state.data vs overwrite key
):
    """
    Decorate a step (class.run or function) to:
      - validate input: input_model(**getattr(state, input_from))
      - run the step
      - validate output: output_model(**<dict from result or mutated state>)
      - write back to getattr(state, output_to)

      NOTE:
      	For partial outputs (e.g., just {"entities": [...]}), merge_output=True keeps the rest of state.data.
		Validation errors are raised as ValueError(...) with clear messages.
      EXAMPLE for function:
        @step("EntifierFn")
        @validate_io(input_model=EntifierInput, output_model=EntifierOutput)
        def entify_fn(state, variant):
            text = (state.data.get("text") or "").strip()
            state.data["entities"] = [w for w in text.split() if w.istitle()]
            return state
    """
    def decorator(fn):
        sig = inspect.signature(fn)

        @wraps(fn)
        def wrapper(*args, **kwargs):
            # Determine if called as bound method (first arg is 'self')
            is_method = False
            if args and hasattr(args[0], "__class__"):
                # Heuristic: method has at least (self, state)
                params = list(sig.parameters)
                if params and params[0] in ("self",):
                    is_method = True

            # Extract state & variant positions
            if is_method:
                # (self, state, variant)
                if len(args) < 2:
                    raise TypeError(f"{fn.__name__} expected at least (self, state)")
                self_obj = args[0]
                state = args[1]
                variant = args[2] if len(args) > 2 else kwargs.get("variant", {})
            else:
                # (state, variant)
                if not args:
                    raise TypeError(f"{fn.__name__} expected at least (state)")
                self_obj = None
                state = args[0]
                variant = args[1] if len(args) > 1 else kwargs.get("variant", {})

            # 1) validate input
            try:
                _ = input_model(**getattr(state, input_from))
            except ValidationError as e:
                raise ValueError(f"[{fn.__name__}] input validation failed: {e}") from e

            # 2) call original
            result = fn(*args, **kwargs)

            # 3) obtain resulting state (method may mutate and return state)
            result_state = result if result is not None else state

            # 4) validate output
            out_source = getattr(result_state, output_to)
            if not isinstance(out_source, dict):
                raise TypeError(f"[{fn.__name__}] expected dict-like state.{output_to}, got {type(out_source)}")

            try:
                out = output_model(**out_source)
            except ValidationError as e:
                raise ValueError(f"[{fn.__name__}] output validation failed: {e}") from e

            if merge_output:
                out_source.update(out.model_dump())
            else:
                setattr(result_state, output_to, out.model_dump())

            return result_state

        return wrapper
    return decorator