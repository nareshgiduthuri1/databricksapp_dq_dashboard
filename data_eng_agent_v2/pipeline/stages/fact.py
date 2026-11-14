"""
Stage 4 — Generate FACT-table configs.

Wraps `fact_generator.run_all_fact`, the unified FACT generator. The SAME
generator emits the same config structure for every data platform; only
the LLM prompt's dialect varies. No platform branching here.
"""

from __future__ import annotations

from typing import Any, Dict

from pipeline.base import PipelineStage
from modules.fact_generator import run_all_fact as _run_all_fact


class FactConfigStage(PipelineStage):
    """
    Calls the unified FACT config generator over the FACT JSON slice,
    passing the configured platform + SQL dialect through to the prompt.
    """

    def __init__(self, config):
        super().__init__(config, name="STEP 4 — FACT Config Generator")

    def _run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        cfg = self.config
        platform = getattr(cfg, "data_platform", "Databricks") or "Databricks"
        print(f"  Input:    {cfg.fact_json_file}")
        print(f"  Output:   {cfg.config_output_dir}")
        print(f"  Platform: {platform}")
        print()

        result = _run_all_fact(
            cfg.fact_json_file,
            cfg.config_output_dir,
            model_name=getattr(cfg, "model_name", "openai"),
            platform=platform,
            sql_dialect=getattr(cfg, "sql_dialect", None),
        )

        if result["failed_count"] > 0:
            print("FACT Config Generation Failed")
        else:
            print("FACT Config Generation Completed")

        return {"fact_result": result}
