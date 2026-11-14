"""
STTM-to-Code pipeline package.

Exposes the two entry points used by ``main.py``:

    from pipeline import Pipeline, PipelineConfig

NOTE (recovery): this ``__init__`` was reconstructed by inference — the
original was not available verbatim. It re-exports the same two symbols
``main.py`` imports; adjust if your original exposed more.
"""

from pipeline.config import PipelineConfig
from pipeline.orchestrator import Pipeline

__all__ = ["Pipeline", "PipelineConfig"]
