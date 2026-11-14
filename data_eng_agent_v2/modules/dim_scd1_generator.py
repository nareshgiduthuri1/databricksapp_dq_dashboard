"""
Code Generator — Standalone
Table Type: DIM (SCD Type 1)

Reads input JSON (PascalCase format), iterates over all DIM tables
where SCD_Type == "1", generates the stage SQL via OpenAI, and writes
a runnable Python file per table embedding the SCD-1 incremental
MERGE template.

Usage:
    python code_generator_scd1.py
    python code_generator_scd1.py input/data.json output/scd1_code/
"""

import json
import re
import os
import sys

from modules.openai_call import convert_with_llm
from modules.prompts.dim_scd1_prompt import build_dim_scd1_stage_sql_prompt
from modules import generation_profiles as _gp


# ============================================================
# Input Format Adapter
# ============================================================

def _yes_no_to_bool(v) -> bool:
    if v is None:
        return False
    if isinstance(v, bool):
        return v
    s = str(v).strip().lower()
    return s in ("yes", "y", "true", "1")


def adapt_input_format(raw_table: dict) -> dict:
    """Adapt PascalCase STTM input into internal snake_case format."""
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
            str(table_type_raw).strip().upper() if table_type_raw else ""
        )

    raw_mappings = raw_table.get("Column_Mappings") or []
    src_tables_set = []
    seen_src = set()
    for cm in raw_mappings:
        src_map = (cm or {}).get("SourceMapping") or {}
        st = src_map.get("Source_Table")
        if st is None:
            continue
        st_str = str(st).strip()
        if not st_str or st_str.lower() in ("null", "none"):
            continue
        if st_str.lower() not in seen_src:
            seen_src.add(st_str.lower())
            src_tables_set.append(st_str)

    adapted = {
        "target_table": raw_table.get("Target_Table"),
        "table_type": normalized_table_type,
        "description": raw_table.get("Table_Definition"),
        "source_data_vault_table": raw_table.get("Source_Data_Vault_Table"),
        "source_logical_table": raw_table.get("Source_Logical_Table"),
        "all_source_tables": src_tables_set,
        "business_key": raw_table.get("Business_Key"),
        "scd_type": raw_table.get("SCD_Type"),
        "loading_order": raw_table.get("Loading_Order"),
        "dependency": raw_table.get("Dependency"),
        "retention_type": raw_table.get("Retention_Type"),
        "retention_attribute": raw_table.get("Retention_Attribute"),
        "retention_reference_table": raw_table.get("Retention_Reference_Table"),
        "watermark_date_columns": raw_table.get("Watermark_Date_Columns"),
        "watermark_time_columns": raw_table.get("Watermark_Time_Columns"),
        "where_clause": raw_table.get("Where_Clause"),
        "contains_pii": raw_table.get("Contains_PII"),
        "database_name": raw_table.get("Database_Name"),
        "schema_name": raw_table.get("Schema_Name"),
        "mappings": [],
    }

    for cm in raw_mappings:
        cm = cm or {}
        src_map = cm.get("SourceMapping") or {}
        adapted["mappings"].append({
            "source_column": src_map.get("Source_Column"),
            "source_table": src_map.get("Source_Table"),
            "target_column": cm.get("Target_Column"),
            "data_type": cm.get("Data_Type"),
            "is_primary_key": _yes_no_to_bool(cm.get("Is_PK")),
            "is_foreign_key": _yes_no_to_bool(cm.get("Is_FK")),
            "transformation": src_map.get("Transformation_Logic"),
            "description": cm.get("Column_Definition"),
            "column_order": cm.get("Column_Order"),
        })

    return adapted


# ============================================================
# Helpers
# ============================================================

_AUDIT_COLS = {
    "created_ts", "created_by", "updated_ts", "updated_by",
    "last_updated_ts", "last_updated_by",
    "attr_hash", "load_date", "load_ts", "insert_ts",
    "effective_from_ts", "effective_to_ts", "record_version",
}


def _is_real_value(v) -> bool:
    if v is None:
        return False
    s = str(v).strip().lower()
    return s not in ("", "null", "none")


