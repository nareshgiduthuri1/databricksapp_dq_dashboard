"""
Config Generator — Standalone
Table Type: FACT

Reads input JSON, iterates over all FACT tables,
generates ETL config for each via OpenAI, writes output files.

Usage:
    python config_generator_fact.py
    python config_generator_fact.py input/data.json output/configs/
"""

import json
import re
import os
import sys

import config_loader
from modules.openai_call import convert_with_llm
from modules.prompts.fact_prompt import build_fact_stage_sql_prompt


DEFAULT_CONVERSION = "Data Vault to Dimensional"


def _get_conversion_type() -> str:
    """Read generation.type_of_conversion from config (DV default).

    Kept defensive so any config issue falls back to the original Data
    Vault behaviour and never breaks the existing pipeline.
    """
    try:
        val = config_loader.get(
            "generation.type_of_conversion", DEFAULT_CONVERSION
        )
        return val or DEFAULT_CONVERSION
    except Exception:
        return DEFAULT_CONVERSION


def _is_3nf(conversion_type: str) -> bool:
    return str(conversion_type or "").strip().lower().startswith("3nf")


# ============================================================
# Helpers
# ============================================================

def _is_real_value(v) -> bool:
    """True if value is not None and not the string 'null'/'none'/''."""
    if v is None:
        return False

    s = str(v).strip().lower()
    return s not in ("", "null", "none")


def _yes_no_to_bool(v) -> bool:
    """Convert 'Yes'/'No'/'Y'/'N'/True/False/None to bool."""
    if v is None:
        return False

    if isinstance(v, bool):
        return v

    s = str(v).strip().lower()
    return s in ("yes", "y", "true", "1")


def _format_name(value: str) -> str:
    """
    Convert values into snake_case format:
    - lowercase
    - replace spaces/special chars with _
    - remove duplicate underscores
    - trim leading/trailing underscores
    """
    if value is None:
        return None

    value = str(value).strip().lower()

    # Replace non-alphanumeric characters with underscore
    value = re.sub(r"[^a-z0-9]+", "_", value)

    # Remove consecutive underscores
    value = re.sub(r"_+", "_", value)

    return value.strip("_")


def derive_increment_keys(
    target_table_name: str,
    columns: list,
    conversion_type: str = DEFAULT_CONVERSION,
) -> list:
    """
    Derive increment_keys for a FACT table from STTM column mappings.

    The Tier-1 rule depends on the source model (`conversion_type`):

      Data Vault to Dimensional (default):
        - Tier 1: match the column whose source_table == 'HUB_<grain>'
          and use its target_column.

      3NF to Dimensional:
        - Tier 1a: match the column whose target_column == '<grain>_id'.
        - Tier 1b: match the first '*_id' column sourced from the base
          grain table '<grain>' (3NF has no HUB tables).

      Tier 2 (shared fallback, if Tier 1 finds nothing):
        - Match the column whose target_column == '<grain>_sk'.

    Returns a list (possibly empty) of increment key column names.
    Note: `source_table` / `target_column` values arriving here are
    already snake_cased/lowercased by adapt_input_format.
    """
    if not target_table_name or not columns:
        return []

    name_lower = str(target_table_name).strip().lower()

    # Strip 'fact_' prefix to get grain
    if name_lower.startswith("fact_"):
        grain = name_lower[len("fact_"):]
    else:
        grain = name_lower

    if not grain:
        return []

    expected_sk = f"{grain}_sk"

    if _is_3nf(conversion_type):
        expected_grain_id = f"{grain}_id"

        # ------- Tier 1a (3NF): exact <grain>_id target -------
        for col in columns:
            if not col:
                continue
            tgt = col.get("target_column")
            if tgt is not None and str(tgt).strip().lower() == expected_grain_id:
                return [_format_name(tgt)]

        # ------- Tier 1b (3NF): any *_id column from the base grain table -------
        for col in columns:
            if not col:
                continue
            src_tbl = col.get("source_table")
            tgt = col.get("target_column")
            if src_tbl is None or tgt is None:
                continue
            if (
                str(src_tbl).strip().lower() == grain
                and str(tgt).strip().lower().endswith("_id")
            ):
                return [_format_name(tgt)]
    else:
        expected_hub = f"HUB_{grain.upper()}"

        # ------- Tier 1 (Data Vault): HUB match -------
        for col in columns:
            if not col:
                continue
            src_tbl = col.get("source_table")
            if src_tbl is None:
                continue
            if str(src_tbl).strip().upper() == expected_hub:
                tgt = col.get("target_column")
                if tgt is not None and str(tgt).strip() != "":
                    return [_format_name(tgt)]

    # ------- Tier 2 (shared): SK fallback -------
    for col in columns:
        if not col:
            continue
        tgt = col.get("target_column")
        if tgt is None:
            continue
        if str(tgt).strip().lower() == expected_sk:
            return [_format_name(tgt)]

    return []


