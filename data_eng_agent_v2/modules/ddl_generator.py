"""
DDL Generator — Standalone (multi-platform)
===========================================

Generates `CREATE TABLE` (+ optional PK/FK `ALTER TABLE`) DDL scripts
for every target table found in the canonical STTM JSON, in the SQL
dialect of the selected Data Platform (Databricks / Snowflake /
Microsoft Fabric / Google BigQuery).

This module is **additive** — it does not touch any of the existing
SCD-1 / SCD-2 / FACT / config / notebook generators. It is wired into
the orchestrator as a new `DdlGenerationStage` that runs immediately
after the STTM filter step.

Reference implementation: `LangGraphAgenticPipeline/pipeline/nodes/`
(`prepare_ddl.py` + `generate_ddl.py`). Logic ported here and adapted
to this project's conventions:

    • single-return `convert_with_llm(prompt, model_name=...)`
    • plain dict-based progress reporting (no LangGraph state object)
    • output dir + platform passed in (no global state)

Usage:
    from modules.ddl_generator import run_all_ddls

    run_all_ddls(
        input_path="output_static/erwin_full_mapping.json",
        output_dir="output/ddl/databricks",
        platform="Databricks",
        sql_dialect="SparkSQL",
    )
"""

from __future__ import annotations

import json
import os
import re
import sys
from typing import Any, Dict, List, Optional

import config_loader
from modules.openai_call import convert_with_llm
from modules.ddl_constants import (
    DATA_TYPE_MAP,
    resolve_platform,
    resolve_dialect,
)
from modules.prompts.ddl_prompt import build_ddl_prompt


# ============================================================
# Small utilities
# ============================================================

def _safe_int(value: Any, default: int = 9999) -> int:
    """Tolerant int parse — used to sort columns by Column_Order."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def clean_llm_output(output: str) -> str:
    """
    Strip markdown code fences from the LLM response, then standardise
    `CREATE TABLE` / `ALTER TABLE` to bare table names — no
    catalog/schema/database prefixes (e.g. ``main.default.dim_policy``
    → ``dim_policy``). Per UX spec: every DDL is displayed in the
    consistent form ``CREATE TABLE <table_name> (...)`` regardless of
    what the LLM emits.
    """
    if not output:
        return ""

    text = output
    if "```" in text:
        parts = text.split("```")
        if len(parts) >= 3:
            block = parts[1]
            for lang in ("sql", "SQL", "Sql"):
                if block.startswith(lang):
                    block = block[len(lang):]
                    break
            text = block
    text = text.strip()

    # Defensive: strip any backtick/double-quote identifier quoting the LLM
    # may still emit (e.g. `is sms`). With source identifiers already
    # normalised to snake_case there is nothing that needs quoting, so the
    # delimiters can be removed outright for consistent, clean DDL.
    text = text.replace("`", "").replace('"', "")

    return _strip_qualified_table_names(text)


def _strip_qualified_table_names(sql_text: str) -> str:
    """
    Rewrite ``CREATE TABLE foo.bar.baz`` → ``CREATE TABLE baz`` and
    ``ALTER TABLE x.y.z`` → ``ALTER TABLE z`` so every DDL displayed
    in the UI uses a single consistent ``<table_name>`` token.

    Also normalises references inside ``REFERENCES <qualified>`` so FK
    statements match.
    """
    import re

    def _last_segment(m: "re.Match[str]") -> str:
        head = m.group(1)              # CREATE TABLE / ALTER TABLE / REFERENCES
        sep = m.group(2) or " "        # original whitespace between keyword and name
        qualified = m.group(3)         # e.g. main.default.dim_policy
        bare = qualified.split(".")[-1]
        return f"{head}{sep}{bare}"

    # Use IGNORECASE; allow optional IF NOT EXISTS between keyword and name.
    pattern = re.compile(
        r"\b(CREATE\s+TABLE(?:\s+IF\s+NOT\s+EXISTS)?|ALTER\s+TABLE|REFERENCES)"
        r"(\s+)"
        r"([A-Za-z_][A-Za-z0-9_.`\"]*)",
        flags=re.IGNORECASE,
    )
    return pattern.sub(_last_segment, sql_text)


# ============================================================
# STTM (PascalCase) → DDL-ready JSON (LangGraph format)
# ============================================================

def _yes(v: Any) -> bool:
    return str(v or "").strip().lower() in ("yes", "y", "true", "1")


def _norm_identifier(value: Any) -> str:
    """
    Normalise an STTM identifier to clean snake_case so the DDL never
    needs backticks/quoting:
      - lowercase
      - non-alphanumeric runs (spaces, hyphens, slashes, dots, ...) -> '_'
      - collapse duplicate underscores, strip leading/trailing '_'
    e.g. "Is SMS" -> "is_sms", "Insured Object Sub-Type" -> "insured_object_sub_type"
    Mirrors `_format_column_name` used by the config/stage-SQL generators
    so column naming is consistent across DDL and configs.
    """
    s = str(value or "").strip().lower()
    s = re.sub(r"[^a-z0-9]+", "_", s)
    s = re.sub(r"_+", "_", s)
    return s.strip("_")


def transform_to_ddl_ready(sttm_table: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert a single PascalCase STTM table record into the DDL-ready
    JSON shape expected by the prompt template:

        {
          "table_name": "<lower>",
          "columns": [
            {"name": "...", "type": "...", "pk": <bool>},
            ...
          ],
          "foreign_keys": [
            {"column": "...", "references_table": "...",
             "references_column": "..."},
            ...
          ]
        }

    Ported from `prepare_ddl_node()` in
    `LangGraphAgenticPipeline/pipeline/nodes/prepare_ddl.py`.
    """
    table_name = _norm_identifier(sttm_table.get("Target_Table"))
    columns_raw = sttm_table.get("Column_Mappings") or []

    columns_sorted = sorted(
        columns_raw,
        key=lambda c: _safe_int((c or {}).get("Column_Order")),
    )

    transformed_columns: List[Dict[str, Any]] = []
    foreign_keys: List[Dict[str, str]] = []

    for col in columns_sorted:
        col = col or {}
        col_name = _norm_identifier(col.get("Target_Column"))
        if not col_name:
            continue

        raw_dtype = col.get("Data_Type")
        data_type = (
            str(raw_dtype).strip().upper() if raw_dtype else "STRING"
        )
        data_type = DATA_TYPE_MAP.get(data_type, data_type)

        pk_flag = _yes(col.get("Is_PK"))
        fk_flag = _yes(col.get("Is_FK"))

        transformed_columns.append(
            {"name": col_name, "type": data_type, "pk": pk_flag}
        )

        if fk_flag:
            src = col.get("SourceMapping") or {}
            ref_table = src.get("Source_Table")
            ref_column = src.get("Source_Column")
            if ref_table and ref_column:
                foreign_keys.append(
                    {
                        "column": col_name,
                        "references_table": _norm_identifier(ref_table),
                        "references_column": _norm_identifier(ref_column),
                    }
                )

    return {
        "table_name": table_name,
        "columns": transformed_columns,
        "foreign_keys": foreign_keys,
    }


