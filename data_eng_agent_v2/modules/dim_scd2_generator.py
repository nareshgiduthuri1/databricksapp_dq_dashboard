"""
Config Generator — Standalone
Table Type: DIM

Reads input JSON (new PascalCase format), iterates over all DIM tables,
generates ETL config for each via OpenAI, writes output files.

Usage:
    python config_generator_dim.py
    python config_generator_dim.py input/data.json output/configs/
"""

import json
import re
import os
import sys

from modules.openai_call import convert_with_llm
from modules.prompts.dim_scd2_prompt import build_dim_scd2_stage_sql_prompt
from modules import generation_profiles as _gp


# ============================================================
# Input Normalizer — New format → internal format
# ============================================================
# ============================================================
# Input Format Adapter
# ============================================================

import re


def _yes_no_to_bool(v) -> bool:
    """Convert 'Yes'/'No'/'Y'/'N'/True/False/None to bool."""
    if v is None:
        return False
    if isinstance(v, bool):
        return v
    s = str(v).strip().lower()
    return s in ("yes", "y", "true", "1")


def _format_column_name(value: str) -> str:
    """
    Convert column names to snake_case:
    - lowercase
    - replace spaces/special chars with underscore
    - remove duplicate underscores
    - strip leading/trailing underscores
    """
    if value is None:
        return None

    value = str(value).strip().lower()

    # Replace non-alphanumeric characters with underscore
    value = re.sub(r"[^a-z0-9]+", "_", value)

    # Remove duplicate underscores
    value = re.sub(r"_+", "_", value)

    return value.strip("_")


def _parse_business_keys(value) -> list:
    """
    Parse the raw STTM Business_Key field into a list of cleaned,
    snake_cased business key column names.

    Examples:
        None                                              -> []
        ""                                                -> []
        "null" / "none"                                   -> []
        "policy_id"                                       -> ["policy_id"]
        "marketing_preference_id, marketing_engagement_id"
            -> ["marketing_preference_id", "marketing_engagement_id"]
        "Policy ID,  Customer Code"
            -> ["policy_id", "customer_code"]

    Notes:
        - Splits ONLY on comma — so individual key names that contain
          spaces or other punctuation are normalised as a whole token
          by _format_column_name (NOT split apart).
        - Drops empty / null-ish parts.
        - Always returns a list (possibly empty).
    """
    if value is None:
        return []

    s = str(value).strip()
    if not s or s.lower() in ("null", "none"):
        return []

    parts = s.split(",")
    cleaned = []
    seen = set()
    for p in parts:
        token = (p or "").strip()
        if not token or token.lower() in ("null", "none"):
            continue
        norm = _format_column_name(token)
        if not norm:
            continue
        if norm in seen:
            continue
        seen.add(norm)
        cleaned.append(norm)
    return cleaned


