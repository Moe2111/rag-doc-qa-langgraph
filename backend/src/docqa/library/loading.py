"""Bytes -> pages. The type comes from magic bytes, never the name or the declared
content type. One LangChain Document per page (a "page" in docs/GLOSSARY.md)."""

import re
from dataclasses import dataclass
from io import BytesIO
from typing import Literal

from langchain_core.documents import Document as Page
from pypdf import PdfReader
from pypdf.errors import DependencyError, PyPdfError

from docqa.library.errors import UnsupportedFileType

Kind = Literal["pdf", "text"]

_SPACES = re.compile(r"[^\S\n]+")  # whitespace except newlines
_BLANK_LINES = re.compile(r"\n{3,}")


@dataclass(frozen=True)
class Loaded:
    pages: list[Page]  # pages with any text; a blank page is left out
    page_count: int  # every page in the file, blank or not


def classify(data: bytes) -> Kind:
    if data.startswith(b"%PDF-"):
        return "pdf"
    if b"\x00" not in data:
        try:
            data.decode("utf-8")
        except UnicodeDecodeError:
            pass
        else:
            return "text"
    raise UnsupportedFileType("only PDF and UTF-8 text files are supported")


def load(data: bytes, kind: Kind) -> Loaded:
    if kind == "text":
        text = _clean(data.decode("utf-8-sig"))
        return Loaded(
            pages=[Page(page_content=text, metadata={"page": None})] if text else [], page_count=1
        )
    return _load_pdf(data)


def _load_pdf(data: bytes) -> Loaded:
    try:
        reader = PdfReader(BytesIO(data))
        if reader.is_encrypted:
            reader.decrypt("")
        pages: list[Page] = []
        for number, pdf_page in enumerate(reader.pages, start=1):
            text = _clean(pdf_page.extract_text())
            if text:
                pages.append(Page(page_content=text, metadata={"page": number}))
        return Loaded(pages=pages, page_count=len(reader.pages))
    except (PyPdfError, DependencyError, ValueError, KeyError) as error:
        raise UnsupportedFileType("the PDF could not be read") from error


def _clean(text: str) -> str:
    """Collapse runs of spaces and blank lines, but keep line and paragraph breaks:
    the splitter cuts at those before it falls back to spaces."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = (_SPACES.sub(" ", line).strip() for line in text.split("\n"))
    return _BLANK_LINES.sub("\n\n", "\n".join(lines)).strip()