# ============================================================
# Input Format Adapter
# ============================================================

def adapt_input_format(raw_table: dict) -> dict:
    """
    Adapt new STTM input format (PascalCase + nested SourceMapping)
    into the internal flat snake_case format used by the rest of the pipeline.
    """

    if not raw_table:
        return {}

    table_type_raw = raw_table.get("Table_Type") or ""
    table_type_str = str(table_type_raw).strip().lower()

    if table_type_str == "dimension":
        normalized_table_type = "DIM"

    elif table_type_str == "fact":
        normalized_table_type = "FACT"

    else:
        normalized_table_type = (
            str(table_type_raw).strip().upper()
            if table_type_raw
            else ""
        )

    raw_mappings = raw_table.get("Column_Mappings") or []

    # Derive all_source_tables from per-column SourceMapping.Source_Table
    src_tables_set = []
    seen_src = set()

    for cm in raw_mappings:
        src_map = (cm or {}).get("SourceMapping") or {}

        st = src_map.get("Source_Table")

        if not _is_real_value(st):
            continue

        formatted_st = _format_name(st)

        if formatted_st not in seen_src:
            seen_src.add(formatted_st)
            src_tables_set.append(formatted_st)

    adapted = {
        "target_table": _format_name(
            raw_table.get("Target_Table")
        ),
        "table_type": normalized_table_type,
        "description": raw_table.get("Table_Definition"),
        "source_data_vault_table": _format_name(
            raw_table.get("Source_Data_Vault_Table")
        ),
        "source_logical_table": _format_name(
            raw_table.get("Source_Logical_Table")
        ),
        "all_source_tables": src_tables_set,
        "business_key": _format_name(
            raw_table.get("Business_Key")
        ),
        "scd_type": raw_table.get("SCD_Type"),
        "loading_order": raw_table.get("Loading_Order"),
        "dependency": raw_table.get("Dependency"),
        "retention_type": raw_table.get("Retention_Type"),
        "retention_attribute": _format_name(
            raw_table.get("Retention_Attribute")
        ),
        "retention_reference_table": _format_name(
            raw_table.get("Retention_Reference_Table")
        ),
        "watermark_date_columns": raw_table.get("Watermark_Date_Columns"),
        "watermark_time_columns": raw_table.get("Watermark_Time_Columns"),
        "where_clause": raw_table.get("Where_Clause"),
        "contains_pii": raw_table.get("Contains_PII"),
        "database_name": _format_name(
            raw_table.get("Database_Name")
        ),
        "schema_name": _format_name(
            raw_table.get("Schema_Name")
        ),
        "mappings": [],
    }

    for cm in raw_mappings:
        cm = cm or {}
        src_map = cm.get("SourceMapping") or {}

        adapted_mapping = {
            "source_column": _format_name(
                src_map.get("Source_Column")
            ),
            "source_table": _format_name(
                src_map.get("Source_Table")
            ),
            "target_column": _format_name(
                cm.get("Target_Column")
            ),
            "data_type": (
                str(cm.get("Data_Type")).strip().lower()
                if cm.get("Data_Type")
                else None
            ),
            "is_primary_key": _yes_no_to_bool(
                cm.get("Is_PK")
            ),
            "is_foreign_key": _yes_no_to_bool(
                cm.get("Is_FK")
            ),
            "transformation": src_map.get(
                "Transformation_Logic"
            ),
            "description": cm.get("Column_Definition"),
            "column_order": cm.get("Column_Order"),
        }

        adapted["mappings"].append(adapted_mapping)

    return adapted

# ============================================================
# STTM Cleaning + Transform
# ============================================================

