from __future__ import annotations
import re
from typing import Iterable, List

WORD_RE = re.compile(r"[A-Za-zÀ-ÖØ-öø-ÿ]+(?:[-'][A-Za-zÀ-ÖØ-öø-ÿ]+)*")
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
URL_RE = re.compile(r"\bhttps?://[^\s)]+", flags=re.IGNORECASE)

_SENT_SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-ZÀ-ÖØ-öø-ÿ])")

def unique(seq: Iterable[str]) -> List[str]:
    seen = set()
    out: List[str] = []
    for x in seq:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out

def split_sentences(text: str) -> List[str]:
    if not text:
        return []
    parts = _SENT_SPLIT.split(text.strip())
    return [p.strip() for p in parts if p.strip()]