"""Domain errors raised by Answerer.ask. The server maps them to HTTP codes (T5)."""


class ThreadNotFound(Exception):
    """A thread_id with no checkpoint in this workspace (404 thread_not_found)."""