def clean_sttm_for_config(sttm_data: dict) -> dict:
    """Strip STTM data to only the fields needed for config generation."""
    clean = {
        "target_table": sttm_data.get("target_table"),
        "table_type": sttm_data.get("table_type"),
        "source_data_vault_table": sttm_data.get("source_data_vault_table"),
        "source_logical_table": sttm_data.get("source_logical_table"),
        "all_source_tables": sttm_data.get("all_source_tables"),
        "business_key": sttm_data.get("business_key"),
        "scd_type": sttm_data.get("scd_type"),
        "mappings": [],
    }

    for m in sttm_data.get("mappings", []):
        clean_mapping = {
            "source_column": m.get("source_column"),
            "source_table": m.get("source_table"),
            "target_column": m.get("target_column"),
            "data_type": m.get("data_type"),
            "is_primary_key": m.get("is_primary_key"),
            "is_foreign_key": m.get("is_foreign_key"),
            "transformation": m.get("transformation"),
            "column_order": m.get("column_order"),
        }
        clean["mappings"].append(clean_mapping)

    return clean


def transform_sttm_to_config_json(sttm_data: dict) -> dict:
    """
    Convert cleaned STTM into a structured config dict for LLM prompting.
    For FACT tables we return only the config (no attribute_cols needed).
    """
    cleaned = clean_sttm_for_config(sttm_data or {})

    target_table = cleaned.get("target_table")
    target_table_str = (
        str(target_table).strip() if target_table is not None else ""
    )
    name = target_table_str.lower() if target_table_str else ""

    mappings = cleaned.get("mappings") or []
    columns = []
    primary_key_col = None
    foreign_key_cols = []

    for m in mappings:
        m = m or {}
        col_entry = {
            "source_column": m.get("source_column"),
            "source_table": m.get("source_table"),
            "target_column": m.get("target_column"),
            "data_type": m.get("data_type"),
            "is_primary_key": bool(m.get("is_primary_key")),
            "is_foreign_key": bool(m.get("is_foreign_key")),
            "transformation": m.get("transformation"),
            "column_order": m.get("column_order"),
        }
        columns.append(col_entry)

        tc = col_entry.get("target_column")
        if tc is not None:
            tc_norm = str(tc).strip().lower()
            if col_entry["is_primary_key"] and not primary_key_col:
                primary_key_col = tc_norm
            if col_entry["is_foreign_key"]:
                foreign_key_cols.append(tc_norm)

    has_transformations = any(
        c.get("transformation") is not None
        and str(c.get("transformation")).strip() != ""
        for c in columns
    )

    raw_source_tables = cleaned.get("all_source_tables") or []
    source_tables = [t for t in raw_source_tables if _is_real_value(t)]

    # Derive increment_keys deterministically. The Tier-1 rule adapts to
    # the configured source model (Data Vault vs 3NF); Tier-2 SK fallback
    # is shared.
    increment_keys = derive_increment_keys(
        name, columns, conversion_type=_get_conversion_type()
    )

    config_dict = {
        "name": name,
        "table_type": cleaned.get("table_type"),
        "target_table": target_table,
        "source_tables": source_tables,
        "source_data_vault_table": cleaned.get("source_data_vault_table"),
        "source_logical_table": cleaned.get("source_logical_table"),
        "business_key": cleaned.get("business_key"),
        "scd_type": cleaned.get("scd_type"),
        "primary_key": primary_key_col,
        "foreign_keys": foreign_key_cols,
        "increment_keys": increment_keys,
        "columns": columns,
        "has_transformations": has_transformations,
    }

    return config_dict


# ============================================================
# Stage SQL Prompt + Cleaner (FACT-specific)
# ============================================================


def clean_llm_sql(raw_sql: str) -> str:
    """Strip markdown fences, leading junk, normalise LLM SQL output."""
    sql = raw_sql.strip()
    sql = (
        sql.replace("```sql", "")
        .replace("```SQL", "")
        .replace("```Sql", "")
        .replace("```", "")
    )
    sql = sql.replace("\r", " ")
    sql = re.sub(
        r"^[^A-Z]*(WITH|SELECT|MERGE)",
        r"\1",
        sql,
        flags=re.IGNORECASE | re.DOTALL,
    )
    sql = sql.strip()
    if not re.match(r"^(WITH|SELECT|MERGE)\b", sql, flags=re.IGNORECASE):
        match = re.search(
            r"(WITH|SELECT|MERGE)\b.*",
            sql,
            flags=re.IGNORECASE | re.DOTALL,
        )
        sql = match.group(0).strip() if match else sql
    return sql.strip()