def adapt_input_format(raw_table: dict) -> dict:
    """
    Adapt new STTM input format (PascalCase + nested SourceMapping)
    into the internal flat snake_case format used by the rest of the pipeline.
    """
    if not raw_table:
        return {}

    # Map table-level fields (PascalCase → snake_case)
    table_type_raw = raw_table.get("Table_Type") or ""
    table_type_str = str(table_type_raw).strip().lower()

    # 'dimension' → 'DIM', 'fact' → 'FACT', else passthrough upper
    if table_type_str == "dimension":
        normalized_table_type = "DIM"
    elif table_type_str == "fact":
        normalized_table_type = "FACT"
    else:
        normalized_table_type = (
            str(table_type_raw).strip().upper() if table_type_raw else ""
        )

    # Derive all_source_tables from column-level SourceMapping.Source_Table
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
        "target_table": _format_column_name(raw_table.get("Target_Table")),
        "table_type": normalized_table_type,
        "description": raw_table.get("Table_Definition"),
        "source_data_vault_table": _format_column_name(
            raw_table.get("Source_Data_Vault_Table")
        ),
        "source_logical_table": _format_column_name(
            raw_table.get("Source_Logical_Table")
        ),
        "all_source_tables": [
            _format_column_name(t) for t in src_tables_set
        ],
        # CHANGE B: business_key is now ALWAYS a list of cleaned key names
        # (could be empty, single-element, or multi-element).
        "business_key": _parse_business_keys(raw_table.get("Business_Key")),
        "scd_type": raw_table.get("SCD_Type"),
        "loading_order": raw_table.get("Loading_Order"),
        "dependency": raw_table.get("Dependency"),
        "retention_type": raw_table.get("Retention_Type"),
        "retention_attribute": _format_column_name(
            raw_table.get("Retention_Attribute")
        ),
        "retention_reference_table": _format_column_name(
            raw_table.get("Retention_Reference_Table")
        ),
        "watermark_date_columns": raw_table.get("Watermark_Date_Columns"),
        "watermark_time_columns": raw_table.get("Watermark_Time_Columns"),
        "where_clause": raw_table.get("Where_Clause"),
        "contains_pii": raw_table.get("Contains_PII"),
        "database_name": _format_column_name(raw_table.get("Database_Name")),
        "schema_name": _format_column_name(raw_table.get("Schema_Name")),
        "mappings": [],
    }

    # Map column-level fields
    for cm in raw_mappings:
        cm = cm or {}
        src_map = cm.get("SourceMapping") or {}

        adapted_mapping = {
            "source_column": _format_column_name(
                src_map.get("Source_Column")
            ),
            "source_table": _format_column_name(
                src_map.get("Source_Table")
            ),
            "target_column": _format_column_name(
                cm.get("Target_Column")
            ),
            "data_type": str(cm.get("Data_Type")).lower()
            if cm.get("Data_Type")
            else None,
            "is_primary_key": _yes_no_to_bool(cm.get("Is_PK")),
            "is_foreign_key": _yes_no_to_bool(cm.get("Is_FK")),
            "transformation": src_map.get("Transformation_Logic"),
            "description": cm.get("Column_Definition"),
            "column_order": cm.get("Column_Order"),
        }

        adapted["mappings"].append(adapted_mapping)

    return adapted

# ============================================================
# Agent 5: Rule Engine — Derive helpers
# ============================================================

def clean_sttm_for_config(sttm_data: dict) -> dict:
    """Strip STTM data to only the fields needed for config generation."""
    clean = {
        "target_table": sttm_data.get("target_table"),
        "table_type": sttm_data.get("table_type"),
        "source_data_vault_table": sttm_data.get("source_data_vault_table"),
        "source_logical_table": sttm_data.get("source_logical_table"),
        "all_source_tables": sttm_data.get("all_source_tables"),
        # business_key is now a list (passthrough)
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
        }
        clean["mappings"].append(clean_mapping)

    return clean


# ============================================================
# Agent 6: STTM Transform
# ============================================================



_AUDIT_COLS = {
    "created_ts", "created_by", "updated_ts", "updated_by",
    "last_updated_ts", "last_updated_by", "effective_from_ts",
    "effective_to_ts", "record_version", "attr_hash",
    "load_date", "load_ts", "insert_ts",
}

_SYNTHETIC_PATTERNS = [
    "current_timestamp", "current_date", "sysdate", "now()",
    "uuid", "md5(", "sha(", "hash(", "nextval", "sequence",
]


def _is_real_value(v) -> bool:
    """True if value is not None and not the string 'null'/'none'/''."""
    if v is None:
        return False
    s = str(v).strip().lower()
    return s not in ("", "null", "none")