# Business Vault xref tables carry no PK; their natural/MERGE key is the
# FK link to the master. Resolved by semantics, not naming, so it works
# for any convention (global_*_identifier, global_*_id, or future names).
def _bv_xref_business_key_targets(sttm_data: dict) -> set:
    """Resolve the BV xref business/MERGE key by semantics, not naming.

    1. Use the table-level Business_Key if the mapping populates it
       (future-proof; currently None for xref).
    2. Otherwise the Is_FK=Yes column(s) — an xref's link to its master
       is its business key. If several FK columns exist, prefer a
       global_-prefixed one, else take the first.

    Returns a set of lowercased target column name(s).
    """
    mappings = sttm_data.get("mappings") or []

    # 1. Table-level Business_Key (future-proof; currently None for xref).
    bk = sttm_data.get("business_key")
    if _is_real_value(bk):
        return {str(bk).strip().lower()}

    # 2. Fall back to the FK column(s) — the xref's link to its master.
    fk_cols = [
        str(m.get("target_column")).strip()
        for m in mappings
        if m and m.get("target_column") and m.get("is_foreign_key")
    ]
    if not fk_cols:
        return set()
    global_fks = [c for c in fk_cols if c.lower().startswith("global_")]
    chosen = global_fks[0] if global_fks else fk_cols[0]
    return {chosen.lower()}


def derive_attribute_columns(sttm_data: dict) -> tuple:
    """
    Return (business_key_cols, attribute_cols) — both as lists of
    target column names (preserving original casing where possible).
    """
    mappings = sttm_data.get("mappings") or []
    business_keys = []
    attribute_cols = []
    seen_attr = set()
    seen_bk = set()

    # Business Vault xref tables have no PK; the FK-to-master column is
    # their business/MERGE key (resolved by semantics). Dimensional is
    # unaffected — bv_bk_targets stays empty when target isn't BV.
    is_bv_target = _gp.get_target_model() == _gp.TARGET_BUSINESS_VAULT
    bv_bk_targets = (
        _bv_xref_business_key_targets(sttm_data) if is_bv_target else set()
    )

    for m in mappings:
        m = m or {}
        target_column = m.get("target_column")
        if not target_column:
            continue

        target_str = str(target_column).strip()
        target_norm = target_str.lower()
        if not target_norm:
            continue

        is_pk = bool(m.get("is_primary_key"))
        is_fk = bool(m.get("is_foreign_key"))

        if is_pk:
            if target_norm not in seen_bk:
                seen_bk.add(target_norm)
                business_keys.append(target_str)
            continue

        # BV: the xref's FK-to-master is its business/MERGE key. Detect it
        # BEFORE the FK-skip below so the key isn't dropped.
        if is_bv_target and target_norm in bv_bk_targets:
            if target_norm not in seen_bk:
                seen_bk.add(target_norm)
                business_keys.append(target_str)
            continue

        if is_fk:
            continue

        # Audit/system columns are excluded from attribute_cols. Business
        # Vault detects them by concept (naming-agnostic) so renamed columns
        # like load_ts are still recognised; Dimensional uses its static set.
        if is_bv_target:
            if _gp.bv_is_audit_col(target_norm):
                continue
        elif target_norm in _gp.get_profile().audit_cols:
            continue

        if target_norm in seen_attr:
            continue
        seen_attr.add(target_norm)
        attribute_cols.append(target_str)

    return business_keys, attribute_cols


# ============================================================
# Stage SQL Prompt + Cleaner
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

    # Strip f-string wrappers around table refs
    sql = re.sub(r'f"([A-Za-z_{][A-Za-z0-9_.{}]*)"', r'\1', sql)
    sql = re.sub(r"f'([A-Za-z_{][A-Za-z0-9_.{}]*)'", r'\1', sql)

    # Defensive: convert any generic {schema_name} → vault/gold split
    sql = re.sub(
        r'\{schema_name\}(\.(?:HUB_|SAT_|LINK_))',
        r'{vault_schema_name}\1',
        sql, flags=re.IGNORECASE,
    )
    sql = re.sub(
        r'\{schema_name\}(\.DIM_)',
        r'{gold_schema_name}\1',
        sql, flags=re.IGNORECASE,
    )
    sql = re.sub(
        r'\{schema_name\}(\.[A-Za-z_])',
        r'{vault_schema_name}\1',
        sql,
    )

    return sql.strip()