# ============================================================
# Stage SQL LLM Call
# ============================================================

def generate_stage_sql(config_json: dict, model_name: str = "openai", platform: str = "Databricks", sql_dialect: str = None) -> str:
    """Build prompt from config_json, call LLM, clean the result.

    `model_name` is forwarded to the LLM backend so the new UI can
    swap models. Default 'openai' preserves original behaviour.
    """
    prompt_text = build_fact_stage_sql_prompt(
        config_json,
        platform=platform,
        sql_dialect=sql_dialect,
        conversion_type=_get_conversion_type(),
    )
    raw_sql = convert_with_llm(prompt_text, model_name=model_name)
    return clean_llm_sql(raw_sql)


# ============================================================
# Config Assembly + Formatter (FACT-specific structure)
# ============================================================

def assemble_final_configs(config_json: dict, stage_sql: str) -> dict:
    """Assemble the final FACT config dictionary."""
    name = config_json.get("name", "")
    target_table = config_json.get("target_table", "")

    # increment_keys are now derived deterministically inside
    # transform_sttm_to_config_json (Tier 1 HUB match, Tier 2 SK fallback).
    # We simply propagate them here.
    increment_keys = config_json.get("increment_keys") or []
    # Defensive: ensure list of clean strings
    increment_keys = [
        str(k).strip()
        for k in increment_keys
        if k is not None and str(k).strip() != ""
    ]

    return {
        "name": name,
        "target_table": target_table,
        "stage_sql": stage_sql,
        "increment_keys": increment_keys,
    }


def format_config_as_python(config: dict, variable_name: str) -> str:
    """Format the FACT config dict as a Python source string."""
    name = str(config.get("name", ""))
    target_table = str(config.get("target_table", ""))

    raw_sql = str(config.get("stage_sql", ""))
    formatted_sql = raw_sql.replace("\\n", "\n")

    increment_keys = [str(k) for k in config.get("increment_keys", [])]

    # Extract bare table name
    parts = target_table.split(".")
    if len(parts) == 3:
        table_name = parts[2]
    elif len(parts) == 2:
        table_name = parts[1]
    else:
        table_name = target_table

    lines = []
    lines.append(f'{variable_name}_CFG = {{')
    lines.append(f'    "name": "{name}",')
    lines.append(
        f'    "target_table": '
        f'f"{{catalog_name}}.{{gold_schema_name}}.{table_name}",'
    )
    lines.append("")
    lines.append('    "stage_sql": f"""')
    for line in formatted_sql.split("\n"):
        lines.append(f"        {line}")
    lines.append('    """,')
    lines.append("")
    lines.append('    "increment_keys": [')
    for key in increment_keys:
        lines.append(f'        "{key}",')
    lines.append("    ],")
    lines.append("}")

    return "\n".join(lines)


# ============================================================
# Master function: Generate config for one FACT table
# ============================================================

def generate_config(sttm_data: dict, model_name: str = "openai", platform: str = "Databricks", sql_dialect: str = None) -> dict:
    """Generate ETL config for a single FACT table from its STTM data.

    `model_name` is forwarded to the LLM call (default 'openai').
    """
    config_json = transform_sttm_to_config_json(sttm_data)

    # Guard: if no source tables at all, skip LLM call
    src_tables = config_json.get("source_tables") or []
    src_dv = config_json.get("source_data_vault_table")
    src_logical = config_json.get("source_logical_table")

    has_any_source_hint = (
        len(src_tables) > 0
        or _is_real_value(src_dv)
        or _is_real_value(src_logical)
    )

    if not has_any_source_hint:
        print(
            f"  ℹ Skipping LLM call — '{config_json.get('name')}' has no "
            f"source tables defined."
        )
        stage_sql = (
            "-- No source tables defined. "
            "This fact table requires manual SQL definition."
        )
    else:
        stage_sql = generate_stage_sql(config_json, model_name=model_name, platform=platform, sql_dialect=sql_dialect)

    return assemble_final_configs(config_json, stage_sql)


# ============================================================
# Main execution: Process all FACT tables
# ============================================================