def transform_sttm_to_config_json(sttm_data: dict) -> tuple:
    """
    Convert cleaned STTM into a structured config dict and a list
    of non-null source columns.

    Returns:
        (config_dict, non_null_source_columns)
    """
    cleaned = clean_sttm_for_config(sttm_data or {})

    target_table = cleaned.get("target_table")
    target_table_str = (
        str(target_table).strip() if target_table is not None else ""
    )
    name = target_table_str.lower() if target_table_str else ""

    # Business Vault treats the (PK) business key as a persisted attribute
    # and detects audit columns by concept (naming-agnostic). Dimensional
    # keeps its original PK-skip + static audit-set behaviour.
    is_bv = _gp.get_target_model() == _gp.TARGET_BUSINESS_VAULT

    mappings = cleaned.get("mappings") or []
    columns = []
    primary_key_col = None

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
        }
        columns.append(col_entry)
        if col_entry["is_primary_key"] and not primary_key_col:
            tc = col_entry.get("target_column")
            if tc is not None:
                primary_key_col = str(tc).strip().lower()

    has_transformations = any(
        c.get("transformation") is not None
        and str(c.get("transformation")).strip() != ""
        for c in columns
    )

    # Filter out 'null'-string and None entries from source_tables
    raw_source_tables = cleaned.get("all_source_tables") or []
    source_tables = [t for t in raw_source_tables if _is_real_value(t)]

    config_dict = {
        "name": name,
        "table_type": cleaned.get("table_type"),
        "target_table": target_table,
        "source_tables": source_tables,
        "source_data_vault_table": cleaned.get("source_data_vault_table"),
        "source_logical_table": cleaned.get("source_logical_table"),
        # business_key is a list (possibly empty)
        "business_key": cleaned.get("business_key"),
        "scd_type": cleaned.get("scd_type"),
        "primary_key": primary_key_col,
        "columns": columns,
        "has_transformations": has_transformations,
    }

    non_null_source_columns = []
    seen_targets = set()

    # Determine if this table has ANY source hint (table-level)
    has_table_level_source = (
        len(source_tables) > 0
        or _is_real_value(cleaned.get("source_data_vault_table"))
        or _is_real_value(cleaned.get("source_logical_table"))
    )

    for c in columns:
        source_table = c.get("source_table")
        source_column = c.get("source_column")
        target_column = c.get("target_column")
        is_pk = bool(c.get("is_primary_key"))
        is_fk = bool(c.get("is_foreign_key"))
        transformation = c.get("transformation")

        if target_column is None:
            continue

        target_norm = str(target_column).strip().lower()
        if not target_norm:
            continue

        # Skip the dimension's own primary key and ordinary foreign keys,
        # BUT keep foreign surrogate keys (e.g. insured_object_sk,
        # geography_sk, channel_sk). These resolve to another dimension's
        # surrogate key, are projected in the stage SQL, and must be
        # persisted — so they belong in attribute_cols / insert_cols.
        is_foreign_sk = is_fk and target_norm.endswith("_sk")
        # Business Vault: the PK is the business key (e.g. global_*_id) and
        # MUST be persisted, so only ordinary FKs are skipped. Dimensional:
        # skip both PK (surrogate) and ordinary FK, as before.
        if is_bv:
            if is_fk and not is_foreign_sk:
                continue
        elif (is_pk or is_fk) and not is_foreign_sk:
            continue

        # Skip standard audit columns
        # if target_norm in _AUDIT_COLS:
        #     continue

        # Skip standard audit columns (target-model specific: Dimensional
        # uses the original static set; Business Vault detects audit columns
        # by concept — naming-agnostic — so renamed cols like current_flag /
        # load_ts are still excluded from attribute_cols).
        if is_bv:
            if _gp.bv_is_audit_col(target_norm):
                continue
        elif target_norm in _gp.get_profile().audit_cols:
            continue

        # Skip purely synthetic columns (derived without source).
        # Foreign surrogate keys are exempt: they have a real source
        # (another dimension's SK) and their transformation may legitimately
        # contain hash/join expressions like md5(...) in the JOIN predicate.
        trans_str = (
            str(transformation).strip().lower()
            if transformation is not None
            else ""
        )
        if trans_str and not is_foreign_sk:
            is_synthetic = any(pat in trans_str for pat in _SYNTHETIC_PATTERNS)
            if not is_synthetic and trans_str in (
                "null", "cast(null", "cast(null as"
            ):
                is_synthetic = True
            if is_synthetic:
                continue

        # Determine if column comes from source data:
        # - Either column-level source info is present (source_table or source_column)
        # - OR table-level source info exists (and column isn't pk/fk/audit/synthetic)
        column_has_source_info = (
            _is_real_value(source_table) or _is_real_value(source_column)
        )

        if not column_has_source_info and not has_table_level_source:
            # No source info at all — truly static column
            continue

        # Dedupe
        if target_norm in seen_targets:
            continue
        seen_targets.add(target_norm)
        non_null_source_columns.append(target_norm)

    print(f"Non-null source columns: {non_null_source_columns}")

    return config_dict, non_null_source_columns


