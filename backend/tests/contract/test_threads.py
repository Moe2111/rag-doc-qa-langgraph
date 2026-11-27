"""PostgresSaver threads (ADR-0009): a thread survives a restart, and one
workspace can't reach another's thread. Needs DOCQA_TEST_DATABASE_URL."""

from uuid import uuid4

import pytest
from langchain_core.embeddings import DeterministicFakeEmbedding
from langgraph.checkpoint.postgres import PostgresSaver

from docqa.answering import Answerer, ThreadNotFound
from docqa.corpus import Corpus, MemoryChunkStore
from docqa.domain import AskRequest, WorkspaceId
from tests.fakes import ScriptedModels

pytestmark = pytest.mark.postgres


def _refusing_models(turns: int) -> ScriptedModels:
    """Every turn refuses (empty corpus: no grader call), which still saves the turn."""
    return ScriptedModels(rewrites=["q"] * turns, standalone=["standalone"] * turns)


def _answerer(saver: PostgresSaver, models: ScriptedModels) -> Answerer:
    corpus = Corpus(MemoryChunkStore(), DeterministicFakeEmbedding(size=16))
    return Answerer(corpus, models, saver)


def test_a_thread_survives_a_restart(database_url: str) -> None:
    ws = WorkspaceId(str(uuid4()))
    with PostgresSaver.from_conn_string(database_url) as saver:
        saver.setup()
        first = _answerer(saver, _refusing_models(1)).ask(AskRequest(workspace=ws, question="Q1"))

    with PostgresSaver.from_conn_string(database_url) as saver:  # a new process, in effect
        models = _refusing_models(1)
        _answerer(saver, models).ask(
            AskRequest(workspace=ws, question="Q2", thread_id=first.thread_id)
        )

    assert models.contextualized[0][0][0] == "Q1"


def test_a_thread_is_invisible_to_another_workspace(database_url: str) -> None:
    with PostgresSaver.from_conn_string(database_url) as saver:
        saver.setup()
        answerer = _answerer(saver, _refusing_models(2))
        first = answerer.ask(AskRequest(workspace=WorkspaceId(str(uuid4())), question="Q1"))

        with pytest.raises(ThreadNotFound):
            answerer.ask(
                AskRequest(
                    workspace=WorkspaceId(str(uuid4())), question="Q2", thread_id=first.thread_id
                )
            )
