"""Ingest files through Library with memory adapters and fake embeddings.

Offline smoke check for T3: no keys, no network, no paid APIs.

    uv run python scripts/ingest.py ../evals/corpus/nist-csf-2.0.pdf [more files...]
"""

import argparse
import mimetypes
import uuid
from pathlib import Path

from langchain_core.embeddings import DeterministicFakeEmbedding

from docqa.corpus import Corpus, MemoryChunkStore
from docqa.domain import Upload, WorkspaceId
from docqa.library import Library, MemoryBlobStore


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("paths", nargs="+", type=Path)
    parser.add_argument("--max-bytes", type=int, default=10_000_000)
    args = parser.parse_args()

    corpus = Corpus(MemoryChunkStore(), DeterministicFakeEmbedding(size=512))
    library = Library(corpus, MemoryBlobStore(), max_bytes=args.max_bytes)
    ws = WorkspaceId(str(uuid.uuid4()))

    for path in args.paths:
        content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        upload = Upload(name=path.name, content_type=content_type, data=path.read_bytes())
        try:
            info = library.add(ws, upload)
        except Exception as error:
            print(f"{path.name}: {type(error).__name__}: {error}")
            continue
        print(info.model_dump_json())

    for passage in corpus.search(ws, "governance", k=2):
        print(f"  sample chunk p.{passage.page} of {passage.name}: {passage.text[:100]!r}")


if __name__ == "__main__":
    main()
