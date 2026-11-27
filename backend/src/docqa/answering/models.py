"""The Models port: the four model roles behind one interface, prompts included.

ClaudeModels is the real adapter. wiring.py builds its two chat models
(Sonnet for the writer, Haiku for the small roles) with effort and max_tokens
from Settings (ADR-0005, ADR-0008). Tests script outputs per role instead.
"""

from collections.abc import Sequence
from typing import Protocol

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, AnyMessage, HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from docqa.answering import prompts
from docqa.answering.citations import NO_ANSWER
from docqa.domain import Passage


class Grade(BaseModel):
    """The grader's verdict on the passages for one search query."""

    sufficient: bool = Field(description="True only if the passages can answer the question")
    relevant: list[int] = Field(description="1-based numbers of the passages that help")


class Models(Protocol):
    def contextualize(self, history: Sequence[AnyMessage], question: str) -> str:
        """The question rewritten to stand without the history."""
        ...

    def grade(self, question: str, passages: Sequence[Passage]) -> Grade: ...

    def rewrite(self, question: str, search_query: str) -> str:
        """One new search query; never an answer."""
        ...

    def write(self, question: str, passages: Sequence[Passage]) -> str:
        """A draft with [n] markers, or NO_ANSWER."""
        ...


def _refused(message: AIMessage) -> bool:
    return message.response_metadata.get("stop_reason") == "refusal"


class ClaudeModels:
    def __init__(self, writer: BaseChatModel, small: BaseChatModel) -> None:
        self._writer = writer
        self._small = small

    def _invoke(self, model: BaseChatModel, system: str, user: str) -> str | None:
        """The reply's text, or None when the API refused."""
        message = model.invoke([SystemMessage(system), HumanMessage(user)])
        return None if _refused(message) else message.text.strip()

    def contextualize(self, history: Sequence[AnyMessage], question: str) -> str:
        user = prompts.contextualize_input(history, question)
        return self._invoke(self._small, prompts.CONTEXTUALIZE, user) or question

    def grade(self, question: str, passages: Sequence[Passage]) -> Grade:
        messages = [
            SystemMessage(prompts.GRADE),
            HumanMessage(prompts.passages_input(question, passages)),
        ]
        # Native structured outputs: forced tool use is not allowed with thinking on.
        grader = self._small.with_structured_output(Grade, method="json_schema", include_raw=True)
        result = grader.invoke(messages)
        parsed = result.get("parsed") if isinstance(result, dict) else None
        # A refusal or an unparseable verdict counts as weak: it can only lead to a refusal.
        return parsed if isinstance(parsed, Grade) else Grade(sufficient=False, relevant=[])

    def rewrite(self, question: str, search_query: str) -> str:
        user = prompts.rewrite_input(question, search_query)
        return self._invoke(self._small, prompts.REWRITE, user) or search_query

    def write(self, question: str, passages: Sequence[Passage]) -> str:
        user = prompts.passages_input(question, passages)
        text = self._invoke(self._writer, prompts.WRITE, user)
        # An API refusal is treated as NO_ANSWER (ADR-0005).
        return NO_ANSWER if text is None else text
