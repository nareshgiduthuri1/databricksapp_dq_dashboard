"""Platform-aware Raw-Data-Vault HUB build-SQL prompt builder.

Config-driven (same pattern as the dimensional/fact prompts): a static
instruction template that encodes the Data-Vault HUB conventions, with the
table-specific mapping injected as `config_json` (the single source of
truth for columns, keys, source tables, transformations and filters).
"""

from __future__ import annotations

import json

from modules.prompts._profiles import stage_sql_platform_rules, apply_dialect_tokens


def build_hub_build_sql_prompt(
    config_json: dict,
    platform: str = "Databricks",
    sql_dialect: str = "Spark SQL",
) -> str:
    """Build the LLM prompt that generates a HUB table's build_sql."""
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
Write the build (staging) SELECT for the HUB table: {target_table}

A HUB row is uniquely identified by its business key. Produce ONE row per
business key from the source(s). Use `config_json` (below) as the SINGLE
SOURCE OF TRUTH for every column, key, source table, transformation and
filter. Do NOT invent columns or joins.

============================================================================
HUB COLUMN CONVENTIONS
============================================================================
Project EXACTLY the columns in config_json.columns (nothing else):

1. HASH KEY (the column with is_pk = true): build it as
       md5(CONCAT(<business_key_source_col>, origin_sys)) AS <target_column>
   - Translate any `HASH(a, b, ...)` transformation into md5(CONCAT(a, b, ...)).
2. BUSINESS KEY column (non-key attribute, e.g. account_id):
       <source_column> AS <target_column>
3. record_source column:
       origin_sys AS record_source
4. load_date column: project it from its MAPPED source column (the load/pull
   timestamp, which is pull_ts) as:
       CAST(pull_ts AS timestamp) AS load_date

Apply each column's `transformation` exactly ("Direct one-to-one mapping"
means project source_column directly under its target_column alias).

============================================================================
FORBIDDEN COLUMNS (CRITICAL — these violate the target DDL)
============================================================================
- Do NOT project any column that is not a target column in config_json.columns.
- NEVER emit: source_tbl_name, target_table AS source_tbl_name,
  etl_load_timestamp, source_load_timestamp_col, load_ts.
- Only pull_ts is used for load_date (cast to timestamp).

============================================================================
FROM / MULTI-SOURCE RULES
============================================================================
- Source tables: {source_tables}
- Single source: SELECT ... FROM <source>.
- Multiple sources: one SELECT per source combined with `UNION ALL`,
  projecting the SAME output column list/order from each source (mapping each
  source's own columns per config_json).

============================================================================
FILTER RULE (per-source WHERE conditions)
============================================================================
filter_rule for this table:
{filter_rule if filter_rule else "(none)"}

- If filter_rule is empty/(none), do NOT add any WHERE clause.
- filter_rule may contain per-source conditions, each prefixed with a
  source-system label and colon, e.g.:
      CRM: party_kind="Legal"
      SAP: person_type="Legal"
- Apply each labeled condition as a WHERE clause ONLY on the SELECT that reads
  the MATCHING source table — match the label to the source whose name contains
  that token (CRM -> the crm_* table, SAP -> the sap_* table).
- Use single quotes for string literals, e.g. WHERE party_kind = 'Legal'.
- A single unlabeled condition applies to every source SELECT.
- Do NOT invent conditions that are not present in filter_rule.

============================================================================
OUTPUT REQUIREMENTS
============================================================================
- Return RAW SQL ONLY: no markdown, no code fences, no comments, no explanation.
- The SQL MUST start with SELECT (or WITH if genuinely required).
- Use the source table and column names exactly as in config_json.
- Do NOT hardcode catalog/schema; reference source tables by their bare name.

config_json:
{config_str}

Now output ONLY the final {sql_dialect} build SQL.
"""
    return apply_dialect_tokens(prompt, platform)
