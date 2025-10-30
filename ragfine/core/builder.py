# ragfine/registry/builder.py
from __future__ import annotations
from typing import Any, Dict, Union, Tuple, TYPE_CHECKING
import yaml, json
from .registry import STEP_REGISTRY
from .pipeline import Pipeline

if TYPE_CHECKING:
    from ..core.pipeline import Pipeline

def build_step_from_spec(spec: Union[str, Dict[str, Any]]):
    if isinstance(spec, str):
        return STEP_REGISTRY[spec]()  # no-arg factory
    name = spec.get("use") or spec.get("type")
    params = {k: v for k, v in spec.items() if k not in ("use", "type")}
    return STEP_REGISTRY[name](**params)

def pipeline_from_spec(spec: Dict[str, Any]) -> Tuple["Pipeline", Dict[str, Any]]:
    from ..core.pipeline import Pipeline  # local import avoids cycles
    steps = [build_step_from_spec(s) for s in spec.get("steps", [])]
    return Pipeline(steps), (spec.get("defaults") or {})

# ---------------------------------------------------------------------------
# Convenience loaders for YAML / JSON specs
# ---------------------------------------------------------------------------

def pipeline_from_yaml(text_or_path: Union[str, bytes]) -> Tuple["Pipeline", Dict[str, Any]]:
    """
    Build a Pipeline and defaults from YAML text or file path.
    Example:
        pipe, defaults = pipeline_from_yaml(open("spec.yml").read())
    or:
        pipe, defaults = pipeline_from_yaml("spec.yml")
    """
    from pathlib import Path

    # If the argument is a filename (Path or string path)
    if isinstance(text_or_path, (str, Path)) and Path(text_or_path).exists():
        text = Path(text_or_path).read_text(encoding="utf-8")
    else:
        text = text_or_path.decode("utf-8") if isinstance(text_or_path, bytes) else text_or_path

    spec = yaml.safe_load(text)
    return pipeline_from_spec(spec)


def pipeline_from_json(text_or_path: Union[str, bytes]) -> Tuple["Pipeline", Dict[str, Any]]:
    """
    Build a Pipeline and defaults from JSON text or file path.
    Example:
        pipe, defaults = pipeline_from_json(open("spec.json").read())
    or:
        pipe, defaults = pipeline_from_json("spec.json")
    """
    from pathlib import Path

    if isinstance(text_or_path, (str, Path)) and Path(text_or_path).exists():
        text = Path(text_or_path).read_text(encoding="utf-8")
    else:
        text = text_or_path.decode("utf-8") if isinstance(text_or_path, bytes) else text_or_path

    spec = json.loads(text)
    return pipeline_from_spec(spec)