def generate_stage_sql(
    sttm_data: dict,
    attribute_cols: list,
    business_keys: list,
    model_name: str = "openai",
    platform: str = "Databricks",
    sql_dialect: str = None,
) -> str:
    """Build prompt, call LLM, clean and return stage SQL.

    `model_name` is forwarded to the LLM backend (default 'openai').
    """
    prompt_text = build_dim_scd1_stage_sql_prompt(
        sttm_data, attribute_cols, business_keys,
        platform=platform, sql_dialect=sql_dialect,
    )
    # No-op for Dimensional; swaps audit names for Business Vault.
    prompt_text = _gp.apply_audit_renames(prompt_text)
    # Business Vault only: append source-fidelity rules (preserve every
    # WHERE/record_source/join predicate; prefer per-source CTE structure).
    prompt_text = _gp.append_bv_fidelity_rules(prompt_text)
    raw_sql = convert_with_llm(prompt_text, model_name=model_name)
    return clean_llm_sql(raw_sql)


# ============================================================
# Code Template Renderer (SCD-1 Incremental MERGE)
# ============================================================

def render_scd1_code(
    target_table_name: str,
    business_keys: list,
    attribute_cols: list,
    stage_sql: str,
    catalog_default: str = "allianz_coe",
    gold_schema_default: str = "agentic_testing",
    vault_schema_default: str = "dvault_faker01",
    control_schema_default: str = "audit_control",
    watermark_table_default: str = "application_watermark",
    bv_meta: dict = None,
) -> str:
    """
    Render the runnable Python SCD-1 incremental load code,
    embedding the LLM-generated stage SQL, prefixed with
    dbutils widget setup.

    `bv_meta` (Business Vault only): when provided, an xref metadata block
    (modelling_pattern / hash_col / object_id / attribute_cols / insert_cols)
    is emitted after the staging SQL. None -> no block (Dimensional).
    """
    name_lower = target_table_name.lower()

    # Business Vault xref metadata block (emitted only for BV; empty string
    # otherwise so Dimensional output is unchanged).
    bv_meta_block = ""
    if bv_meta is not None:
        def _pylist(items):
            return "[" + ", ".join(f'"{i}"' for i in items) + "]"
        meta_attribute_cols = list(business_keys) + list(attribute_cols)
        meta_insert_cols = meta_attribute_cols + list(bv_meta.get("audit_cols") or [])
        hash_col_val = bv_meta.get("hash_col") or "rawdv_hash_key"
        object_id_val = f"{name_lower}_3"
        bv_meta_block = (
            "    # ===============================\n"
            "    # Business Vault xref metadata\n"
            "    # ===============================\n"
            '    modelling_pattern = "business_vault"\n'
            f'    hash_col = "{hash_col_val}"\n'
            f'    object_id = "{object_id_val}"\n'
            f'    attribute_cols = {_pylist(meta_attribute_cols)}\n'
            f'    insert_cols = {_pylist(meta_insert_cols)}\n'
        )

    # SQL fragments built from attribute lists
    merge_select_cols = ", ".join(business_keys + attribute_cols + ["attr_hash"])

    # ON clause
    on_clause = "\n        AND ".join(
        [f"tgt.{bk} = src.{bk}" for bk in business_keys]
    )

    # UPDATE SET — attribute cols only (not business keys)
    update_set_lines = ",\n            ".join(
        [f"tgt.{c} = src.{c}" for c in attribute_cols] +
        [
            "tgt.last_updated_by = 'ETL_SYSTEM'",
            "tgt.last_updated_ts = current_timestamp()",
            "tgt.attr_hash = src.attr_hash",
        ]
    )

    # INSERT column list & VALUES
    insert_cols_list = business_keys + attribute_cols + [
        "attr_hash",
        "created_by", "created_ts",
        "last_updated_by", "last_updated_ts",
    ]
    insert_cols_csv = ", ".join(insert_cols_list)

    insert_values_list = (
        [f"src.{c}" for c in business_keys + attribute_cols] +
        [
            "src.attr_hash",
            "'ETL_SYSTEM'", "current_timestamp()",
            "'ETL_SYSTEM'", "current_timestamp()",
        ]
    )
    insert_values_csv = ", ".join(insert_values_list)

    # ============================================================
    # Header block — dbutils widgets + variable extraction
    # ============================================================
    header = f'''dbutils.widgets.text("table_name", "{name_lower}")
dbutils.widgets.text("catalog_name", "{catalog_default}")
dbutils.widgets.text("gold_schema_name", "{gold_schema_default}")
dbutils.widgets.text("vault_schema_name", "{vault_schema_default}")
dbutils.widgets.text("batch_run_id", "")
dbutils.widgets.text("task_run_id", "")
dbutils.widgets.text("control_schema_name", "{control_schema_default}")
dbutils.widgets.text("watermark_table_name", "{watermark_table_default}")

catalog_name = dbutils.widgets.get("catalog_name")
gold_schema_name = dbutils.widgets.get("gold_schema_name")
vault_schema_name = dbutils.widgets.get("vault_schema_name")
dim_name = dbutils.widgets.get("table_name")
batch_run_id = dbutils.widgets.get("batch_run_id")
task_run_id = dbutils.widgets.get("task_run_id")
control_schema_name = dbutils.widgets.get("control_schema_name")
watermark_table_name = dbutils.widgets.get("watermark_table_name")


full_table_name = f"{{catalog_name}}.{{gold_schema_name}}.{{dim_name}}"
full_wm_table_name = f"{{catalog_name}}.{{control_schema_name}}.{{watermark_table_name}}"
etl_component_name = dbutils.notebook.entry_point.getDbutils() \\
.notebook().getContext().notebookPath().get()


'''

    # ============================================================
    # Body block — SCD-1 incremental load
    # ============================================================
    body = f'''# ===============================
# Incremental SCD-1 Load: {target_table_name}
# ===============================

tgt_tbl = f"{{catalog_name}}.{{gold_schema_name}}.{target_table_name}"
full_table_name = "{name_lower}"

# 1. Get watermark on the fly from the target
wm_df = spark.sql(f"""
    SELECT COALESCE(MAX(watermark), TIMESTAMP('1900-01-01 00:00:00')) AS wm
    FROM {{full_wm_table_name}} WHERE table_name = '{{tgt_tbl}}'
""")
watermark_ts = wm_df.collect()[0]["wm"]

log_message = f"Running {name_lower}. Watermark used : {{watermark_ts}}"
task_log(
    task_run_id=task_run_id,
    task_name=full_table_name,
    etl_component_name=etl_component_name,
    message=log_message,
)

print(f"Using watermark from target.last_updated_ts: {{watermark_ts}}")


try:
    # 2. Build incremental staging dataset (LLM-generated)
    staging_sql = f"""
{stage_sql}
"""
{bv_meta_block}    log_message = f"staging_sql used for {name_lower} : {{staging_sql}}"
    task_log(
        task_run_id=task_run_id,
        task_name=full_table_name,
        message=log_message,
        etl_component_name=etl_component_name,
    )

    stg_df = spark.sql(staging_sql)

    # 3. Short-circuit if nothing new
    if stg_df.isEmpty():
        log_message = (
            f"No new or changed rows since {{watermark_ts}}. "
            f"Nothing to merge."
        )
        task_log(
            task_run_id=task_run_id,
            task_name=full_table_name,
            message=log_message,
            etl_component_name=etl_component_name,
        )
        task_status = 'success'
        tot_row_count = 0
    else:
        stg_df.createOrReplaceTempView("stg_{name_lower}")

        # 4. Perform SCD-1 MERGE (overwrite on match)
        merge_sql = f"""
        MERGE INTO {{tgt_tbl}} AS tgt
        USING (
            SELECT {merge_select_cols} FROM stg_{name_lower}
        ) AS src
        ON {on_clause}

        WHEN MATCHED AND tgt.attr_hash != src.attr_hash THEN UPDATE SET
            {update_set_lines}

        WHEN NOT MATCHED THEN INSERT (
            {insert_cols_csv}
        ) VALUES (
            {insert_values_csv}
        )
        """
        log_message = f"merge_sql used : {{merge_sql}}"
        task_log(
            task_run_id=task_run_id,
            task_name=full_table_name,
            message=log_message,
            etl_component_name=etl_component_name,
        )

        spark.sql(merge_sql)
        print("Incremental SCD-1 MERGE completed successfully.")

        history = spark.sql(f"DESCRIBE HISTORY {{tgt_tbl}}").first()
        metrics = history.operationMetrics

        insert_dict = {{
            "Inserted": metrics['numTargetRowsInserted'],
            "Updated": metrics['numTargetRowsUpdated'],
        }}

        task_status = 'success'
        tot_row_count = (
            int(insert_dict['Inserted']) + int(insert_dict['Updated'])
        )
        log_message = f"{name_lower} ran successfully"
        task_log(
            task_run_id=task_run_id,
            task_name=full_table_name,
            message=log_message,
            etl_component_name=etl_component_name,
        )
except Exception as e:
    exception_msg = str(e)
    print(f"Error occurred: {{exception_msg}}")
    task_status = 'failed'
    tot_row_count = -1
    log_message = f"exception occurred : {{exception_msg}}"
    task_log(
        task_run_id=task_run_id,
        task_name=full_table_name,
        message=log_message,
        etl_component_name=etl_component_name,
    )
'''

    return header + body

