"""
Pipeline orchestrator.

Wires the individual stages together in the exact order the original
`main.py` ran them. Each stage is independent and can be skipped, swapped,
or unit-tested on its own — this class only sequences them and threads a
shared `context` dict between stages.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pipeline.base import PipelineStage, StageResult
from pipeline.config import PipelineConfig
from pipeline.stages.xml_to_json import XmlToJsonStage
from pipeline.stages.sttm_filter import SttmFilterStage
from pipeline.stages.ddl_generation import DdlGenerationStage
from pipeline.stages.dim_scd2 import DimSCD2ConfigStage
from pipeline.stages.fact import FactConfigStage
from pipeline.stages.dim_scd1 import DimSCD1ConfigStage
from pipeline.stages.notebook import NotebookAssemblyStage
from pipeline.stages.json_to_csv import JsonToCsvStage
from pipeline.stages.raw_vault import RawVaultConfigStage
from modules import generation_profiles as _gp


class Pipeline:
    """
    Default end-to-end STTM-to-Code pipeline.

    Usage
    -----
    >>> from pipeline import Pipeline, PipelineConfig
    >>> cfg = PipelineConfig.from_env()
    >>> Pipeline(cfg).run()

    Custom assembly
    ---------------
    >>> Pipeline(cfg, stages=[XmlToJsonStage(cfg), SttmFilterStage(cfg)]).run()
    """

    def __init__(
        self,
        config: PipelineConfig,
        stages: Optional[List[PipelineStage]] = None,
    ):
        self.config = config
        self.stages: List[PipelineStage] = stages or self._default_stages()
        self.results: List[StageResult] = []

    # ------------------------------------------------------------------
    # Default pipeline graph
    # ------------------------------------------------------------------
    def _default_stages(self) -> List[PipelineStage]:
        cfg = self.config

        # Stages common to every target model.
        common = [
            XmlToJsonStage(cfg),
            SttmFilterStage(cfg),
            DdlGenerationStage(cfg),
        ]

        # Stage 3+ depends on the target model.
        if _gp.get_target_model() == _gp.TARGET_RAW_DATA_VAULT:
            # Bronze -> Raw Data Vault: hub/sat/link config generation only.
            # (No SCD/FACT generation, notebook assembly, or lineage CSV.)
            return common + [RawVaultConfigStage(cfg)]

        # Dimensional / Business Vault: original flow (unchanged).
        return common + [
            DimSCD2ConfigStage(cfg),
            FactConfigStage(cfg),
            DimSCD1ConfigStage(cfg),
            NotebookAssemblyStage(cfg),
            JsonToCsvStage(cfg),
        ]

    # ------------------------------------------------------------------
    # Execution
    # ------------------------------------------------------------------
    def run(self) -> List[StageResult]:
        """Run every stage in order, sharing a context dict."""
        print(self.config.describe())
        print()

        context: Dict[str, Any] = {}
        for stage in self.stages:
            result = stage.run(context)
            self.results.append(result)

            # Propagate payload so later stages can read upstream output
            context[stage.name] = result.payload
            context.update(result.payload)

            if not result.success:
                print(f"  [STAGE FAILED] {result.name}: {result.error}")

        self._print_summary()
        return self.results

    # ------------------------------------------------------------------
    # Reporting
    # ------------------------------------------------------------------
    def _print_summary(self) -> None:
        print()
        print("=" * 55)
        print("  PIPELINE SUMMARY")
        print("=" * 55)
        for r in self.results:
            print(f"  {r}")
        total = sum(r.duration_sec for r in self.results)
        ok = sum(1 for r in self.results if r.success)
        print("─" * 55)
        print(f"  {ok}/{len(self.results)} stages OK   total {total:.2f}s")
        print("=" * 55)
