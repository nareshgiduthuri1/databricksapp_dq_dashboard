"""
Base classes for every pipeline stage.

A stage is a single, well-named unit of work (e.g. "parse XML",
"generate FACT configs"). All stages share the same minimal contract so
the orchestrator can run them uniformly and so individual stages can be
unit-tested or skipped in isolation.
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from pipeline.config import PipelineConfig


@dataclass
class StageResult:
    """Lightweight result envelope returned by every stage."""

    name: str
    success: bool
    duration_sec: float
    payload: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None

    def __str__(self) -> str:  # pragma: no cover - cosmetic
        flag = "OK" if self.success else "FAIL"
        return f"[{flag}] {self.name} ({self.duration_sec:.2f}s)"


class PipelineStage(ABC):
    """
    Abstract base for every pipeline stage.

    Subclasses implement `_run(...)` and return a free-form payload dict.
    The base class times the execution, traps exceptions, and wraps
    everything into a uniform :class:`StageResult`.

    Parameters
    ----------
    config : PipelineConfig
        Pipeline-wide configuration.
    name : str, optional
        Human-readable stage name; defaults to the class name.
    """

    def __init__(self, config: PipelineConfig, name: Optional[str] = None):
        self.config = config
        self.name = name or self.__class__.__name__

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def run(self, context: Optional[Dict[str, Any]] = None) -> StageResult:
        """Execute the stage with timing + error trapping."""
        ctx = context or {}
        self._banner()
        started = time.perf_counter()
        try:
            payload = self._run(ctx) or {}
            duration = time.perf_counter() - started
            return StageResult(
                name=self.name,
                success=True,
                duration_sec=duration,
                payload=payload,
            )
        except SystemExit:
            # Preserve legacy behaviour: some modules call sys.exit(1)
            raise
        except Exception as exc:  # pragma: no cover - defensive
            duration = time.perf_counter() - started
            return StageResult(
                name=self.name,
                success=False,
                duration_sec=duration,
                error=f"{type(exc).__name__}: {exc}",
            )

    # ------------------------------------------------------------------
    # Hooks
    # ------------------------------------------------------------------
    @abstractmethod
    def _run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Subclasses do their work here and return a payload dict."""

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _banner(self) -> None:
        """Print the stage header in the same style as the old script."""
        print("=" * 55)
        print(f"  {self.name}")
        print("=" * 55)
