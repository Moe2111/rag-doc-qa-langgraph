"""The citation check (ADR-0006): pure code, the only path from a draft to an answer."""

import re
from collections.abc import Sequence

from docqa.domain import Citation, Passage

NO_ANSWER = "NO_ANSWER"
REFUSAL = "I don't know based on the documents provided."  # v1's sentence, word for word
SNIPPET_CHARS = 200

_MARKER = re.compile(r"\[(\d+)\]")


def check(draft: str, passages: Sequence[Passage]) -> list[Citation] | None:
    """The citations for a valid draft, or None when it must become a refusal.

    Rejects NO_ANSWER, a draft with no [n] marker, and any marker outside 1..m,
    where m is the number of passages the writer saw.
    """
    if NO_ANSWER in draft:
        return None
    markers = {int(n) for n in _MARKER.findall(draft)}
    if not markers or any(not 1 <= n <= len(passages) for n in markers):
        return None
    return [
        Citation(
            n=n,
            document_id=passages[n - 1].document_id,
            name=passages[n - 1].name,
            page=passages[n - 1].page,
            snippet=passages[n - 1].text[:SNIPPET_CHARS],
        )
        for n in sorted(markers)
    ]