# ============================================================
# Master function: Generate code for one table
# ============================================================

def generate_code(sttm_data: dict, model_name: str = "openai", platform: str = "Databricks", sql_dialect: str = None) -> str:
    """Generate runnable SCD-1 Python code for a single table.

    `model_name` is forwarded to the LLM call (default 'openai').
    """
    business_keys, attribute_cols = derive_attribute_columns(sttm_data)
    target_table = sttm_data.get("target_table") or ""

    # Derive bare table name (remove schema/catalog if present)
    table_name = target_table.split(".")[-1] if target_table else ""

    if not business_keys:
        print(
            f"  ⚠ WARNING: '{table_name}' has no primary key columns. "
            f"MERGE ON clause cannot be built."
        )
        return None

    if not attribute_cols:
        print(
            f"  ⚠ WARNING: '{table_name}' has no attribute columns. "
            f"Nothing to MERGE — skipping."
        )
        return None

    # Check we have any source hint at all
    src_tables = sttm_data.get("all_source_tables") or []
    src_dv = sttm_data.get("source_data_vault_table")
    src_logical = sttm_data.get("source_logical_table")

    has_any_source_hint = (
        len(src_tables) > 0
        or _is_real_value(src_dv)
        or _is_real_value(src_logical)
    )

    if not has_any_source_hint:
        print(
            f"  ℹ Skipping LLM call — '{table_name}' has no source tables "
            f"(static dimension)."
        )
        return None

    print(f"    Business keys: {business_keys}")
    print(f"    Attribute cols: {attribute_cols}")

    stage_sql = generate_stage_sql(
        sttm_data, attribute_cols, business_keys, model_name=model_name,
        platform=platform, sql_dialect=sql_dialect,
    )

    # Business Vault xref: build the metadata block inputs (hash_col from the
    # actual rawdv_*hash*key column; audit cols detected by concept, e.g.
    # load_ts). None for Dimensional -> no metadata block emitted.
    bv_meta = None
    if _gp.get_target_model() == _gp.TARGET_BUSINESS_VAULT:
        all_target_names = [
            str(m.get("target_column")).strip().lower()
            for m in (sttm_data.get("mappings") or [])
            if m and m.get("target_column")
        ]
        hash_col = next(
            (n for n in all_target_names if re.search(r"rawdv.*hash.*key", n)),
            "rawdv_hash_key",
        )
        bv_meta = {
            "hash_col": hash_col,
            "audit_cols": _gp.bv_audit_columns(all_target_names),
        }

    code_str = render_scd1_code(
        target_table_name=table_name,
        business_keys=business_keys,
        attribute_cols=attribute_cols,
        stage_sql=stage_sql,
        bv_meta=bv_meta,
    )
    return code_str


