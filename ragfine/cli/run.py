#!/usr/bin/env python3
import argparse
import sys
import json
from pathlib import Path
import inspect

# Auto-register built-in steps on import
import ragfine.steps  # noqa: F401

from ragfine import State, pipeline_from_yaml, pipeline_from_json

def main():
    ap = argparse.ArgumentParser(description="Run a ragfine pipeline from YAML/JSON spec.")
    ap.add_argument("--spec", required=True, help="Path to YAML/JSON pipeline spec (or '-' for stdin)")
    ap.add_argument("--async", dest="async_mode", action="store_true",
                    help="Run in async mode if pipeline supports it")
    ap.add_argument("--text", default="Alice greets Bob.\nBob smiles back.",
                    help="Initial text to place in State.data['text']")
    args = ap.parse_args()

    # Read spec (file or stdin)
    if args.spec == "-":
        raw = sys.stdin.read()
        suffix = ""
    else:
        p = Path(args.spec)
        if not p.exists():
            sys.exit(f"Spec not found: {args.spec}")
        raw = p.read_text(encoding="utf-8")
        suffix = p.suffix.lower()

    # Build pipeline
    try:
        if suffix in (".yml", ".yaml"):
            pipe, defaults = pipeline_from_yaml(raw)
        elif suffix == ".json" or suffix == "":
            # try JSON first; if it fails and no suffix, try YAML as fallback
            try:
                pipe, defaults = pipeline_from_json(raw)
            except Exception:
                pipe, defaults = pipeline_from_yaml(raw)
        else:
            # unknown suffix: try YAML then JSON
            try:
                pipe, defaults = pipeline_from_yaml(raw)
            except Exception:
                pipe, defaults = pipeline_from_json(raw)
    except Exception as e:
        sys.exit(f"Failed to build pipeline from spec: {e}")

    # Prepare initial state
    initial = State(data={"text": args.text})

    # Prepare kwargs for run(); pass async_mode only if supported
    run_kwargs = {
        "variants": [
            {"style_suffix": "\n—A"},
            {"style_suffix": "\n—B"},
        ],
        "defaults": defaults or {},
    }
    if "async_mode" in inspect.signature(pipe.run).parameters:
        run_kwargs["async_mode"] = args.async_mode

    # Execute
    try:
        reports = pipe.run(initial, **run_kwargs)
    except Exception as e:
        sys.exit(f"Pipeline execution failed: {e}")

    # Output
    for i, rep in enumerate(reports, 1):
        print(f"\n=== RUN {i} ===")
        print(rep.final_state.data.get("result", ""))

if __name__ == "__main__":
    main()