# ============================================================
# Single-table DDL generation
# ============================================================

def generate_ddl_for_table(
    ddl_ready_table: Dict[str, Any],
    platform: str,
    sql_dialect: str,
    model_name: str = "openai",
) -> Optional[str]:
    """
    Build the prompt for one DDL-ready table, call the LLM, and return
    the cleaned DDL text. Returns ``None`` if the call failed.
    """
    prompt = build_ddl_prompt(
        input_json=json.dumps(ddl_ready_table, indent=2),
        platform_name=platform,
        sql_dialect=sql_dialect,
    )

    raw = convert_with_llm(prompt, model_name=model_name)
    if not raw or str(raw).strip().upper() == "NA":
        return None

    return clean_llm_output(raw)


# ============================================================
# Batch runner
# ============================================================

def _load_sttm_json(input_path: str) -> List[Dict[str, Any]]:
    """
    Load the canonical STTM JSON produced by `XmlToJsonStage`. Accepts
    either a top-level list or a `{...: [...]}` wrapper for safety.
    """
    if not os.path.exists(input_path):
        print(f"ERROR: Input STTM JSON not found: {input_path}")
        sys.exit(1)

    with open(input_path, "r", encoding="utf-8") as fp:
        raw = json.load(fp)

    if isinstance(raw, list):
        return raw
    if isinstance(raw, dict):
        for k in ("tables", "Tables", "sttm", "STTM", "data", "Data"):
            if k in raw and isinstance(raw[k], list):
                return raw[k]
        return [raw]

    print(f"ERROR: Unexpected JSON root type: {type(raw).__name__}")
    sys.exit(1)


