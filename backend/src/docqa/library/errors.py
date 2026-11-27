"""Domain errors raised by Library.add. The server maps each to an HTTP code (T5);
this module never knows about HTTP."""


class FileTooLarge(Exception):
    """The upload is over the per-file byte limit (413)."""


class UnsupportedFileType(Exception):
    """The bytes are not a readable PDF or UTF-8 text (415)."""


class NoTextFound(Exception):
    """The file parsed but holds no extractable text, e.g. a scanned PDF (422)."""


class WorkspaceFull(Exception):
    """A new document would exceed the per-workspace document limit (409)."""
