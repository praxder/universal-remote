"""Famous movie/TV quotes for the landing menu, loaded from packaged data."""

from __future__ import annotations

import random
from dataclasses import dataclass
from importlib import resources


@dataclass(frozen=True)
class Quote:
    """A quote and its attribution: who said it and where it is from."""

    text: str
    character: str
    source: str


def load_quotes(source: str | None = None) -> list[Quote]:
    """Parse `text|character|source` lines, skipping blank and malformed ones.

    With no `source`, reads the packaged `data/quotes.txt`; a missing file
    yields an empty list rather than raising.
    """
    text = _packaged_text() if source is None else source
    quotes = []
    for line in text.splitlines():
        parts = [part.strip() for part in line.split("|")]
        if len(parts) != 3 or not all(parts):
            continue
        quotes.append(Quote(*parts))
    return quotes


def random_quote(quotes: list[Quote] | None = None) -> Quote | None:
    """Pick one quote at random, or None when there are none."""
    quotes = load_quotes() if quotes is None else quotes
    return random.choice(quotes) if quotes else None


def _packaged_text() -> str:
    resource = resources.files("universal_remote.tui").joinpath("data", "quotes.txt")
    try:
        return resource.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""
