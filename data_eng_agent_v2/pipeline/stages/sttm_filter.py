"""
Stage 2 — Filter the parsed STTM JSON into SCD1 / SCD2 / FACT buckets.

The filter logic is identical to the original `main.py` (no rule change).
The class adds: explicit loading, deterministic writing, and surfaces the
three intermediate paths into the pipeline context so downstream stages
do not have to re-read the file.
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List

from pipeline.base import PipelineStage
from modules import generation_profiles as _gp


class SttmFilterStage(PipelineStage):
    """Splits the canonical STTM JSON into SCD1, SCD2, and FACT slices.

    Routing is target-model aware:
      * Dimensional (default) — original logic: SCD2 slice is limited to
        SCD_Type==2 dimension tables; FACT slice is Table_Type==fact.
      * Business Vault — master tables (SCD_Type==2) go to the SCD2 slice
        and xref tables (SCD_Type==1) to the SCD1 slice, regardless of
        Table_Type (BV masters are not typed "dimension"); there are no
        FACT tables.
    """

    def __init__(self, config):
        super().__init__(config, name="STEP 2 — Filter STTM (SCD1/SCD2/FACT)")

    # ------------------------------------------------------------------
    # Filters — SCD-type routing (SCD1 is shared across target models)
    # ------------------------------------------------------------------
    @staticmethod
    def _scd1(records: List[dict]) -> List[dict]:
        return [r for r in records if str(r.get("SCD_Type")) == "1"]

    @staticmethod
    def _scd2_dim(records: List[dict]) -> List[dict]:
        return [
            r for r in records
            if str(r.get("SCD_Type")) == "2"
            and str(r.get("Table_Type")).lower() == "dimension"
        ]

    @staticmethod
    def _scd2_bv(records: List[dict]) -> List[dict]:
        # Business Vault: all SCD_Type==2 tables (master tables), without
        # the Dimensional "Table_Type == dimension" restriction.
        return [r for r in records if str(r.get("SCD_Type")) == "2"]

    @staticmethod
    def _fact(records: List[dict]) -> List[dict]:
        return [
            r for r in records
            if str(r.get("Table_Type")).lower() == "fact"
        ]

    # Raw Data Vault routing — split by Table_Type (Hub / Sat / Link).
    @staticmethod
    def _by_table_type(records: List[dict], *types: str) -> List[dict]:
        wanted = {t.lower() for t in types}
        return [
            r for r in records
            if str(r.get("Table_Type")).strip().lower() in wanted
        ]

    # ------------------------------------------------------------------
    # Stage body
    # ------------------------------------------------------------------
    def _run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        cfg = self.config

        with open(cfg.output_json_file, "r") as fp:
            sttm_json = json.load(fp)

        target_model = _gp.get_target_model()

        # ── Raw Data Vault: split into hub / sat / link slices ─────────
        if target_model == _gp.TARGET_RAW_DATA_VAULT:
            hub = self._by_table_type(sttm_json, "hub")
            sat = self._by_table_type(sttm_json, "sat", "satellite")
            link = self._by_table_type(sttm_json, "link")

            for path in (cfg.hub_json_file, cfg.sat_json_file, cfg.link_json_file):
                os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
            with open(cfg.hub_json_file, "w") as fp:
                json.dump(hub, fp, indent=4)
            with open(cfg.sat_json_file, "w") as fp:
                json.dump(sat, fp, indent=4)
            with open(cfg.link_json_file, "w") as fp:
                json.dump(link, fp, indent=4)

            print(f"  hub={len(hub)}  sat={len(sat)}  link={len(link)}")
            return {
                "hub_count": len(hub),
                "sat_count": len(sat),
                "link_count": len(link),
                "hub_json_file": cfg.hub_json_file,
                "sat_json_file": cfg.sat_json_file,
                "link_json_file": cfg.link_json_file,
            }

        scd1 = self._scd1(sttm_json)
        if target_model == _gp.TARGET_BUSINESS_VAULT:
            scd2 = self._scd2_bv(sttm_json)
            fact = []  # Business Vault has no FACT tables
        else:
            scd2 = self._scd2_dim(sttm_json)
            fact = self._fact(sttm_json)

        # Ensure destination directories (e.g. ./output/sttm/) exist.
        for path in (cfg.scd1_json_file, cfg.scd2_json_file, cfg.fact_json_file):
            os.makedirs(os.path.dirname(path) or ".", exist_ok=True)

        with open(cfg.scd1_json_file, "w") as fp:
            json.dump(scd1, fp, indent=4)
        with open(cfg.scd2_json_file, "w") as fp:
            json.dump(scd2, fp, indent=4)
        with open(cfg.fact_json_file, "w") as fp:
            json.dump(fact, fp, indent=4)

        print(
            f"  scd1={len(scd1)}  scd2-dim={len(scd2)}  fact={len(fact)}"
        )

        return {
            "scd1_count": len(scd1),
            "scd2_count": len(scd2),
            "fact_count": len(fact),
            "scd1_json_file": cfg.scd1_json_file,
            "scd2_json_file": cfg.scd2_json_file,
            "fact_json_file": cfg.fact_json_file,
        }
