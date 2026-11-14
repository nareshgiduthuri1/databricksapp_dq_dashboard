"""
Stage 2.5 — DDL Generation (multi-platform)
===========================================

Generates per-table `CREATE TABLE` (+ PK/FK ALTER) scripts for every
target table found in the canonical STTM JSON, in the SQL dialect of
the Data Platform selected on :class:`PipelineConfig`.

This stage is wired into the orchestrator immediately AFTER
:class:`SttmFilterStage` (so the STTM JSON is fully materialised) and
BEFORE the existing SCD-2 / FACT / SCD-1 config generators — none of
which it touches. It can be turned off via
``PipelineConfig.enable_ddl_generation = False`` to preserve byte-
identical behaviour with the pre-DDL pipeline.

Reference: `LangGraphAgenticPipeline/pipeline/nodes/generate_ddl.py`.
"""

from __future__ import annotations

from typing import Any, Dict

from pipeline.base import PipelineStage
from modules.ddl_generator import run_all_ddls as _run_all_ddls


class DdlGenerationStage(PipelineStage):
    """
    Calls the multi-platform DDL generator over the canonical STTM JSON.

    Reads the platform / dialect / output-dir directly from
    :class:`PipelineConfig` so the future Streamlit UI only needs to
    push user selections into the config object — no other rewiring is
    required.
    """

    def __init__(self, config):
        super().__init__(config, name="STEP 2.5 — DDL Generator")

    # ------------------------------------------------------------------
    # Stage body
    # ------------------------------------------------------------------
    def _run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        cfg = self.config

        # Optional kill-switch — keeps the original pipeline byte-
        # identical when DDL generation is intentionally disabled.
        if not getattr(cfg, "enable_ddl_generation", True):
            print("  DDL generation disabled via config — skipping.")
            return {"ddl_result": {"skipped": True}}

        platform = getattr(cfg, "data_platform", "Databricks")
        sql_dialect = getattr(cfg, "sql_dialect", None)
        ddl_dir = getattr(cfg, "ddl_output_dir", "output/ddl/")

        print(f"  Input:    {cfg.output_json_file}")
        print(f"  Output:   {ddl_dir}")
        print(f"  Platform: {platform}")
        print(f"  Dialect:  {sql_dialect or '(platform default)'}")
        print()

        result = _run_all_ddls(
            input_path=cfg.output_json_file,
            output_dir=ddl_dir,
            platform=platform,
            sql_dialect=sql_dialect,
            model_name=getattr(cfg, "model_name", "openai"),
        )

        if result.get("failed_count", 0) > 0:
            print("DDL Generation completed with failures")
        else:
            print("DDL Generation Completed")

        return {"ddl_result": result}
