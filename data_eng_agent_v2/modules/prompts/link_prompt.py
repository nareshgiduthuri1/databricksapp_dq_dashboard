"""Platform-aware Raw-Data-Vault LINK build-SQL prompt builder.

Config-driven: static LINK conventions + injected `config_json`.
"""

from __future__ import annotations

import json

from modules.prompts._profiles import stage_sql_platform_rules, apply_dialect_tokens


def build_link_build_sql_prompt(
    config_json: dict,
    platform: str = "Databricks",
    sql_dialect: str = "Spark SQL",
) -> str:
    """Build the LLM prompt that generates a LINK table's build_sql."""
    config_str = json.dumps(config_json, indent=2, default=str)
    target_table = config_json.get("target_table", "")
    source_tables = config_json.get("source_tables") or []
    filter_rule = config_json.get("filter_rule")

    platform = platform or "Databricks"
    sql_dialect = sql_dialect or "Spark SQL"
    platform_rules = stage_sql_platform_rules(platform, sql_dialect)

    prompt = f"""You are an expert {platform} SQL ({sql_dialect}) engineer building a Raw Data Vault.

PLATFORM-SPECIFIC SQL RULES (the generated SQL MUST be valid for {platform} / {sql_dialect}):
{platform_rules}

============================================================================
OBJECTIVE
============================================================================
Write the build (staging) SELECT for the LINK table: {target_table}

A LINK captures the association between two (or more) hubs. Its own hash key
is derived from the parent hub hash keys. Use `config_json` (below) as the
SINGLE SOURCE OF TRUTH for every column, key, source table, transformation and
filter. Do NOT invent columns or joins.

============================================================================
LINK COLUMN CONVENTIONS
============================================================================
config_json.columns contains: the LINK hash key (is_pk = true), the parent hub
hash keys (is_fk = true), load_date, and usually record_source.

Build the SQL as a `combined` CTE, then a final SELECT — EXACTLY this shape:

  WITH combined AS (
    SELECT
      md5(CONCAT(<hubA_business_key_src>, origin_sys)) AS <hubA_hash_key>,
      md5(CONCAT(<hubB_business_key_src>, origin_sys)) AS <hubB_hash_key>,
      pull_ts,
      origin_sys
    FROM <source> [WHERE <this source's filter condition>]
    -- multiple sources: UNION ALL one such SELECT per source
  )
  SELECT
    md5(CONCAT(<hubA_hash_key>, <hubB_hash_key>, origin_sys)) AS <link_hash_key>,
    CAST(pull_ts AS timestamp) AS load_date,
    origin_sys AS record_source,
    <hubA_hash_key>,
    <hubB_hash_key>
  FROM combined

Rules:
- Translate every `HASH(a, b, ...)` / `HASH(CONCAT(a, b))` into md5(CONCAT(a, b, ...)).
  The LINK hash key concatenates the parent hub hash keys (and origin_sys)
  exactly as its transformation specifies.
- Project each FK hub hash key using its own transformation from config_json.
- record_source: apply its transformation (e.g. COALESCE(origin_sys, origin_sys))
  or `origin_sys AS record_source`.
- load_date: CAST(pull_ts AS timestamp) AS load_date.

============================================================================
FORBIDDEN COLUMNS (CRITICAL — these violate the target DDL)
============================================================================
- Project ONLY the target columns in config_json.columns.
- NEVER emit: source_tbl_name, target_table AS source_tbl_name,
  etl_load_timestamp, source_load_timestamp_col, load_ts.
- The `combined` CTE must carry ONLY the parent hub hash keys, pull_ts and
  origin_sys — nothing else. Only pull_ts is used for load_date (cast in the
  final SELECT).

============================================================================
FROM / MULTI-SOURCE RULES
============================================================================
- Source tables: {source_tables}
- Single source: build the `combined` CTE from that one source.
- Multiple sources: within `combined`, one SELECT per source combined with
  `UNION ALL` (same output columns/order), then the final SELECT reads combined.

============================================================================
FILTER RULE (per-source WHERE conditions)
============================================================================
filter_rule for this table:
{filter_rule if filter_rule else "(none)"}

- If filter_rule is empty/(none), do NOT add any WHERE clause.
- filter_rule may contain per-source conditions prefixed with a source-system
  label and colon, e.g. `CRM: party_kind="Legal"` / `SAP: person_type="Legal"`.
- Apply each labeled condition as a WHERE clause ONLY on the `combined` SELECT
  reading the matching source table (CRM -> crm_* table, SAP -> sap_* table).
  Use single quotes for string literals, e.g. WHERE party_kind = 'Legal'.
- A single unlabeled condition applies to every source SELECT.
- Do NOT invent conditions that are not present in filter_rule.

============================================================================
OUTPUT REQUIREMENTS
============================================================================
- Return RAW SQL ONLY: no markdown, no code fences, no comments, no explanation.
- The SQL MUST start with WITH (or SELECT if no CTE is needed).
- Use the source table and column names exactly as in config_json.
- Do NOT hardcode catalog/schema; reference source tables by their bare name.

config_json:
{config_str}

Now output ONLY the final {sql_dialect} build SQL.
"""
    return apply_dialect_tokens(prompt, platform)
