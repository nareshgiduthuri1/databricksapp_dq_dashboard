"""
Raw Data Vault config generator (Bronze -> Data Vault).
=======================================================

Shared generator for HUB / SAT / LINK tables. The config-dict STRUCTURE is
identical across the three object types — only `object_type`, `process_order`
and which build-SQL prompt is used differ — so a single module handles all
three (mirroring the existing generator flow: adapt -> transform -> LLM SQL
-> assemble -> format).

Output: ONE bundled config file per object type
(`hub_config.py`, `sat_config.py`, `link_config.py`) written into the
configs output dir, each containing one config dict per table:

    <target_table>_<product_id> = {
        "product_id": "3",
        "vault_object_id": "<target_table>_3",
        "object_type": "hub" | "sat" | "link",
        "target_table": "<target_table>",
        "process_order": "1" (hub) | "2" (link) | "3" (sat),
        "build_sql": f\"\"\" ... \"\"\",
        "source_table": "<comma-separated sources>",
    }

Only reached when the active target model is Raw Data Vault; the
Dimensional / Business Vault flows never call this module.
"""

import json
import re
import os
import sys

from modules.openai_call import convert_with_llm
from modules.prompts.hub_prompt import build_hub_build_sql_prompt
from modules.prompts.sat_prompt import build_sat_build_sql_prompt
from modules.prompts.link_prompt import build_link_build_sql_prompt


# ============================================================
# Constants
# ============================================================

PRODUCT_ID = "3"                       # hardcoded per requirement
PROCESS_ORDER = {"hub": "1", "link": "2", "sat": "3"}
_PROMPT_BUILDERS = {
    "hub": build_hub_build_sql_prompt,
    "sat": build_sat_build_sql_prompt,
    "link": build_link_build_sql_prompt,
}
# Normalise the STTM Table_Type value to our object_type key.
_TABLE_TYPE_TO_OBJECT = {
    "hub": "hub",
    "sat": "sat",
    "satellite": "sat",
    "link": "link",
}


# ============================================================
# Helpers
# ============================================================

def _is_real_value(v) -> bool:
    if v is None:
        return False
    s = str(v).strip().lower()
    return s not in ("", "null", "none")


def _split_source_tables(value) -> list:
    """Split a possibly comma-separated Source_Table string into names."""
    if not _is_real_value(value):
        return []
    return [p.strip() for p in str(value).split(",") if p.strip()]


def clean_llm_sql(raw_sql: str) -> str:
    """Strip markdown fences / leading junk, normalise LLM SQL output."""
    sql = (raw_sql or "").strip()
    sql = (
        sql.replace("```sql", "").replace("```SQL", "")
        .replace("```Sql", "").replace("```", "")
    )
    sql = sql.replace("\r", " ")
    # Trim anything before the first WITH/SELECT.
    if not re.match(r"^(WITH|SELECT)\b", sql, flags=re.IGNORECASE):
        m = re.search(r"(WITH|SELECT)\b.*", sql, flags=re.IGNORECASE | re.DOTALL)
        sql = m.group(0).strip() if m else sql
    return sql.strip()


# ============================================================
# Input adapter
# ============================================================

def adapt_input_format(raw_table: dict) -> dict:
    """Adapt one STTM table record into the raw-vault config_json shape."""
    if not raw_table:
        return {}

    table_type_raw = str(raw_table.get("Table_Type") or "").strip().lower()
    object_type = _TABLE_TYPE_TO_OBJECT.get(table_type_raw, table_type_raw)

    target_table = str(raw_table.get("Target_Table") or "").strip()

    raw_mappings = raw_table.get("Column_Mappings") or []

    source_tables: list = []
    seen_src = set()
    columns = []
    for cm in raw_mappings:
        cm = cm or {}
        sm = cm.get("SourceMapping") or {}

        for st in _split_source_tables(sm.get("Source_Table")):
            if st not in seen_src:
                seen_src.add(st)
                source_tables.append(st)

        columns.append({
            "target_column": cm.get("Target_Column"),
            "source_table": sm.get("Source_Table"),
            "source_column": sm.get("Source_Column"),
            "transformation": sm.get("Transformation_Logic"),
            "filter_rule": sm.get("Filter_Rule"),
            "is_pk": str(cm.get("Is_PK", "No")).strip().lower() in ("yes", "y", "true", "1"),
            "is_fk": str(cm.get("Is_FK", "No")).strip().lower() in ("yes", "y", "true", "1"),
            "data_type": cm.get("Data_Type"),
        })

    # Table-level filter rule = the first non-empty column Filter_Rule.
    # (Filter Rule is a column UDP but is consistent per table/source; it
    # carries per-source conditions like 'CRM: ...  SAP: ...'.)
    table_filter_rule = next(
        (c["filter_rule"] for c in columns if _is_real_value(c.get("filter_rule"))),
        None,
    )

    return {
        "object_type": object_type,
        "target_table": target_table,
        "source_tables": source_tables,
        # Per-source filter conditions from the mapping (None if absent).
        "filter_rule": table_filter_rule,
        "columns": columns,
    }


# ============================================================
# Build SQL (LLM)
# ============================================================

