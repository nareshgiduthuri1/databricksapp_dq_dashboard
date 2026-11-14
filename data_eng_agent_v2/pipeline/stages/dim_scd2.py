"""
Stage 3 — Generate SCD-2 dimension configs.

Wraps `dim_scd2_generator.run_all`, the unified SCD-2 DIM generator.
The SAME generator produces the same config structure for every data
platform (Databricks / Snowflake / Microsoft Fabric / Google BigQuery);
only the LLM prompt's dialect varies. No platform branching here.
"""

from __future__ import annotations

from typing import Any, Dict

from pipeline.base import PipelineStage
from modules.dim_scd2_generator import run_all as _run_all_dim_scd2


class DimSCD2ConfigStage(PipelineStage):
    """
    Calls the unified SCD-2 DIM config generator over the SCD2 JSON slice,
    passing the configured platform + SQL dialect through to the prompt.
    """

    def __init__(self, config):
        super().__init__(config, name="STEP 3 — DIM SCD2 Config Generator")

    def _run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        cfg = self.config
        platform = getattr(cfg, "data_platform", "Databricks") or "Databricks"
        print(f"  Input:    {cfg.scd2_json_file}")
        print(f"  Output:   {cfg.config_output_dir}")
        print(f"  Platform: {platform}")
        print()

        result = _run_all_dim_scd2(
            cfg.scd2_json_file,
            cfg.config_output_dir,
            model_name=getattr(cfg, "model_name", "openai"),
            platform=platform,
            sql_dialect=getattr(cfg, "sql_dialect", None),
        )

        if result["failed_count"] > 0:
            print("DIM SCD2 Config Generation Failed")
        else:
            print("DIM SCD2 Config Generation Completed")

        return {"dim_scd2_result": result}
