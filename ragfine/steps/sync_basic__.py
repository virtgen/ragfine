"""
ragfine.steps.sync_basic
------------------------

Domain steps for a linear QA-style pipeline:

Entifier  -> extracts simple entities from text
Questor   -> generates questions about those entities
Solver    -> produces answers to the questions
Integrator-> stitches Q/A into a single text
Refiner   -> polishes style/spacing
Rebaser   -> applies final tweaks from Variant (prefix/suffix)

Each class implements: run(state: State, variant: dict) -> State
and is registered via register_step("<Name>", factory).

USAGE:
    from ragfine.core.pipeline import Pipeline
    from ragfine.core.state import State
    from ragfine.steps.sync_basic import entify, quest, solve, integrate, refine, rebase

    pipe = Pipeline([
        entify(),
        quest(),
        solve(),
        integrate(),
        refine(ensure_trailing_newline=True),
        rebase(),
    ])

    state = State(data={"text": "Alice emailed Bob via https://example.com"})
    report = pipe.run(state)[0]
    print(report.final_state.data["result"])
"""

from __future__ import annotations
from typing import Any, Dict, Iterable, List
import re

from ..core.pipebase import State
from ..core.registry import register_step

Variant = Dict[str, Any]


# ----------------------------- utils ---------------------------------------
_WORD_RE = re.compile(r"[A-Za-zÀ-ÖØ-öø-ÿ]+(?:[-'][A-Za-zÀ-ÖØ-öø-ÿ]+)*")
_EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
_URL_RE = re.compile(
    r"\bhttps?://[^\s)]+", flags=re.IGNORECASE
)

def _split_sentences(text: str) -> List[str]:
    # Simple sentence splitter; avoids heavy deps
    parts = re.split(r"(?<=[.!?])\s+(?=[A-ZÀ-ÖØ-öø-ÿ])", text.strip())
    return [p.strip() for p in parts if p.strip()]

def _unique(seq: Iterable[str]) -> List[str]:
    seen = set()
    out: List[str] = []
    for x in seq:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out


# ----------------------------- steps ---------------------------------------

class Entifier:
    """
    Very lightweight "entity" finder:
      - Proper-cased words (TitleCase) as pseudo-PER/ORG
      - Emails
      - URLs
    Stores under state.data['entities'] as list[str]
    """
    def __init__(self, name: str = "Entifier"):
        self.name = name

    def run(self, state: State, variant: Variant) -> State:
        text = state.data.get("text", "") or ""
        words = _WORD_RE.findall(text)

        titlecase = [w for w in words if w[:1].isupper() and w.lower() != w]
        emails = _EMAIL_RE.findall(text)
        urls = _URL_RE.findall(text)

        entities = _unique(titlecase + emails + urls)
        state.data["entities"] = entities
        return state


register_step("Entifier", lambda **kw: Entifier(**kw))

def entify(name: str = "Entifier") -> "Entifier":
    """Factory: Entifier()"""
    return Entifier(name=name)

register_step("entify", lambda **kw: entify(**kw))



class Questor:
    """
    Generates naive questions about entities or per sentence.
    Stores under state.data['questions'] as list[str]
    """
    def __init__(self, name: str = "Questor"):
        self.name = name

    def run(self, state: State, variant: Variant) -> State:
        text = state.data.get("text", "") or ""
        ents: List[str] = state.data.get("entities", []) or []
        sents = _split_sentences(text)

        qs: List[str] = []
        if ents:
            for e in ents:
                if "@" in e:
                    qs.append(f"Who uses the email '{e}'?")
                elif e.startswith("http"):
                    qs.append(f"What is the purpose of the URL '{e}'?")
                else:
                    qs.append(f"What is {e}?")
        else:
            # fallback: generic per-sentence questions
            qs = [f"What is the main point of: '{s}'?" for s in sents]

        state.data["questions"] = _unique(qs)
        return state


register_step("Questor", lambda **kw: Questor(**kw))

def quest(name: str = "Questor") -> "Questor":
    """Factory: Questor()"""
    return Questor(name=name)

register_step("quest", lambda **kw: quest(**kw))