# ============================================================
# Agent 7: Stage SQL Prompt + Cleaner
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

    # ===== CHANGE 2a: Pass 5 — Strip f-string wrappers around table references =====
    # Handles: f"{catalog_name}.{schema_name}.X", f'{catalog_name}.{schema_name}.X',
    # malformed f"{catalog_name}{schema_name}.X" (missing dot), and bare f"X"/f'X'.
    sql = re.sub(
        r'f"(\{catalog_name\}\.?\{schema_name\}\.[A-Za-z_][A-Za-z0-9_]*)"',
        r'\1',
        sql,
    )
    sql = re.sub(
        r"f'(\{catalog_name\}\.?\{schema_name\}\.[A-Za-z_][A-Za-z0-9_]*)'",
        r'\1',
        sql,
    )
    sql = re.sub(r'f"([A-Za-z_][A-Za-z0-9_.]*)"', r'\1', sql)
    sql = re.sub(r"f'([A-Za-z_][A-Za-z0-9_.]*)'", r'\1', sql)
    # ===== END CHANGE 2a =====

    # ===== CHANGE 8: NEW Pass 7 — Schema-name split (vault vs gold) =====
    # Rewrites any LLM-emitted generic {schema_name} into the appropriate
    # vault/gold placeholder, based on the table prefix that follows.
    # Order matters: specific prefix matches first (7a, 7b), defensive
    # catch-all last (7c). Scope is restricted to {schema_name}.<TABLE_PREFIX>
    # patterns; standalone {schema_name} occurrences (which shouldn't exist)
    # are left untouched until the catch-all.

    # Pass 7a: Vault tables (HUB_*, SAT_*, LINK_*) — case-insensitive
    sql = re.sub(
        r'\{schema_name\}(\.(?:HUB_|SAT_|LINK_))',
        r'{vault_schema_name}\1',
        sql,
        flags=re.IGNORECASE,
    )
    # Pass 7b: Dimension tables (DIM_*) — case-insensitive
    sql = re.sub(
        r'\{schema_name\}(\.DIM_)',
        r'{gold_schema_name}\1',
        sql,
        flags=re.IGNORECASE,
    )
    # Pass 7c: Defensive catch-all — any remaining {schema_name}.<table>
    # defaults to vault (vault sources are the dominant case).
    sql = re.sub(
        r'\{schema_name\}(\.[A-Za-z_])',
        r'{vault_schema_name}\1',
        sql,
    )
    # ===== END CHANGE 8 =====

    # ===== CHANGE 2b: Pass 6 — Strip banned columns from any SELECT projection at any CTE level =====
    _BANNED_COLS = [
        "attr_hash", "created_by", "created_ts",
        "last_updated_by", "last_updated_ts", "record_version",
        "load_date", "load_ts", "insert_ts",
    ]
    _ALLOWED_ALIASES = {"effective_from_ts", "effective_to_ts"}
    banned_pattern = "|".join(_BANNED_COLS)
    # Matches lines like:
    #   sp.created_by,    |   created_by,    |   sp.attr_hash    |   attr_hash
    #   d.created_ts AS CREATED_TS,   |   created_ts AS created_ts,
    line_re = re.compile(
        r'^\s*(?:[A-Za-z_][A-Za-z0-9_]*\s*\.\s*)?(' + banned_pattern +
        r')(?:\s+AS\s+([A-Za-z_][A-Za-z0-9_]*))?\s*,?\s*$',
        re.IGNORECASE,
    )

    cleaned_lines = []
    for line in sql.split("\n"):
        m = line_re.match(line)
        if m:
            alias = (m.group(2) or "").strip().lower()
            # Safeguard: keep lines aliased to allowed names (e.g. ... AS effective_from_ts)
            if alias in _ALLOWED_ALIASES:
                cleaned_lines.append(line)
                continue
            # Safeguard: keep lines that are inside an expression (have '(' before col)
            if "(" in line:
                cleaned_lines.append(line)
                continue
            # Drop this line (banned column projection)
            continue
        cleaned_lines.append(line)
    sql = "\n".join(cleaned_lines)

    # ---- Trailing-comma cleanup (orphaned commas left after line removal) ----
    sql = re.sub(r',(\s*\n\s*FROM\b)', r'\1', sql, flags=re.IGNORECASE)
    sql = re.sub(r',(\s*\n\s*\))', r'\1', sql)
    # ===== END CHANGE 2b =====

    # ===== CHANGE 9: NEW Pass 9 — Convert single-brace placeholders to double-brace =====
    # The LLM consistently emits ${watermark_col} and ${watermark_value} with
    # single braces. When the generated stage_sql is wrapped inside the output
    # config file's f"""...""" block, single braces are interpreted as Python
    # f-string interpolation slots, causing NameError or wrong substitution.
    # Doubling the braces here makes the output literal ${watermark_col} and
    # ${watermark_value} after f-string evaluation — which is what Databricks
    # widget syntax requires.
    #
    # Idempotent regex (negative lookbehind/lookahead): only matches the
    # single-brace form. Already-doubled ${{watermark_col}} / ${{watermark_value}}
    # are left untouched, so re-running this pass is safe.
    sql = re.sub(
        r'(?<!\{)\$\{watermark_col\}(?!\})',
        '${{watermark_col}}',
        sql,
    )
    sql = re.sub(
        r'(?<!\{)\$\{watermark_value\}(?!\})',
        '${{watermark_value}}',
        sql,
    )
    # ===== END CHANGE 9 =====

    return sql.strip()


