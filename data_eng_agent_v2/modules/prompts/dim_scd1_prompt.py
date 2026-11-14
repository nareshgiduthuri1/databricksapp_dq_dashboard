"""Platform-aware SCD-1 dimension staging-SQL prompt builder."""

from __future__ import annotations

import json

from modules.prompts._profiles import stage_sql_platform_rules, apply_dialect_tokens


def build_dim_scd1_stage_sql_prompt(sttm_data: dict, attribute_cols: list,
                                    business_keys: list,
                                    platform: str = "Databricks",
                                    sql_dialect: str = "Spark SQL") -> str:
    """Build LLM prompt for SCD-1 staging SQL generation."""
    config_str = json.dumps(sttm_data, indent=2, default=str)
    target_table = sttm_data.get("target_table", "")
    business_key = (
        sttm_data.get("business_key")
        or (business_keys[0] if business_keys else "")
    )
    attr_cols_csv = ", ".join(attribute_cols)
    bk_cols_csv = ", ".join(business_keys) if business_keys else business_key

    platform = platform or "Databricks"
    sql_dialect = sql_dialect or "Spark SQL"
    platform_rules = stage_sql_platform_rules(platform, sql_dialect)
    prompt = f"""You are an expert {platform} SQL ({sql_dialect}) engineer.

PLATFORM-SPECIFIC SQL RULES (the generated SQL MUST be valid for {platform} / {sql_dialect}):
{platform_rules}

Platform: {platform}
SQL dialect: {sql_dialect}
Pattern: SCD Type 1 (overwrite-on-change incremental staging)

Objective:
- Write a STAGING SELECT query (CTE chain) for the SCD-1 dimension target: {target_table}
- The query produces a deduplicated incremental dataset for the downstream MERGE.
- For SCD-1, NO history is tracked. NO effective_from_ts, NO effective_to_ts,
  NO record_version.

Required output columns (in this order):
- Business key column(s):  {bk_cols_csv}
- Attribute columns:       {attr_cols_csv}
- attr_hash               (SHA2(CONCAT_WS('||', <attribute cols cast to string, COALESCEd>), 256))

SQL requirements:
- Return RAW SQL ONLY: no markdown, no code fences, no comments, no explanation.
- The SQL must start with WITH or SELECT.
- Use idiomatic {sql_dialect} with CTEs.
- The query will later be embedded inside a Python f-string that already has
  {{watermark_ts}} substituted at runtime — so use the literal token
  TIMESTAMP('{{watermark_ts}}') in the WHERE clause as shown below.

Schema placeholder rules (CRITICAL):
- All Data Vault tables (HUB_*, SAT_*, LINK_*) MUST use:
    {{catalog_name}}.{{vault_schema_name}}.<table_name>
- All Dimension tables (DIM_*) referenced as join sources MUST use:
    {{catalog_name}}.{{gold_schema_name}}.<table_name>
- Use placeholders DIRECTLY — NOT wrapped in f"..." or quoted.
- Do NOT use generic {{schema_name}}.
- Do NOT hardcode catalog or schema names.

Mapping rules:
- Use the provided STTM JSON as the single source of truth for joins, filters,
  and column-level transformation logic.
- Apply every transformation expression exactly as defined in the
  `transformation` field, only adjusting syntax to {sql_dialect}.
- Build the JOIN graph from `source_table` per column plus transformation hints.

WATERMARK / INCREMENTAL FILTER:
- Qualify the watermark column with the SAT alias (NEVER the HUB alias).
- Single-source case (one SAT in the join graph):
    WHERE <sat_alias>.load_date > TIMESTAMP('{{watermark_ts}}')
- Multi-sat case:
    WHERE greatest(COALESCE(<sat_a>.load_date, DATE('1900-01-01')),
                   COALESCE(<sat_b>.load_date, DATE('1900-01-01')),
                   ... ) > TIMESTAMP('{{watermark_ts}}')

DEDUPLICATION:
- Use ROW_NUMBER() OVER (PARTITION BY {bk_cols_csv}
                         ORDER BY <sat_alias>.load_date DESC) AS rn
- Filter rn = 1 in the final SELECT.

ATTR_HASH (CRITICAL):
- The final SELECT MUST compute:
    SHA2(
      CONCAT_WS('||',
        COALESCE(CAST(<attribute_col_1> AS STRING), ''),
        COALESCE(CAST(<attribute_col_2> AS STRING), ''),
        ...
      ),
      256
    ) AS attr_hash
- Include EVERY attribute column listed above in the hash, in the same order.

FORBIDDEN COLUMNS in any projection:
    created_by, created_ts, last_updated_by, last_updated_ts,
    record_version, effective_from_ts, effective_to_ts,
    load_date, load_ts, insert_ts, attr_hash (as raw source col)
EXCEPTIONS:
- attr_hash MUST be the COMPUTED expression in the final SELECT.
- load_date MAY appear inside WHERE clauses and ROW_NUMBER ORDER BY only.

STRUCTURAL SKELETON (illustration only — adapt to actual mappings):

  WITH src AS (
    SELECT
      <business_key_columns>,
      <attribute columns from sources, with transformations applied>,
      sa.load_date AS watermark_col
    FROM {{catalog_name}}.{{vault_schema_name}}.<HUB_TABLE> hu
    LEFT JOIN {{catalog_name}}.{{vault_schema_name}}.<SAT_TABLE> sa
      ON sa.<hash_key> = hu.<hash_key>
    WHERE sa.load_date > TIMESTAMP('{{watermark_ts}}')
  ),
  dedup AS (
    SELECT
      <business_key_columns>,
      <attribute columns>,
      ROW_NUMBER() OVER (
        PARTITION BY {bk_cols_csv}
        ORDER BY watermark_col DESC
      ) AS rn
    FROM src
  )
  SELECT
    <business_key_columns>,
    <attribute columns>,
    SHA2(
      CONCAT_WS('||',
        COALESCE(CAST(<attribute_col_1> AS STRING), ''),
        COALESCE(CAST(<attribute_col_2> AS STRING), ''),
        ...
      ),
      256
    ) AS attr_hash
  FROM dedup
  WHERE rn = 1

STTM JSON:
{sttm_data}

Now output ONLY the final {sql_dialect} query, starting with WITH or SELECT.
"""
    return apply_dialect_tokens(prompt, platform)
