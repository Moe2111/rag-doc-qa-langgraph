"""Test doubles shared across test modules."""

from collections.abc import Sequence

from langchain_core.messages import AnyMessage

from docqa.answering import Grade
from docqa.domain import Passage


class ScriptedModels:
    """Each role returns its scripted outputs in order and records what it was given."""

    def __init__(
        self,
        *,
        grades: Sequence[Grade] = (),
        drafts: Sequence[str] = (),
        rewrites: Sequence[str] = (),
        standalone: Sequence[str] = (),
    ) -> None:
        self._grades = list(grades)
        self._drafts = list(drafts)
        self._rewrites = list(rewrites)
        self._standalone = list(standalone)
        self.contextualized: list[tuple[list[str], str]] = []
        self.graded: list[str] = []
        self.rewritten: list[str] = []
        self.written: list[list[Passage]] = []

    def contextualize(self, history: Sequence[AnyMessage], question: str) -> str:
        self.contextualized.append(([m.text for m in history], question))
        return self._standalone.pop(0)

    def grade(self, question: str, passages: Sequence[Passage]) -> Grade:
        self.graded.append(question)
        return self._grades.pop(0)

    def rewrite(self, question: str, search_query: str) -> str:
        self.rewritten.append(search_query)
        return self._rewrites.pop(0)

    def write(self, question: str, passages: Sequence[Passage]) -> str:
        self.written.append(list(passages))
        return self._drafts.pop(0)