# ============================================================
# Agent 8: Stage SQL LLM Call
# ============================================================

def generate_stage_sql(config_json: dict, model_name: str = "openai", platform: str = "Databricks", sql_dialect: str = None) -> str:
    """Build prompt from config_json, call LLM, clean the result.

    `model_name` is an OPTIONAL pass-through so the new Streamlit UI can
    select a different backend (claude / gpt-5 / …). Default 'openai'
    preserves the original behaviour byte-for-byte.
    """
    prompt_text = build_dim_scd2_stage_sql_prompt(config_json, platform=platform, sql_dialect=sql_dialect)
    # For non-Dimensional targets (Business Vault), swap the SCD-2 audit
    # column names in the prompt (effective_from_ts -> effective_from,
    # effective_to_ts -> effective_to, record_version -> current_active_flag).
    # No-op for Dimensional -> prompt stays byte-identical.
    prompt_text = _gp.apply_audit_renames(prompt_text)
    # Business Vault only: append source-fidelity rules (preserve every
    # WHERE/record_source/join predicate; prefer per-source CTE structure).
    # No-op for Dimensional.
    prompt_text = _gp.append_bv_fidelity_rules(prompt_text)
    raw_sql = convert_with_llm(prompt_text, model_name=model_name)
    return clean_llm_sql(raw_sql)


# ============================================================
# Agent 9: Config Assembly + Formatter
# ============================================================