class Solver:
    """
    Produces naive answers by heuristics:
      - Emails -> 'contact detail'
      - URLs   -> 'a referenced link'
      - TitleCase -> 'a named entity'
      - Else -> brief paraphrase
    Stores under state.data['answers'] as list[str],
    aligned by index with state.data['questions'].
    """
    def __init__(self, name: str = "Solver"):
        self.name = name

    def run(self, state: State, variant: Variant) -> State:
        qs: List[str] = state.data.get("questions", []) or []
        answers: List[str] = []

        for q in qs:
            # Extract a token inside quotes if present
            m = re.search(r"'([^']+)'", q)
            token = m.group(1) if m else None

            if token and "@" in token:
                answers.append(f"'{token}' appears to be a contact detail (email).")
            elif token and token.startswith("http"):
                answers.append(f"'{token}' is a referenced web link (URL).")
            else:
                # Try to capture entity-style token (capitalized word) from the question
                cap = re.search(r"\b([A-ZÀ-ÖØ-öø-ÿ][\w'-]+)\b", q)
                if cap:
                    answers.append(f"{cap.group(1)} looks like a named entity mentioned in the text.")
                else:
                    answers.append("It refers to a key point inferred from the sentence.")

        state.data["answers"] = answers
        return state


register_step("Solver", lambda **kw: Solver(**kw))

def solve(name: str = "Solver") -> "Solver":
    """Factory: Solver()"""
    return Solver(name=name)

register_step("solve", lambda **kw: solve(**kw))


class Integrator:
    """
    Stitches Q/A into a single markdown-ish section.
    Writes to state.data['summary'] and state.data['result'] (same at this stage).
    """
    def __init__(self, name: str = "Integrator"):
        self.name = name

    def run(self, state: State, variant: Variant) -> State:
        qs: List[str] = state.data.get("questions", []) or []
        ans: List[str] = state.data.get("answers", []) or []

        lines: List[str] = []
        for i, q in enumerate(qs):
            a = ans[i] if i < len(ans) else ""
            lines.append(f"- {q} → {a}")

        summary = "\n".join(lines).strip()
        state.data["summary"] = summary
        state.data["result"] = summary
        return state


register_step("Integrator", lambda **kw: Integrator(**kw))

def integrate(name: str = "Integrator") -> "Integrator":
    """Factory: Integrator()"""
    return Integrator(name=name)

register_step("integrate", lambda **kw: integrate(**kw))


class Refiner:
    """
    Light formatting:
      - squeeze multiple blank lines
      - trim whitespace
      - ensure final newline optionally
    """
    def __init__(self, name: str = "Refiner", ensure_trailing_newline: bool = False):
        self.name = name
        self.ensure_trailing_newline = ensure_trailing_newline

    def run(self, state: State, variant: Variant) -> State:
        result = state.data.get("result", "") or ""

        # collapse excessive blank lines and spaces around arrows
        result = re.sub(r"[ \t]+\n", "\n", result)
        result = re.sub(r"\n{3,}", "\n\n", result)
        result = re.sub(r"\s*→\s*", " → ", result)
        result = result.strip()

        if self.ensure_trailing_newline and not result.endswith("\n"):
            result += "\n"

        state.data["result"] = result
        return state


register_step("Refiner", lambda **kw: Refiner(**kw))

def refine(name: str = "Refiner", *, ensure_trailing_newline: bool = False) -> "Refiner":
    """Factory: Refiner(ensure_trailing_newline=...)"""
    return Refiner(name=name, ensure_trailing_newline=ensure_trailing_newline)

register_step("refine", lambda **kw: refine(**kw))

class Rebaser:
    """
    Final, optional cosmetic changes driven by Variant:
      - style_prefix: string to prepend to result
      - style_suffix: string to append to result
    """
    def __init__(self, name: str = "Rebaser"):
        self.name = name

    def run(self, state: State, variant: Variant) -> State:
        result = state.data.get("result", "") or ""
        prefix = variant.get("style_prefix", "")
        suffix = variant.get("style_suffix", "")

        state.data["result"] = f"{prefix}{result}{suffix}"
        return state


register_step("Rebaser", lambda **kw: Rebaser(**kw))

def rebase(name: str = "Rebaser") -> "Rebaser":
    """Factory: Rebaser()"""
    return Rebaser(name=name)

register_step("rebase", lambda **kw: rebase(**kw))


__all__ = [
    "Entifier", "Questor", "Solver", "Integrator", "Refiner", "Rebaser",
    "entify", "quest", "solve", "integrate", "refine", "rebase",
]