# ============================================================
# Main execution: Process all DIM tables with SCD_Type == "1"
# ============================================================

def _is_scd1(scd_value) -> bool:
    if scd_value is None:
        return False
    s = str(scd_value).strip().lower()
    return s in ("1", "scd1", "scd 1", "scd_1", "type 1", "type1")


def run_all_dim_scd1(
    input_path: str,
    output_dir: str,
    model_name: str = "openai",
    platform: str = "Databricks",
    sql_dialect: str = None,
) -> dict:
    """Read input JSON, process all SCD-1 DIM tables, write notebooks.

    Optional `model_name` is forwarded to every per-table LLM call;
    defaults to 'openai' so existing callers see no behavioural change.
    """
    if not os.path.exists(input_path):
        print(f"ERROR: Input file not found: {input_path}")
        print(f"  Current directory: {os.getcwd()}")
        sys.exit(1)

    with open(input_path, "r", encoding="utf-8") as f:
        raw = json.load(f)

    if isinstance(raw, list):
        all_tables = raw
    elif isinstance(raw, dict):
        wrapper_keys = ["tables", "Tables", "sttm", "STTM", "data", "Data"]
        wrapped = None
        for k in wrapper_keys:
            if k in raw and isinstance(raw[k], list):
                wrapped = raw[k]
                break
        if wrapped is not None:
            all_tables = wrapped
        else:
            all_tables = [raw]
    else:
        print(f"ERROR: Unexpected JSON root type: {type(raw).__name__}")
        sys.exit(1)

    print(f"DEBUG: Loaded {len(all_tables)} raw table(s) from input")

    adapted_tables = [adapt_input_format(t) for t in all_tables if t]

    print(f"DEBUG: Adapted {len(adapted_tables)} table(s):")
    for i, t in enumerate(adapted_tables):
        print(
            f"  [{i}] target_table={t.get('target_table')!r}, "
            f"table_type={t.get('table_type')!r}, "
            f"scd_type={t.get('scd_type')!r}"
        )

    # Target-model aware selection. Dimensional selects DIM + SCD1
    # tables; Business Vault xref tables are not typed "dimension", so
    # select purely by SCD type == 1.
    if _gp.get_target_model() == _gp.TARGET_BUSINESS_VAULT:
        target_tables = [
            t for t in adapted_tables
            if _is_scd1(t.get("scd_type"))
        ]
    else:
        target_tables = [
            t for t in adapted_tables
            if str(t.get("table_type", "")).upper() == "DIM"
            and _is_scd1(t.get("scd_type"))
        ]

    if not target_tables:
        print("No SCD-1 tables found in input")
        return {
            "success_count": 0,
            "failed_count": 0,
            "total_count": 0,
            "output_files": [],
            "failed_tables": [],
        }

    total = len(target_tables)
    print(f"\nProcessing {total} SCD-1 DIM table(s)...\n")

    os.makedirs(output_dir, exist_ok=True)
    output_files = []
    failed_tables = []
    skipped_tables = []

    for idx, sttm_data in enumerate(target_tables):
        table_name = sttm_data.get("target_table", f"table_{idx}")
        progress = f"[{idx + 1}/{total}]"

        print(f"  {progress} Generating SCD-1 code for: {table_name}")

        try:
            code_str = generate_code(sttm_data, model_name=model_name, platform=platform, sql_dialect=sql_dialect)

            if code_str is None:
                skipped_tables.append(table_name)
                continue

            bare_name = table_name.split(".")[-1].lower()
            code_filename = f"{bare_name}_scd1_load.py"
            code_path = os.path.join(output_dir, code_filename)

            with open(code_path, "w", encoding="utf-8") as out_f:
                out_f.write(code_str)

            output_files.append(code_path)
            print(f"    ✓ Written: {code_path}")

        except Exception as e:
            error_msg = f"{type(e).__name__}: {str(e)}"
            print(f"    ✗ FAILED: {table_name} - {error_msg}")
            failed_tables.append({"table": table_name, "error": error_msg})

    success = len(output_files)
    failed = len(failed_tables)
    skipped = len(skipped_tables)

    print()
    print("=" * 55)
    print(
        f"  COMPLETE: {success}/{total} succeeded, "
        f"{failed} failed, {skipped} skipped"
    )
    print(f"  Output:   {os.path.abspath(output_dir)}")
    if failed_tables:
        print()
        for ft in failed_tables:
            print(f"    FAILED - {ft['table']}: {ft['error']}")
    if skipped_tables:
        print()
        for st in skipped_tables:
            print(f"    SKIPPED - {st}")
    print("=" * 55)

    return {
        "success_count": success,
        "failed_count": failed,
        "total_count": total,
        "output_files": output_files,
        "failed_tables": failed_tables,
        "skipped_tables": skipped_tables,
    }


# ============================================================
# Entry point
# ============================================================

if __name__ == "__main__":
    input_file = (
        sys.argv[1]
        if len(sys.argv) > 1
        else "input/Enhanced Customer360 Data Model Repository.json"
    )
    output_directory = (
        sys.argv[2]
        if len(sys.argv) > 2
        else "output_static/scd1_code/"
    )

    print("=" * 55)
    print("  Code Generator — DIM Tables (SCD Type 1)")
    print(f"  Input:  {input_file}")
    print(f"  Output: {output_directory}")
    print("=" * 55)
    print()

    result = run_all_dim_scd1(input_file, output_directory)

    if result["failed_count"] > 0:
        sys.exit(1)
    sys.exit(0)