def assemble_final_configs(
    config_json: dict,
    stage_sql: str,
    non_null_source_columns: list,
) -> dict:
    """Assemble the final config dictionary from all computed pieces."""
    name = config_json.get("name", "")
    target_table = config_json.get("target_table", "")

    # CHANGE D: business_key is now a LIST in config_json (after adapt_input_format).
    # Decide the value type to store under `business_key_col`:
    #   - empty list  -> ""              (preserves existing behaviour: empty string)
    #   - 1 element   -> "<key>"         (preserves existing single-string format)
    #   - 2+ elements -> ["<a>", "<b>"]  (new list format for composite keys)
    # The dict key NAME stays as "business_key_col" (singular) — unchanged.
    bk_list = config_json.get("business_key") or []
    primary_key = config_json.get("primary_key", "")

    if not bk_list:
        # Fallback to primary_key for backward compatibility
        business_key_col_value = primary_key if primary_key else ""
    elif len(bk_list) == 1:
        business_key_col_value = bk_list[0]
    else:
        business_key_col_value = list(bk_list)

    # ===== CHANGE 3: Plumb scd_type from config_json into the assembled dict =====
    # Preserve None as None (not coerced to empty string) per Lock 1.
    scd_type = config_json.get("scd_type")
    # ===== END CHANGE 3 =====

    # Target-model specific column names + audit tail. Dimensional keeps
    # the original literals (effective_from_ts / record_version + full
    # audit tail); Business Vault uses effective_from / current_active_flag
    # + its smaller tail. watermark_col is shared ("load_date").
    _profile = _gp.get_profile()
    is_bv = _profile.target_model == _gp.TARGET_BUSINESS_VAULT
    watermark_col = "load_date"

    # All target column names from the mapping (order preserved) — used for
    # concept-based BV audit/flag/hash detection.
    all_target_names = [
        str(c.get("target_column")).strip().lower()
        for c in (config_json.get("columns") or [])
        if c.get("target_column")
    ]

    # effective_from / record-version(flag) column NAMES. Business Vault
    # resolves them from the actual mapping (naming-agnostic); Dimensional
    # keeps its original literals.
    if is_bv:
        effective_from_col = _gp.bv_effective_from_col(all_target_names)
        record_version_col = _gp.bv_current_flag_col(all_target_names)
    else:
        effective_from_col = _profile.effective_from_col
        record_version_col = _profile.record_version_col

    seen = set()
    attribute_cols = []
    for col in non_null_source_columns:
        if col is None:
            continue
        col_str = str(col).strip().lower()
        if col_str and col_str not in seen:
            seen.add(col_str)
            attribute_cols.append(col_str)

    # insert_cols = list(attribute_cols) + [
    #     "attr_hash",
    #     "effective_from_ts",
    #     "effective_to_ts",
    #     "record_version",
    #     "created_by",
    #     "created_ts",
    #     "last_updated_by",
    #     "last_updated_ts",
    # ]
    # insert_cols audit tail. Business Vault builds it from the audit columns
    # ACTUALLY present in the mapping (concept-detected, in mapping order) so
    # no hardcoded literal (e.g. current_active_flag/load_timestamp) is
    # injected when the product renamed it. Dimensional keeps its static tail.
    if is_bv:
        audit_tail = _gp.bv_audit_columns(all_target_names)
    else:
        audit_tail = list(_profile.scd2_insert_audit_tail)
    insert_cols = list(attribute_cols) + list(audit_tail)
    insert_cols = [str(c) for c in insert_cols]

    result = {
        "name": name,
        "target_table": target_table,
        "business_key_col": business_key_col_value,
        # ===== CHANGE 3 (cont.): Add scd_type to returned dict =====
        # Positioned right after business_key_col, before watermark_col,
        # for consistency with the output file's key ordering.
        "scd_type": scd_type,
        # ===== END CHANGE 3 (cont.) =====
        "watermark_col": watermark_col,
        "effective_from_col": effective_from_col,
        "record_version_col": record_version_col,
        # Config-dict KEY name for the flag entry: "record_version_col"
        # (Dimensional) or "current_flag_col" (Business Vault).
        "record_version_key": _profile.record_version_key,
        "stage_sql": stage_sql,
        "attribute_cols": attribute_cols,
        "insert_cols": insert_cols,
    }

    # Business-Vault-only extra keys (absent for Dimensional so its output
    # stays byte-identical).
    if is_bv:
        if _profile.modelling_pattern:
            result["modelling_pattern"] = _profile.modelling_pattern
        # Master hash column: master_*_hash_key.
        hash_col = next(
            (n for n in all_target_names
             if re.match(r"^master_.*_hash_key$", n)),
            None,
        )
        if hash_col:
            result["hash_col"] = hash_col
        bare = str(target_table).split(".")[-1].lower() if target_table else name
        result["object_id"] = f"{bare}_3"

    return result


