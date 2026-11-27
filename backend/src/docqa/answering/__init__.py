"""The answering module: question -> cited answer or refusal.

Public interface (import only these; see docs/ARCHITECTURE.md, Modules):
    Answerer        the facade: ask
    Models, Grade   the model-roles port and the grader's verdict
    ClaudeModels    the real Models adapter; wiring.py builds its chat models
    ThreadNotFound  raised by ask for an unknown thread
    REFUSAL         the fixed refusal sentence

wiring.py is the only caller that picks adapters (ADR-0008).
"""

from docqa.answering.citations import REFUSAL
from docqa.answering.errors import ThreadNotFound
from docqa.answering.models import ClaudeModels, Grade, Models
from docqa.answering.service import Answerer

__all__ = ["REFUSAL", "Answerer", "ClaudeModels", "Grade", "Models", "ThreadNotFound"]
