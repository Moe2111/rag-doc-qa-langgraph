"""T4 acceptance: one live question, traced in LangSmith. SPENDS CREDIT.

Ingests one document with Voyage embeddings into an in-memory corpus, then asks
one question through the real answer graph (Haiku grades, Sonnet writes).
Run from backend/ (Settings reads backend/.env); about $0.01-0.05 per run.

    uv run python scripts/ask_live.py ../evals/corpus/nist-csf-2.0.pdf "What are the six CSF 2.0 Functions?"
"""

import argparse
import uuid
from pathlib import Path

from langgraph.checkpoint.memory import InMemorySaver

from docqa.answering import Answerer
from docqa.corpus import Corpus, MemoryChunkStore
from docqa.domain import AskRequest, Upload, WorkspaceId
from docqa.library import Library, MemoryBlobStore
from docqa.settings import Settings
from docqa.wiring import build_embeddings, build_models, configure_tracing


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("path", type=Path)
    parser.add_argument("question")
    args = parser.parse_args()

    settings = Settings(docqa_adapters="live")
    configure_tracing(settings)
    corpus = Corpus(MemoryChunkStore(), build_embeddings(settings))
    ws = WorkspaceId(str(uuid.uuid4()))

    data = args.path.read_bytes()
    upload = Upload(name=args.path.name, content_type="application/pdf", data=data)
    info = Library(corpus, MemoryBlobStore()).add(ws, upload)
    print(f"ingested {info.name}: {info.pages} pages, {info.chunks} chunks")

    answerer = Answerer(
        corpus,
        build_models(settings),
        InMemorySaver(),
        top_k=settings.docqa_top_k,
        max_rewrites=settings.docqa_max_rewrites,
    )
    answer = answerer.ask(AskRequest(workspace=ws, question=args.question))
    print(answer.model_dump_json(indent=2))
    print(f"LangSmith tracing: {settings.langsmith_tracing and bool(settings.langsmith_api_key)}")


if __name__ == "__main__":
    main()