def generate_build_sql(
    config_json: dict,
    model_name: str = "openai",
    platform: str = "Databricks",
    sql_dialect: str = None,
) -> str:
    """Build the object-type-specific prompt, call the LLM, clean the SQL."""
    object_type = config_json.get("object_type")
    builder = _PROMPT_BUILDERS.get(object_type)
    if builder is None:
        return f"-- Unsupported object_type '{object_type}'."
    prompt_text = builder(config_json, platform=platform, sql_dialect=sql_dialect)
    raw_sql = convert_with_llm(prompt_text, model_name=model_name)
    return clean_llm_sql(raw_sql)


# ============================================================
# Config assembly + formatting
# ============================================================

def assemble_config(adapted: dict, build_sql: str) -> dict:
    """Assemble the final raw-vault config dict for one table."""
    target_table = adapted.get("target_table", "")
    object_type = adapted.get("object_type", "")
    vault_object_id = f"{target_table}_{PRODUCT_ID}"
    return {
        "product_id": PRODUCT_ID,
        "vault_object_id": vault_object_id,
        "object_type": object_type,
        "target_table": target_table,
        "process_order": PROCESS_ORDER.get(object_type, ""),
        "build_sql": build_sql,
        "source_table": ",".join(adapted.get("source_tables") or []),
    }


def format_config_as_python(config: dict) -> str:
    """Format one config dict as a Python assignment block (DE style)."""
    var_name = config.get("vault_object_id", "unknown")
    raw_sql = str(config.get("build_sql", "")).replace("\\n", "\n")

    lines = []
    lines.append(f"{var_name} =  {{")
    lines.append(f'  "product_id": "{config.get("product_id", "")}",')
    lines.append(f'  "vault_object_id": "{config.get("vault_object_id", "")}",')
    lines.append(f'  "object_type": "{config.get("object_type", "")}",')
    lines.append(f'  "target_table": "{config.get("target_table", "")}",')
    lines.append(f'  "process_order": "{config.get("process_order", "")}",')
    lines.append('  "build_sql": f"""')
    lines.append(raw_sql.strip())
    lines.append('""",')
    lines.append(f'  "source_table": "{config.get("source_table", "")}"')
    lines.append("}")
    return "\n".join(lines)


# ============================================================
# Per-table generation
# ============================================================

def generate_config(
    sttm_data: dict,
    model_name: str = "openai",
    platform: str = "Databricks",
    sql_dialect: str = None,
) -> dict:
    """Generate the config dict for a single raw-vault table."""
    adapted = adapt_input_format(sttm_data)

    if not (adapted.get("source_tables") or []):
        print(
            f"  ℹ Skipping LLM call — '{adapted.get('target_table')}' has no "
            f"source tables defined."
        )
        build_sql = (
            "-- No source tables defined. "
            "This object requires a manual build SQL definition."
        )
    else:
        build_sql = generate_build_sql(
            adapted, model_name=model_name, platform=platform,
            sql_dialect=sql_dialect,
        )

    return assemble_config(adapted, build_sql)


# ============================================================
# Run all tables of one object type -> one bundled file
# ============================================================

def run_all(
    input_path: str,
    output_dir: str,
    object_type: str,
    model_name: str = "openai",
    platform: str = "Databricks",
    sql_dialect: str = None,
) -> dict:
    """Process every table in the slice JSON and write ONE bundled config
    file (`<object_type>_config.py`) into `output_dir`."""
    result = {
        "object_type": object_type,
        "success_count": 0,
        "failed_count": 0,
        "total_count": 0,
        "output_file": None,
        "failed_tables": [],
    }

    if not os.path.exists(input_path):
        print(f"  ⚠ Slice not found: {input_path} — nothing to generate.")
        return result

    with open(input_path, "r", encoding="utf-8") as f:
        raw = json.load(f)

    all_tables = raw if isinstance(raw, list) else raw.get("tables", [raw])
    # Defensive: only keep tables matching this object type.
    tables = [
        t for t in all_tables if t
        and _TABLE_TYPE_TO_OBJECT.get(
            str(t.get("Table_Type") or "").strip().lower()
        ) == object_type
    ]
    result["total_count"] = len(tables)

    if not tables:
        print(f"  No {object_type} tables found in {input_path}")
        return result

    print(f"\nProcessing {len(tables)} {object_type} table(s)...\n")
    os.makedirs(output_dir, exist_ok=True)

    blocks = []
    for idx, sttm_data in enumerate(tables):
        target = sttm_data.get("Target_Table", f"table_{idx}")
        print(f"  [{idx + 1}/{len(tables)}] Generating {object_type} config for: {target}")
        try:
            config = generate_config(
                sttm_data, model_name=model_name, platform=platform,
                sql_dialect=sql_dialect,
            )
            blocks.append(format_config_as_python(config))
            result["success_count"] += 1
        except Exception as e:  # pragma: no cover - defensive
            err = f"{type(e).__name__}: {e}"
            print(f"    ✗ FAILED: {err}")
            result["failed_tables"].append({"table": target, "error": err})
            result["failed_count"] += 1

    header = (
        "# Databricks notebook source\n"
        f"# DBTITLE 1,{object_type.capitalize()} Configs - Product ID {PRODUCT_ID}\n\n"
    )
    out_path = os.path.join(output_dir, f"{object_type}_config.py")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(header + "\n\n".join(blocks) + "\n")
    result["output_file"] = out_path

    print(f"    ✓ Written: {out_path}")
    print("=" * 55)
    print(
        f"  {object_type.upper()} COMPLETE: "
        f"{result['success_count']}/{result['total_count']} succeeded, "
        f"{result['failed_count']} failed"
    )
    print("=" * 55)
    return result
