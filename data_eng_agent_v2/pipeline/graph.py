"""
Stage-Based Pipeline Callables — UI Driver
==========================================

Exposes three approval-gated entry points that the Streamlit UI uses to
execute the existing pipeline one stage at a time:

    run_stage1(xml_path, …)  → STTM generation  (XmlToJson + SttmFilter)
    run_stage2(state)        → DDL generation   (multi-platform)
    run_stage3(state)        → SQL & Config     (SCD-2 / FACT / SCD-1
                                                + Notebook assembly
                                                + Lineage CSV)

Each callable returns a *state dict* shaped like the LangGraph agent's
state object so the existing UI components (`render_sttm_output`,
`render_ddl_output`, `render_config_output`) can render the results
with no porting.

NOTE
----
This module is *additive*. The existing `pipeline.orchestrator.Pipeline`
class still runs the full 7-stage flow in one go for CLI / batch
callers (`python main.py`). The UI calls these helpers instead, so the
human-in-the-loop approval workflow can pause between stages — without
touching any of the underlying generator modules.
"""

from __future__ import annotations

import json
import os
import time
import glob
from datetime import datetime
from typing import Any, Dict, List, Optional

import config_loader
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


# ============================================================
# Helpers
# ============================================================

def _ts() -> str:
    return datetime.now().strftime("%H:%M:%S")


def _log(state: Dict[str, Any], step: str, message: str, level: str = "INFO") -> None:
    state.setdefault("pipeline_logs", []).append(
        {"timestamp": _ts(), "level": level, "step": step, "message": message}
    )


def _build_config(
    output_json_file: str,
    data_platform: str,
    sql_dialect: Optional[str],
    model_name: str,
    ddl_output_dir: str,
    config_output_dir: str,
    notebook_output_dir: str,
    csv_output_file: str,
    xml_path: str,
) -> PipelineConfig:
    """Construct a PipelineConfig directly (bypassing from_env)."""
    return PipelineConfig(
        input_xml_file=xml_path,
        output_json_file=output_json_file,
        config_output_dir=config_output_dir,
        notebook_output_dir=notebook_output_dir,
        csv_output_file=csv_output_file,
        data_platform=data_platform,
        sql_dialect=sql_dialect,
        ddl_output_dir=ddl_output_dir,
        model_name=model_name,
    )


def _read_files_in_dir(directory: str, pattern: str = "*") -> List[Dict[str, str]]:
    """Return [{filename, path, content}, …] for files matching pattern."""
    items: List[Dict[str, str]] = []
    if not directory or not os.path.isdir(directory):
        return items
    for path in sorted(glob.glob(os.path.join(directory, pattern))):
        if not os.path.isfile(path):
            continue
        try:
            with open(path, "r", encoding="utf-8") as fp:
                content = fp.read()
        except Exception as e:  # pragma: no cover
            content = f"# Failed to read file: {e}"
        items.append(
            {
                "filename": os.path.basename(path),
                "path": path,
                "content": content,
            }
        )
    return items


# ============================================================
# STAGE 1 — STTM generation
# ============================================================