def format_config_as_python(config: dict, variable_name: str) -> str:
    """Format the config dict as a Python source string for output."""
    name = str(config.get("name", ""))
    target_table = str(config.get("target_table", ""))

    # CHANGE E: business_key_col can be a list (composite key) OR a string
    # (single key / empty). Read as-is — do NOT coerce to string upfront.
    business_key_col_value = config.get("business_key_col", "")

    watermark_col = str(config.get("watermark_col", "load_date"))
    effective_from_col = str(config.get("effective_from_col", "effective_from_ts"))
    record_version_col = str(config.get("record_version_col", "record_version"))
    # Flag key name is target-model specific: "record_version_col"
    # (Dimensional) or "current_flag_col" (Business Vault).
    record_version_key = str(config.get("record_version_key", "record_version_col"))
    # Business-Vault-only extra keys (None/absent for Dimensional).
    modelling_pattern = config.get("modelling_pattern")
    hash_col = config.get("hash_col")
    object_id = config.get("object_id")

    # ===== CHANGE 2 (a): Read scd_type from config — preserve None per Lock 1 =====
    # Do NOT coerce to string here; we want to render `null` (Python None)
    # for null inputs and `"<value>"` for string inputs.
    scd_type_val = config.get("scd_type")
    # ===== END CHANGE 2 (a) =====

    raw_sql = str(config.get("stage_sql", ""))
    formatted_sql = raw_sql.replace("\\n", "\n")

    attribute_cols = [str(c) for c in config.get("attribute_cols", [])]
    insert_cols = [str(c) for c in config.get("insert_cols", [])]

    # Extract bare table name from possibly-qualified target_table
    parts = target_table.split(".")
    if len(parts) == 3:
        table_name = parts[2]
    elif len(parts) == 2:
        table_name = parts[1]
    else:
        table_name = target_table

    lines = []
    lines.append(f'{variable_name}_CFG = {{')
    # Business Vault emits "modelling_pattern" as the first key.
    if modelling_pattern:
        lines.append(f'    "modelling_pattern": "{modelling_pattern}",')
    lines.append(f'    "name": "{name}",')
    # ===== CHANGE 1: target_table schema rename — schema_name → gold_schema_name =====
    lines.append(
        f'    "target_table": '
        f'f"{{catalog_name}}.{{gold_schema_name}}.{table_name}",'
    )
    # ===== END CHANGE 1 =====

    # CHANGE E (cont.): Emit business_key_col conditionally based on type.
    # - list  -> Python list literal: ["a","b"]
    # - str   -> quoted string:        "policy_id"
    # Key name stays "business_key_col" (singular) in BOTH cases.
    if isinstance(business_key_col_value, list):
        joined = ",".join(f'"{str(c)}"' for c in business_key_col_value)
        lines.append(f'    "business_key_col": [{joined}],')
    else:
        bk_str = str(business_key_col_value)
        lines.append(f'    "business_key_col": "{bk_str}",')

    # ===== CHANGE 2 (b): Emit scd_type line right after business_key_col =====
    # If scd_type is None → render literal `null` (unquoted).
    # If scd_type is a string → render `"<value>"` (quoted).
    if scd_type_val is None:
        lines.append(f'    "scd_type": null,')
    else:
        lines.append(f'    "scd_type": "{scd_type_val}",')
    # ===== END CHANGE 2 (b) =====
    lines.append(f'    "watermark_col": "{watermark_col}",')
    lines.append(f'    "effective_from_col": "{effective_from_col}",')
    # Flag entry under its target-model-specific key name.
    lines.append(f'    "{record_version_key}": "{record_version_col}",')
    # Business-Vault-only keys, positioned before stage_sql.
    if hash_col:
        lines.append(f'    "hash_col": "{hash_col}",')
    if object_id:
        lines.append(f'    "object_id": "{object_id}",')
    lines.append("")
    lines.append('    "stage_sql": f"""')
    for line in formatted_sql.split("\n"):
        lines.append(f"        {line}")
    lines.append('    """,')
    lines.append("")
    lines.append('    "attribute_cols": [')
    for col in attribute_cols:
        lines.append(f'        "{col}",')
    lines.append("    ],")
    lines.append("")
    lines.append('    "insert_cols": [')
    for col in insert_cols:
        lines.append(f'        "{col}",')
    lines.append("    ]")
    lines.append("}")

    return "\n".join(lines)


# ============================================================
# Master function: Generate config for one table
# ============================================================