def run_all_fact(
    input_path: str,
    output_dir: str,
    model_name: str = "openai",
    platform: str = "Databricks",
    sql_dialect: str = None,
) -> dict:
    """Read input JSON, process all FACT tables, write config files.

    Optional `model_name` is forwarded to every per-table LLM call;
    defaults to 'openai' so existing callers see no behavioural change.
    """

    if not os.path.exists(input_path):
        print(f"ERROR: Input file not found: {input_path}")
        print(f"  Current directory: {os.getcwd()}")
        sys.exit(1)

    with open(input_path, "r", encoding="utf-8") as f:
        raw = json.load(f)

    # Robust unwrap
    if isinstance(raw, list):
        all_tables = raw
    elif isinstance(raw, dict):
        wrapper_keys = ["tables", "Tables", "sttm", "STTM", "data", "Data"]
        wrapped = None
        for k in wrapper_keys:
            if k in raw and isinstance(raw[k], list):
                wrapped = raw[k]
                break
        all_tables = wrapped if wrapped is not None else [raw]
    else:
        print(f"ERROR: Unexpected JSON root type: {type(raw).__name__}")
        sys.exit(1)

    print(f"DEBUG: Loaded {len(all_tables)} raw table(s) from input")

    adapted_tables = [adapt_input_format(t) for t in all_tables if t]

    print(f"DEBUG: Adapted {len(adapted_tables)} table(s):")
    for i, t in enumerate(adapted_tables):
        print(
            f"  [{i}] target_table={t.get('target_table')!r}, "
            f"table_type={t.get('table_type')!r}"
        )

    target_tables = [
        t for t in adapted_tables
        if str(t.get("table_type", "")).upper() == "FACT"
    ]

    if not target_tables:
        print("No FACT tables found in input")
        return {
            "success_count": 0,
            "failed_count": 0,
            "total_count": 0,
            "output_files": [],
            "failed_tables": [],
        }

    total = len(target_tables)
    print(f"\nProcessing {total} FACT table(s)...\n")

    os.makedirs(output_dir, exist_ok=True)
    output_files = []
    failed_tables = []

    for idx, sttm_data in enumerate(target_tables):
        table_name = sttm_data.get("target_table", f"table_{idx}")
        progress = f"[{idx + 1}/{total}]"

        print(f"  {progress} Generating config for: {table_name}")

        try:
            config = generate_config(sttm_data, model_name=model_name, platform=platform, sql_dialect=sql_dialect)

            if not config:
                msg = "Empty config returned"
                print(f"    WARNING: {msg}")
                failed_tables.append({"table": table_name, "error": msg})
                continue

            var_name = (
                table_name.replace(".", "_").replace("-", "_").upper()
            )
            config_str = format_config_as_python(config, var_name)
            config_filename = (
                table_name.lower().replace(".", "_") + "_config.py"
            )
            config_path = os.path.join(output_dir, config_filename)

            with open(config_path, "w", encoding="utf-8") as out_f:
                out_f.write(config_str)

            output_files.append(config_path)
            print(f"    ✓ Written: {config_path}")

        except Exception as e:
            error_msg = f"{type(e).__name__}: {str(e)}"
            print(f"    ✗ FAILED: {error_msg}")
            failed_tables.append({"table": table_name, "error": error_msg})

    success = len(output_files)
    failed = len(failed_tables)

    print()
    print("=" * 55)
    print(f"  COMPLETE: {success}/{total} succeeded, {failed} failed")
    print(f"  Output:   {os.path.abspath(output_dir)}")
    if failed_tables:
        print()
        for ft in failed_tables:
            print(f"    - {ft['table']}: {ft['error']}")
    print("=" * 55)

    return {
        "success_count": success,
        "failed_count": failed,
        "total_count": total,
        "output_files": output_files,
        "failed_tables": failed_tables,
    }


# ============================================================
# Entry point
# ============================================================

# if __name__ == "__main__":
#     input_file = (
#         sys.argv[1]
#         if len(sys.argv) > 1
#         else "input/erwin_customer360_final_mapping_file_08052026.json"
#     )
#     output_directory = (
#         sys.argv[2]
#         if len(sys.argv) > 2
#         else "output_static/configs_facts/"
#     )

#     print("=" * 55)
#     print("  Config Generator — FACT Tables")
#     print(f"  Input:  {input_file}")
#     print(f"  Output: {output_directory}")
#     print("=" * 55)
#     print()

#     result = run_all_fact(input_file, output_directory)

#     if result["failed_count"] > 0:
#         sys.exit(1)
#     sys.exit(0)