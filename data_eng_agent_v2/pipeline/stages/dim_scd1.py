"""
Stage 5 — Generate SCD-1 dimension configs.

Wraps `dim_scd1_generator.run_all_dim_scd1`, the unified SCD-1 generator.
The SAME generator emits `<table>_scd1_load.py` for every data platform;
only the LLM prompt's dialect varies. No platform branching here.
"""

from __future__ import annotations

from typing import Any, Dict

from pipeline.base import PipelineStage
from modules.dim_scd1_generator import run_all_dim_scd1 as _run_all_dim_scd1


class DimSCD1ConfigStage(PipelineStage):
    """
    Calls the unified SCD-1 DIM generator over the SCD1 JSON slice,
    passing the configured platform + SQL dialect through to the prompt.
    """

    def __init__(self, config):
        super().__init__(config, name="STEP 5 — DIM SCD1 Config Generator")

    def _run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        cfg = self.config
        platform = getattr(cfg, "data_platform", "Databricks") or "Databricks"
        print(f"  Input:    {cfg.scd1_json_file}")
        print(f"  Output:   {cfg.config_output_dir}")
        print(f"  Platform: {platform}")
        print()

        result = _run_all_dim_scd1(
            cfg.scd1_json_file,
            cfg.config_output_dir,
            model_name=getattr(cfg, "model_name", "openai"),
            platform=platform,
            sql_dialect=getattr(cfg, "sql_dialect", None),
        )

        if result["failed_count"] > 0:
            print("DIM SCD1 Config Generation Failed")
        else:
            print("DIM SCD1 Config Generation Completed")

        return {"dim_scd1_result": result}