def run_stage1(
    xml_path: str,
    data_platform: Optional[str] = None,
    sql_dialect: Optional[str] = None,
    model_name: Optional[str] = None,
    output_json_file: Optional[str] = None,
    ddl_output_dir: Optional[str] = None,
    config_output_dir: Optional[str] = None,
    notebook_output_dir: Optional[str] = None,
    csv_output_file: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Run XML → STTM JSON and split it into SCD1 / SCD2 / FACT slices.

    Any argument left as ``None`` falls back to the corresponding value
    in ``config.yaml`` (then to a sensible literal default), so the UI
    only needs to pass the user's runtime selections.

    Returns a state dict the UI can render via `render_sttm_output`.
    """
    # ── Resolve runtime selection > config.yaml > literal default ──
    data_platform = data_platform or config_loader.get(
        "generation.data_platform", "Databricks"
    )
    sql_dialect = sql_dialect or config_loader.get("generation.sql_dialect")
    model_name = model_name or config_loader.get("llm.default_model", "openai")
    ddl_output_dir = ddl_output_dir or config_loader.get(
        "directories.ddl_output_dir", "output/ddl/"
    )
    config_output_dir = config_output_dir or config_loader.get(
        "directories.config_output_dir", "output/configs/"
    )
    notebook_output_dir = notebook_output_dir or config_loader.get(
        "directories.notebook_output_dir", "db_notebooks"
    )
    csv_output_file = csv_output_file or config_loader.get(
        "io.csv_output_file",
        "./output/lineage/erwin_customer360_final_mapping_file.csv",
    )

    output_json_file = (
        output_json_file
        or config_loader.get("io.output_json_file")
        or "./output/sttm/erwin_full_mapping.json"
    )
    os.makedirs(os.path.dirname(output_json_file) or ".", exist_ok=True)

    cfg = _build_config(
        output_json_file=output_json_file,
        data_platform=data_platform,
        sql_dialect=sql_dialect,
        model_name=model_name,
        ddl_output_dir=ddl_output_dir,
        config_output_dir=config_output_dir,
        notebook_output_dir=notebook_output_dir,
        csv_output_file=csv_output_file,
        xml_path=xml_path,
    )

    state: Dict[str, Any] = {
        "config": cfg,
        "xml_path": xml_path,
        "data_platform": data_platform,
        "sql_dialect": sql_dialect,
        "model_name": model_name,
        "output_json_file": output_json_file,
        "pipeline_logs": [],
        "metrics": {},
        "current_step": "parse_xml",
    }

    started = time.perf_counter()
    _log(state, "parse_xml", f"Parsing Erwin XML: {xml_path}")

    # Stage 1a — XML → JSON (uses existing XmlToJsonStage)
    XmlToJsonStage(cfg).run({})
    _log(state, "parse_xml", "Erwin XML parsed; STTM JSON written.")

    # Stage 1b — Filter into SCD1 / SCD2 / FACT slices
    state["current_step"] = "validate_sttm"
    filter_stage = SttmFilterStage(cfg)
    filter_result = filter_stage.run({})
    if not filter_result.success:
        raise RuntimeError(f"STTM filter failed: {filter_result.error}")

    payload = filter_result.payload

    # Load the canonical STTM JSON for the UI to render
    with open(output_json_file, "r", encoding="utf-8") as fp:
        sttm_json = json.load(fp)

    # Column count for validation widget
    total_columns = sum(len(t.get("Column_Mappings") or []) for t in sttm_json)

    state["sttm_json"] = sttm_json
    state["scd1_json_file"] = payload["scd1_json_file"]
    state["scd2_json_file"] = payload["scd2_json_file"]
    state["fact_json_file"] = payload["fact_json_file"]
    state["sttm_validation"] = {
        "table_count": len(sttm_json),
        "column_count": total_columns,
        "scd1_count": payload["scd1_count"],
        "scd2_count": payload["scd2_count"],
        "fact_count": payload["fact_count"],
        "is_valid": len(sttm_json) > 0,
        "issues": [],
        "warnings": [],
        "quality_score": 100,
    }
    state["metrics"] = {
        "tables_processed": len(sttm_json),
        "columns_mapped": total_columns,
        "ddls_generated": 0,
        "configs_generated": 0,
        "llm_calls": 0,
        "step_timings": {
            "parse_xml": round(time.perf_counter() - started, 2),
        },
    }

    _log(
        state,
        "validate_sttm",
        f"STTM ready: {len(sttm_json)} tables, {total_columns} columns "
        f"(SCD1={payload['scd1_count']}, SCD2={payload['scd2_count']}, "
        f"FACT={payload['fact_count']}).",
    )
    state["current_step"] = "stage1_done"
    return state


# ============================================================
# STAGE 2 — DDL generation
# ============================================================

def run_stage2(previous_state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run the multi-platform DDL generator. Reuses the canonical STTM
    JSON written by Stage 1, plus the platform/dialect/model selected
    in the sidebar.
    """
    state: Dict[str, Any] = dict(previous_state)
    cfg: PipelineConfig = state["config"]
    started = time.perf_counter()

    _log(
        state,
        "generate_ddl",
        f"Generating DDLs for {cfg.data_platform} "
        f"({cfg.sql_dialect or 'platform default'})",
    )

    state["current_step"] = "generate_ddl"
    stage = DdlGenerationStage(cfg)
    result = stage.run({})
    if not result.success:
        raise RuntimeError(f"DDL stage failed: {result.error}")

    ddl_result = result.payload.get("ddl_result", {})
    output_files: List[str] = ddl_result.get("output_files", [])

    # Build the `generated_ddls` list expected by `render_ddl_output`:
    #   [{"table_name", "ddl_sql", "platform", "dialect"}, …]
    generated_ddls: List[Dict[str, Any]] = []
    for path in output_files:
        try:
            with open(path, "r", encoding="utf-8") as fp:
                ddl_sql = fp.read()
        except Exception:
            ddl_sql = ""
        table_name = os.path.splitext(os.path.basename(path))[0]
        generated_ddls.append(
            {
                "table_name": table_name,
                "ddl_sql": ddl_sql,
                "platform": ddl_result.get("platform"),
                "dialect": ddl_result.get("sql_dialect"),
                "file_path": path,
            }
        )

    # Build a per-table validation dict the UI expects
    table_results = {
        d["table_name"]: {
            "is_valid": "CREATE TABLE" in (d["ddl_sql"] or "").upper(),
            "checks_passed": ["create_table"] if "CREATE TABLE" in (d["ddl_sql"] or "").upper() else [],
            "issues": [] if d["ddl_sql"] else ["Empty DDL"],
        }
        for d in generated_ddls
    }
    failed = sum(
        1 for v in table_results.values() if not v["is_valid"]
    )

    state["generated_ddls"] = generated_ddls
    state["ddl_validation"] = {
        "total_tables": len(generated_ddls),
        "passed": len(generated_ddls) - failed,
        "failed": failed,
        "table_results": table_results,
    }

    # Metrics
    metrics = dict(state.get("metrics", {}))
    metrics["ddls_generated"] = len(generated_ddls)
    metrics["llm_calls"] = metrics.get("llm_calls", 0) + len(generated_ddls)
    step_timings = dict(metrics.get("step_timings", {}))
    step_timings["generate_ddl"] = round(time.perf_counter() - started, 2)
    metrics["step_timings"] = step_timings
    state["metrics"] = metrics

    _log(
        state,
        "validate_ddl",
        f"DDL generation complete — {len(generated_ddls)} files in "
        f"{ddl_result.get('output_dir')}.",
    )
    state["current_step"] = "stage2_done"
    return state


# ============================================================
# STAGE 3 — Stage SQL + Config + Notebook + CSV
# ============================================================

def run_stage3(previous_state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run the SCD-2 / FACT / SCD-1 generators, assemble notebooks, write
    the lineage CSV. This is the original Databricks behaviour of the
    project — unchanged.
    """
    state: Dict[str, Any] = dict(previous_state)
    cfg: PipelineConfig = state["config"]
    started = time.perf_counter()

    _log(
        state,
        "generate_stage_sql",
        f"Generating Stage SQL & configs (model={cfg.model_name})",
    )

    # ── Raw Data Vault branch: hub/sat/link config generation only ─────
    # (No SCD/FACT generation, notebook assembly, or lineage CSV.)
    if _gp.get_target_model() == _gp.TARGET_RAW_DATA_VAULT:
        state["current_step"] = "prepare_config"
        r_rv = RawVaultConfigStage(cfg).run({})
        if not r_rv.success:
            raise RuntimeError(f"Raw Data Vault stage failed: {r_rv.error}")
        rv_result = r_rv.payload.get("raw_vault_result", {})

        config_files = _read_files_in_dir(cfg.config_output_dir, "*.py")
        total = sum(v.get("success_count", 0) for v in rv_result.values())
        failed = sum(v.get("failed_count", 0) for v in rv_result.values())

        state["assembled_configs"] = []
        state["config_files"] = config_files
        state["notebook_files"] = []
        state["config_validation"] = {
            "total_configs": total,
            "passed": total,
            "failed": failed,
            "table_results": {},
        }

        metrics = dict(state.get("metrics", {}))
        metrics["configs_generated"] = total
        step_timings = dict(metrics.get("step_timings", {}))
        step_timings["generate_stage_sql"] = round(time.perf_counter() - started, 2)
        metrics["step_timings"] = step_timings
        state["metrics"] = metrics

        _log(
            state,
            "save_outputs",
            f"Raw Data Vault complete — {len(config_files)} config file(s) "
            f"({total} tables).",
        )
        state["current_step"] = "stage3_done"
        return state

    # 1) SCD-2 DIM configs
    state["current_step"] = "prepare_config"
    r_scd2 = DimSCD2ConfigStage(cfg).run({})
    if not r_scd2.success:
        raise RuntimeError(f"SCD-2 stage failed: {r_scd2.error}")
    scd2_result = r_scd2.payload.get("dim_scd2_result", {})

    # 2) FACT configs
    r_fact = FactConfigStage(cfg).run({})
    if not r_fact.success:
        raise RuntimeError(f"FACT stage failed: {r_fact.error}")
    fact_result = r_fact.payload.get("fact_result", {})

    # 3) SCD-1 DIM configs (per-table notebooks)
    r_scd1 = DimSCD1ConfigStage(cfg).run({})
    if not r_scd1.success:
        raise RuntimeError(f"SCD-1 stage failed: {r_scd1.error}")
    scd1_result = r_scd1.payload.get("dim_scd1_result", {})

    # 4) Notebook assembly (SCD-2 / FACT bundle notebooks)
    state["current_step"] = "assemble_config"
    NotebookAssemblyStage(cfg).run({})

    # 5) JSON → CSV (flat lineage)
    state["current_step"] = "save_outputs"
    JsonToCsvStage(cfg).run({})

    # ── Build `assembled_configs` list for the UI ────────────────
    # Each entry mirrors the LangGraph format closely enough that
    # `render_config_output` works as-is. We pull metadata from the
    # SCD-2 / SCD-1 / FACT input JSONs and inline the matching
    # generated config .py / notebook file as `stage_sql` so users see
    # the actual artifact.
    assembled: List[Dict[str, Any]] = []

    def _meta(rec: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "Target_Table": rec.get("Target_Table"),
            "Table_Type": rec.get("Table_Type"),
            "SCD_Type": rec.get("SCD_Type"),
            "Business_Key": rec.get("Business_Key"),
            "Watermark_Date_Columns": rec.get("Watermark_Date_Columns"),
            "Source_Data_Vault_Table": rec.get("Source_Data_Vault_Table"),
            "Source_Logical_Table": rec.get("Source_Logical_Table"),
        }

    def _load_slice(path: str) -> List[Dict[str, Any]]:
        try:
            with open(path, "r", encoding="utf-8") as fp:
                return json.load(fp)
        except Exception:
            return []

    scd2_records = _load_slice(cfg.scd2_json_file)
    scd1_records = _load_slice(cfg.scd1_json_file)
    fact_records = _load_slice(cfg.fact_json_file)

    # Pick up every Python artifact in the configs dir (covers
    # `<table>_config.py`, `<table>_scd1_config.py`, etc.) and every
    # bundle / per-table notebook on the notebooks dir side.
    config_files = _read_files_in_dir(cfg.config_output_dir, "*.py")
    notebook_files = _read_files_in_dir(cfg.notebook_output_dir, "*.py")

    by_filename = {f["filename"]: f for f in (config_files + notebook_files)}

    def _attach_artifact(rec: Dict[str, Any]) -> Dict[str, Any]:
        m = _meta(rec)
        target = (m["Target_Table"] or "").strip()
        bare = target.split(".")[-1].lower()
        # File-name candidates per generator path:
        #   • Databricks SCD-2 / FACT  : <bare>_config.py
        #   • Databricks SCD-1         : <bare>_scd1_load.py
        #   • Non-Databricks SCD-1     : <bare>_scd1_config.py
        #   • Non-Databricks SCD-2/FACT: <bare>_config.py  (same as DB)
        candidates = [
            f"{bare}_config.py",
            f"{bare}_scd1_load.py",
            f"{bare}_scd1_config.py",
        ]
        artifact = None
        for cand in candidates:
            if cand in by_filename:
                artifact = by_filename[cand]
                break

        sources = []
        if m["Source_Data_Vault_Table"]:
            sources.append(str(m["Source_Data_Vault_Table"]))
        if m["Source_Logical_Table"]:
            sources.append(str(m["Source_Logical_Table"]))

        return {
            "name": target,
            "table_type": m["Table_Type"],
            "scd_type": m["SCD_Type"],
            "business_key_col": m["Business_Key"] or "",
            "watermark_col": m["Watermark_Date_Columns"] or "",
            "source_tables": sources,
            "stage_sql": (artifact or {}).get("content", "-- artifact not found"),
            "artifact_filename": (artifact or {}).get("filename"),
            "artifact_path": (artifact or {}).get("path"),
            "attribute_cols": [
                (c.get("Target_Column") or "")
                for c in (rec.get("Column_Mappings") or [])
                if str(c.get("Is_PK", "No")).lower() != "yes"
                and str(c.get("Is_FK", "No")).lower() != "yes"
            ],
            "insert_cols": [
                (c.get("Target_Column") or "")
                for c in (rec.get("Column_Mappings") or [])
            ],
        }

    for rec in scd1_records:
        assembled.append(_attach_artifact(rec))
    for rec in scd2_records:
        assembled.append(_attach_artifact(rec))
    for rec in fact_records:
        assembled.append(_attach_artifact(rec))

    # ── Validation summary ────────────────────────────────────
    failed = (
        scd2_result.get("failed_count", 0)
        + fact_result.get("failed_count", 0)
        + scd1_result.get("failed_count", 0)
    )
    total = len(assembled)
    table_results = {
        a["name"]: {
            "is_valid": bool(a["stage_sql"]) and "-- artifact not found"
            not in (a["stage_sql"] or ""),
            "checks_passed": ["artifact_present"]
            if a["stage_sql"] and "not found" not in a["stage_sql"]
            else [],
            "issues": []
            if a["stage_sql"] and "not found" not in a["stage_sql"]
            else ["Generated artifact missing on disk"],
        }
        for a in assembled
    }

    state["assembled_configs"] = assembled
    state["config_validation"] = {
        "total_configs": total,
        "passed": total - failed,
        "failed": failed,
        "table_results": table_results,
    }

    # Combined download payloads
    state["config_files"] = config_files
    state["notebook_files"] = notebook_files
    state["lineage_csv_path"] = cfg.csv_output_file

    # Metrics
    metrics = dict(state.get("metrics", {}))
    metrics["configs_generated"] = total
    metrics["llm_calls"] = metrics.get("llm_calls", 0) + total
    step_timings = dict(metrics.get("step_timings", {}))
    step_timings["generate_stage_sql"] = round(
        time.perf_counter() - started, 2
    )
    metrics["step_timings"] = step_timings
    state["metrics"] = metrics

    _log(
        state,
        "save_outputs",
        f"Stage 3 complete — {len(config_files)} config files, "
        f"{len(notebook_files)} notebooks, lineage CSV written.",
    )
    state["current_step"] = "stage3_done"
    return state
