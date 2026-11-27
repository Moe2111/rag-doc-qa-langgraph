"""The answer graph (ADR-0003): contextualize, retrieve, grade, at most one
rewrite, then write and check, or refuse. The only path to an answer runs
through the code-level citation check (ADR-0006)."""

from typing import Annotated, Literal, TypedDict

from langchain_core.messages import AIMessage, AnyMessage
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import END, START, StateGraph  # pyright: ignore[reportMissingTypeStubs]  # langgraph ships py.typed at its namespace root only
from langgraph.graph.message import add_messages  # pyright: ignore[reportMissingTypeStubs]  # langgraph ships py.typed at its namespace root only
from langgraph.graph.state import CompiledStateGraph  # pyright: ignore[reportMissingTypeStubs]  # langgraph ships py.typed at its namespace root only

from docqa.answering import citations
from docqa.answering.models import Grade, Models
from docqa.corpus import Corpus
from docqa.domain import Answer, Citation, DocumentId, Passage, WorkspaceId


class AnswerState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]  # the only field that persists across turns
    workspace: WorkspaceId
    thread_id: str  # the caller's public ID, without the workspace prefix
    question: str
    search_query: str
    only: list[DocumentId] | None
    passages: list[Passage]
    grade: Grade | None
    rewrites: int  # reset to 0 on every invoke
    draft: str
    answer: Answer | None


type Update = dict[str, object]
type Graph = CompiledStateGraph[AnswerState, None, AnswerState, AnswerState]


def _answer(state: AnswerState, text: str, *, refused: bool, cited: list[Citation]) -> Update:
    answer = Answer(thread_id=state["thread_id"], text=text, refused=refused, citations=cited)
    return {"answer": answer, "messages": [AIMessage(text)]}


def _relevant(grade: Grade | None, passages: list[Passage]) -> list[Passage]:
    """The passages the grader marked relevant, in its order, without duplicates or
    numbers outside 1..len(passages)."""
    if grade is None:
        return []
    numbers = dict.fromkeys(n for n in grade.relevant if 1 <= n <= len(passages))
    return [passages[n - 1] for n in numbers]


def build_graph(
    corpus: Corpus,
    models: Models,
    checkpointer: BaseCheckpointSaver[str],
    *,
    top_k: int,
    max_rewrites: int,
) -> Graph:
    def contextualize(state: AnswerState) -> Update:
        history = state["messages"][:-1]  # the last message is this turn's question
        if not history:
            return {"search_query": state["question"]}
        standalone = models.contextualize(history, state["question"])
        return {"question": standalone, "search_query": standalone}

    def retrieve(state: AnswerState) -> Update:
        passages = corpus.search(
            state["workspace"], state["search_query"], k=top_k, only=state["only"]
        )
        return {"passages": passages}

    def grade(state: AnswerState) -> Update:
        if not state["passages"]:
            return {"grade": Grade(sufficient=False, relevant=[])}
        return {"grade": models.grade(state["question"], state["passages"])}

    def after_grade(state: AnswerState) -> Literal["write", "rewrite", "refuse"]:
        # sufficient with no usable relevant passage counts as weak.
        grade = state["grade"]
        if grade is not None and grade.sufficient and _relevant(grade, state["passages"]):
            return "write"
        return "rewrite" if state["rewrites"] < max_rewrites else "refuse"

    def rewrite(state: AnswerState) -> Update:
        query = models.rewrite(state["question"], state["search_query"])
        return {"search_query": query, "rewrites": state["rewrites"] + 1}

    def write(state: AnswerState) -> Update:
        relevant = _relevant(state["grade"], state["passages"])  # renumbered [1]..[m]
        return {"passages": relevant, "draft": models.write(state["question"], relevant)}

    def check(state: AnswerState) -> Update:
        cited = citations.check(state["draft"], state["passages"])
        if cited is None:
            return {}
        return _answer(state, state["draft"], refused=False, cited=cited)

    def after_check(state: AnswerState) -> Literal["refuse", "__end__"]:
        return "__end__" if state["answer"] is not None else "refuse"

    def refuse(state: AnswerState) -> Update:
        return _answer(state, citations.REFUSAL, refused=True, cited=[])

    builder = StateGraph(AnswerState)
    nodes = [contextualize, retrieve, grade, rewrite, write, check, refuse]
    for node in nodes:
        builder.add_node(node.__name__, node)  # pyright: ignore[reportUnknownMemberType]  # Unknown is inside langgraph's own overloads
    builder.add_edge(START, "contextualize")
    builder.add_edge("contextualize", "retrieve")
    builder.add_edge("retrieve", "grade")
    builder.add_conditional_edges("grade", after_grade)
    builder.add_edge("rewrite", "retrieve")
    builder.add_edge("write", "check")
    builder.add_conditional_edges("check", after_check)
    builder.add_edge("refuse", END)
    return builder.compile(checkpointer=checkpointer)  # pyright: ignore[reportUnknownMemberType]  # BaseCache[Unknown] in langgraph's signature
