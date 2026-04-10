"""Deterministic local rewrite — mirrors the frontend helper (no ML)."""

import re


def rewrite_text(plain_text: str) -> str:
    trimmed = plain_text.strip()
    if not trimmed:
        return ""

    sentences = re.split(r"(?<=[.!?])\s+", trimmed)
    sentences = [s for s in sentences if s]
    if len(sentences) < 2:
        return re.sub(r"\s+", " ", re.sub(r"\bi\b", "I", trimmed)).strip()
    first, *rest = sentences
    out = " ".join([*rest, first])
    return re.sub(r"\s+", " ", re.sub(r"\bi\b", "I", out)).strip()