def run_all_ddls(
    input_path: str,
    output_dir: str,
    platform: str = "Databricks",
    sql_dialect: Optional[str] = None,
    model_name: str = "openai",
) -> Dict[str, Any]:
    """
    Generate per-table DDL `.sql` files for every target table found in
    the canonical STTM JSON.

    Parameters
    ----------
    input_path : str
        Path to the canonical STTM JSON (output of `XmlToJsonStage`).
    output_dir : str
        Directory where `<table>.sql` files will be written. Created
        if missing.
    platform : str
        One of "Databricks", "Snowflake", "Microsoft Fabric",
        "Google BigQuery". Unknown values fall back to Databricks
        (preserving historical default).
    sql_dialect : str, optional
        Override dialect; when None, the platform's default dialect
        is used (Databricks→SparkSQL, Snowflake→SnowflakeSQL, …).
    model_name : str
        Which LLM backend in `modules.openai_call.convert_with_llm`
        to use ("openai" by default).

    Returns
    -------
    dict
        Result envelope compatible with the other stages' result dicts.
    """
    platform, platform_cfg = resolve_platform(platform)
    sql_dialect = resolve_dialect(platform, sql_dialect)

    raw_tables = _load_sttm_json(input_path)
    ddl_ready = [
        transform_to_ddl_ready(t) for t in raw_tables
        if t and (t.get("Target_Table") or "").strip()
    ]

    if not ddl_ready:
        print("  No target tables found in STTM JSON — nothing to generate.")
        return {
            "success_count": 0,
            "failed_count": 0,
            "total_count": 0,
            "platform": platform,
            "sql_dialect": sql_dialect,
            "output_dir": output_dir,
            "output_files": [],
            "failed_tables": [],
        }

    os.makedirs(output_dir, exist_ok=True)
    total = len(ddl_ready)

    print(f"  Platform : {platform}")
    print(f"  Dialect  : {sql_dialect}")
    print(f"  Tables   : {total}")
    print(f"  Output   : {os.path.abspath(output_dir)}")
    print()

    output_files: List[str] = []
    failed_tables: List[Dict[str, str]] = []

    for idx, table in enumerate(ddl_ready, start=1):
        table_name = table["table_name"] or f"table_{idx}"
        progress = f"[{idx}/{total}]"
        print(f"  {progress} Generating DDL for: {table_name}")

        try:
            ddl_text = generate_ddl_for_table(
                ddl_ready_table=table,
                platform=platform,
                sql_dialect=sql_dialect,
                model_name=model_name,
            )

            if not ddl_text:
                failed_tables.append(
                    {"table": table_name, "error": "LLM returned NA / empty"}
                )
                print(f"    ✗ LLM returned NA for: {table_name}")
                continue

            file_name = f"{table_name}.sql"
            file_path = os.path.join(output_dir, file_name)
            with open(file_path, "w", encoding="utf-8") as fp:
                fp.write(ddl_text.rstrip() + "\n")

            output_files.append(file_path)
            print(f"    ✓ Written: {file_path}")

        except Exception as e:  # pragma: no cover - defensive
            error_msg = f"{type(e).__name__}: {e}"
            print(f"    ✗ FAILED: {table_name} - {error_msg}")
            failed_tables.append({"table": table_name, "error": error_msg})

    success = len(output_files)
    failed = len(failed_tables)

    print()
    print("=" * 55)
    print(
        f"  DDL COMPLETE: {success}/{total} succeeded, {failed} failed"
        f"  ({platform} / {sql_dialect})"
    )
    print("=" * 55)

    return {
        "success_count": success,
        "failed_count": failed,
        "total_count": total,
        "platform": platform,
        "sql_dialect": sql_dialect,
        "output_dir": output_dir,
        "output_files": output_files,
        "failed_tables": failed_tables,
    }


# ============================================================
# CLI entry point — handy for ad-hoc runs / future Streamlit hookup
# ============================================================

if __name__ == "__main__":
    input_file = (
        sys.argv[1]
        if len(sys.argv) > 1
        else config_loader.get(
            "io.output_json_file",
            "output/sttm/Enhanced Customer360 Data Model Repository.json",
        )
    )
    output_directory = (
        sys.argv[2]
        if len(sys.argv) > 2
        else config_loader.get("directories.ddl_output_dir", "output/ddl")
    )
    platform_arg = (
        sys.argv[3]
        if len(sys.argv) > 3
        else config_loader.get("generation.data_platform", "Databricks")
    )
    dialect_arg = (
        sys.argv[4]
        if len(sys.argv) > 4
        else config_loader.get("generation.sql_dialect")
    )

    print("=" * 55)
    print("  DDL Generator — Multi-platform")
    print(f"  Input    : {input_file}")
    print(f"  Output   : {output_directory}")
    print(f"  Platform : {platform_arg}")
    print(f"  Dialect  : {dialect_arg or '(platform default)'}")
    print("=" * 55)
    print()

    result = run_all_ddls(
        input_path=input_file,
        output_dir=output_directory,
        platform=platform_arg,
        sql_dialect=dialect_arg,
    )

    sys.exit(0 if result["failed_count"] == 0 else 1)
