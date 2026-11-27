"""Pages -> chunks. Splitter settings are a chunking change: they need before/after
eval numbers (docs/CODING_STANDARDS.md)."""

from langchain_core.documents import Document as Page
from langchain_text_splitters import RecursiveCharacterTextSplitter

from docqa.domain import Chunk

_SPLITTER = RecursiveCharacterTextSplitter(chunk_size=1500, chunk_overlap=200, add_start_index=True)


def split(pages: list[Page]) -> list[Chunk]:
    """start_index is the chunk's character offset within its page."""
    return [
        Chunk(
            index=index,
            text=piece.page_content,
            page=piece.metadata["page"],
            start_index=piece.metadata["start_index"],
        )
        for index, piece in enumerate(_SPLITTER.split_documents(pages))
    ]
