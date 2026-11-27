"""The Answerer facade: question -> cited answer or refusal, with thread memory.

Threads live in the checkpointer under `{workspace_id}/{thread_id}`, so one
workspace can never reach another's thread (ADR-0009).
"""

import uuid

from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.base import BaseCheckpointSaver

from docqa.answering.errors import ThreadNotFound
from docqa.answering.graph import AnswerState, build_graph
from docqa.answering.models import Models
from docqa.corpus import Corpus
from docqa.domain import Answer, AskRequest


class Answerer:
    def __init__(
        self,
        corpus: Corpus,
        models: Models,
        checkpointer: BaseCheckpointSaver[str],
        *,
        top_k: int = 4,
        max_rewrites: int = 1,
    ) -> None:
        self._checkpointer = checkpointer
        self._graph = build_graph(
            corpus, models, checkpointer, top_k=top_k, max_rewrites=max_rewrites
        )

    def ask(self, request: AskRequest) -> Answer:
        """Raises ThreadNotFound for a thread_id with no checkpoint in this workspace."""
        thread_id = request.thread_id or str(uuid.uuid4())
        config: RunnableConfig = {
            "configurable": {"thread_id": f"{request.workspace}/{thread_id}"},
            "metadata": {"workspace_id": request.workspace, "thread_id": thread_id},
        }
        if request.thread_id is not None and self._checkpointer.get_tuple(config) is None:
            raise ThreadNotFound(thread_id)

        # Every per-turn field gets a fresh value; only messages carries over.
        turn: AnswerState = {
            "messages": [HumanMessage(request.question)],
            "workspace": request.workspace,
            "question": request.question,
            "search_query": "",
            "only": request.document_ids,
            "passages": [],
            "grade": None,
            "rewrites": 0,
            "draft": "",
            "answer": None,
        }
        final = self._graph.invoke(turn, config)  # pyright: ignore[reportUnknownMemberType] Command[Unknown] in langgraph's signature
        answer = final["answer"]
        if answer is None:  # unreachable: every path ends in check (valid) or refuse
            raise RuntimeError("the answer graph ended without an answer")
        return answer.model_copy(update={"thread_id": thread_id})