def generate_config(sttm_data: dict, model_name: str = "openai", platform: str = "Databricks", sql_dialect: str = None) -> dict:
    """Generate ETL config for a single table from its STTM data.

    `model_name` is forwarded to the LLM call when stage SQL is needed.
    """
    config_json, non_null_source_columns = transform_sttm_to_config_json(
        sttm_data
    )

    # Gather ALL possible source hints
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
            f"source tables at all (truly static dimension)."
        )
        stage_sql = (
            "-- No source tables defined. "
            "This dimension is statically populated."
        )
    else:
        # Pass full mapping context to LLM, even if per-column source_table is null
        stage_sql = generate_stage_sql(config_json, model_name=model_name, platform=platform, sql_dialect=sql_dialect)

    final_config = assemble_final_configs(
        config_json, stage_sql, non_null_source_columns
    )
    return final_config


# ============================================================
# Main execution: Process all DIM tables
# ============================================================
def run_all(
    input_path: str,
    output_dir: str,
    model_name: str = "openai",
    platform: str = "Databricks",
    sql_dialect: str = None,
) -> dict:
    """Read input JSON, process all DIM tables, write config files.

    Optional `model_name` is forwarded to every per-table LLM call.
    Defaults to 'openai' so existing callers see no behavioural change.
    """

    if not os.path.exists(input_path):
        print(f"ERROR: Input file not found: {input_path}")
        print(f"  Current directory: {os.getcwd()}")
        sys.exit(1)

    with open(input_path, "r", encoding="utf-8") as f:
        raw = json.load(f)

    # ── Robust unwrap: handle list, single dict, or dict-with-wrapper-key ──
    if isinstance(raw, list):
        all_tables = raw
    elif isinstance(raw, dict):
        # Try common wrapper keys (case-insensitive)
        wrapper_keys = ["tables", "Tables", "sttm", "STTM", "data", "Data"]
        wrapped = None
        for k in wrapper_keys:
            if k in raw and isinstance(raw[k], list):
                wrapped = raw[k]
                break
        if wrapped is not None:
            all_tables = wrapped
        else:
            # Single-table dict
            all_tables = [raw]
    else:
        print(f"ERROR: Unexpected JSON root type: {type(raw).__name__}")
        sys.exit(1)

    print(f"DEBUG: Loaded {len(all_tables)} raw table(s) from input")

    # ── Adapt every raw input row into the internal format ──
    adapted_tables = [adapt_input_format(t) for t in all_tables if t]

    # ── DEBUG: show what each table looks like after adapting ──
    print(f"DEBUG: Adapted {len(adapted_tables)} table(s):")
    for i, t in enumerate(adapted_tables):
        print(
            f"  [{i}] target_table={t.get('target_table')!r}, "
            f"table_type={t.get('table_type')!r}"
        )

    # target_tables = [
    #     t for t in adapted_tables
    #     if str(t.get("table_type", "")).upper() == "DIM"
    # ]

    # Target-model aware selection. Dimensional selects DIM tables (the
    # input JSON is already SCD-2 filtered by SttmFilterStage). Business
    # Vault master tables are not typed "dimension", so select by SCD
    # type == 2 (the JSON is likewise already SCD-2 filtered).
    if _gp.get_target_model() == _gp.TARGET_BUSINESS_VAULT:
        target_tables = [
            t for t in adapted_tables
            if str(t.get("scd_type")).strip() == "2"
        ]
    else:
        target_tables = [
            t for t in adapted_tables
            if str(t.get("table_type", "")).upper() == "DIM"
        ]

    if not target_tables:
        print("No SCD-2 tables found in input")
        return {
            "success_count": 0,
            "failed_count": 0,
            "total_count": 0,
            "output_files": [],
            "failed_tables": [],
        }

    total = len(target_tables)
    print(f"\nProcessing {total} DIM table(s)...\n")

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
#         else "input/erwin_customer360_final_mapping_file_13052026.json"
#     )
#     output_directory = (
#         sys.argv[2]
#         if len(sys.argv) > 2
#         else "output_static_new_v2/configs/"
#     )

#     print("=" * 55)
#     print("  Config Generator — DIM Tables")
#     print(f"  Input:  {input_file}")
#     print(f"  Output: {output_directory}")
#     print("=" * 55)
#     print()

#     result = run_all(input_file, output_directory)

#     if result["failed_count"] > 0:
#         sys.exit(1)
#     sys.exit(0)