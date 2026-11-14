"""
Stage — Generate Raw Data Vault configs (HUB / SAT / LINK).

Only used when the active target model is Raw Data Vault
(`type_of_conversion: "Bronze to Raw Vault"`). Runs the shared raw-vault
generator once per object type over the hub/sat/link slices produced by
SttmFilterStage, writing one bundled config file per type into the configs
output dir. The same generator emits the same config structure for every
data platform; only the LLM prompt's dialect varies.
"""

from __future__ import annotations

from typing import Any, Dict

from pipeline.base import PipelineStage
from modules.raw_vault_generator import run_all as _run_all_raw_vault


class RawVaultConfigStage(PipelineStage):
    """Generate hub_config.py / sat_config.py / link_config.py."""

    def __init__(self, config):
        super().__init__(config, name="STEP 3 — Raw Data Vault Config Generator")

    def _run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        cfg = self.config
        platform = getattr(cfg, "data_platform", "Databricks") or "Databricks"
        model_name = getattr(cfg, "model_name", "openai")
        sql_dialect = getattr(cfg, "sql_dialect", None)

        slices = [
            ("hub", cfg.hub_json_file),
            ("link", cfg.link_json_file),
            ("sat", cfg.sat_json_file),
        ]

        print(f"  Output:   {cfg.config_output_dir}")
        print(f"  Platform: {platform}")
        print()

        results: Dict[str, Any] = {}
        any_failed = False
        for object_type, slice_path in slices:
            print(f"  Input:    {slice_path}  ({object_type})")
            res = _run_all_raw_vault(
                slice_path,
                cfg.config_output_dir,
                object_type=object_type,
                model_name=model_name,
                platform=platform,
                sql_dialect=sql_dialect,
            )
            results[object_type] = res
            any_failed = any_failed or res.get("failed_count", 0) > 0

        if any_failed:
            print("Raw Data Vault Config Generation Completed (with failures)")
        else:
            print("Raw Data Vault Config Generation Completed")

        return {"raw_vault_result": results}
