"""
DDL Constants — Platform & Dialect Catalog
==========================================

Centralised registry of supported Data Platforms and SQL Dialects used
by the DDL generation flow. This is intentionally kept self-contained
in `modules/ddl_constants.py` so that:

  • the existing pipeline (SCD-1/SCD-2/FACT/config/notebook) is unaffected,
  • a future Streamlit UI can import and render these dictionaries
    directly to populate Data-Platform / SQL-Dialect dropdowns,
  • new platforms (e.g. BigQuery) can be added in ONE place without
    touching the DDL generator or prompt template.

Ported (and slightly trimmed to DDL-only fields) from the
LangGraphAgenticPipeline reference codebase:
`LangGraphAgenticPipeline/config/constants.py`.

NOTE: Do NOT modify any of the SCD/config/stage-SQL related logic in
this project. This file is additive only.
"""

from __future__ import annotations


# ── DDL Constraint Naming ──────────────────────────────────────────────
PK_CONSTRAINT_PREFIX = "XPK"
FK_CONSTRAINT_PREFIX = "FK"


# ── Data Type Normalisation ────────────────────────────────────────────
# Lightweight mapping from Erwin / STTM data-type aliases to a
# canonical upper-case token consumed by the DDL prompt. Platform-
# specific resolution (STRING → VARCHAR, INTEGER → BIGINT, …) happens
# inside `build_ddl_prompt(...)` using DATA_PLATFORMS[<name>].
DATA_TYPE_MAP = {
    "INT": "INTEGER",
    "int": "INTEGER",
    "CHAR": "CHAR(1)",
}


# ══════════════════════════════════════════════════════════════════════
# DATA PLATFORM REGISTRY
# ══════════════════════════════════════════════════════════════════════
DATA_PLATFORMS = {
    "Databricks": {
        "label": "Databricks",
        "string_type": "STRING",
        "integer_type": "BIGINT",
        "timestamp_type": "TIMESTAMP",
        "boolean_type": "BOOLEAN",
        "decimal_type": "DECIMAL",
        "supports_alter_pk": True,
        "supports_alter_fk": True,
        "identity_syntax": "GENERATED ALWAYS AS IDENTITY",
        "catalog_format": "{catalog}.{schema}.{table}",
        "notes": "Unity Catalog compatible",
    },
    "Snowflake": {
        "label": "Snowflake",
        "string_type": "VARCHAR",
        "integer_type": "NUMBER(38,0)",
        "timestamp_type": "TIMESTAMP_NTZ",
        "boolean_type": "BOOLEAN",
        "decimal_type": "NUMBER",
        "supports_alter_pk": True,
        "supports_alter_fk": True,
        "identity_syntax": "AUTOINCREMENT",
        "catalog_format": "{database}.{schema}.{table}",
        "notes": "Snowflake Data Cloud",
    },
    "Microsoft Fabric": {
        "label": "Microsoft Fabric",
        "string_type": "VARCHAR(MAX)",
        "integer_type": "BIGINT",
        "timestamp_type": "DATETIME2",
        "boolean_type": "BIT",
        "decimal_type": "DECIMAL",
        "supports_alter_pk": True,
        "supports_alter_fk": True,
        "identity_syntax": "IDENTITY(1,1)",
        "catalog_format": "{database}.{schema}.{table}",
        "notes": "Microsoft Fabric Lakehouse / Warehouse",
    },
    "Google BigQuery": {
        "label": "Google BigQuery",
        "string_type": "STRING",
        "integer_type": "INT64",
        "timestamp_type": "TIMESTAMP",
        "boolean_type": "BOOL",
        "decimal_type": "NUMERIC",
        "supports_alter_pk": False,
        "supports_alter_fk": False,
        "identity_syntax": "-- BigQuery does not support IDENTITY",
        "catalog_format": "{project}.{dataset}.{table}",
        "notes": "BigQuery does not enforce PK/FK constraints",
    },
}


# ══════════════════════════════════════════════════════════════════════
# SQL DIALECT REGISTRY
# ══════════════════════════════════════════════════════════════════════
SQL_DIALECTS = {
    "SparkSQL":     {"label": "SparkSQL",     "notes": "Databricks / Spark"},
    "SnowflakeSQL": {"label": "SnowflakeSQL", "notes": "Snowflake native SQL"},
    "TSQL":         {"label": "TSQL",         "notes": "Microsoft T-SQL"},
    "BigQuerySQL":  {"label": "BigQuerySQL",  "notes": "Google BigQuery"},
}


# ── Sensible defaults: Platform → Dialect ─────────────────────────────
PLATFORM_DIALECT_DEFAULTS = {
    "Databricks":       "SparkSQL",
    "Snowflake":        "SnowflakeSQL",
    "Microsoft Fabric": "TSQL",
    "Google BigQuery":  "BigQuerySQL",
}


# ── Case-insensitive aliases for user-supplied platform / dialect labels ──
# config.yaml may carry values like "snowflake", "fabrics",
# "Snowflake SQL", "T-SQL (Fabric SQL)" — normalise them all here so the
# generators never silently fall back to Databricks.
_PLATFORM_ALIASES = {
    "databricks": "Databricks",
    "snowflake": "Snowflake",
    "microsoft fabric": "Microsoft Fabric",
    "fabric": "Microsoft Fabric",
    "fabrics": "Microsoft Fabric",
    "ms fabric": "Microsoft Fabric",
    "google bigquery": "Google BigQuery",
    "bigquery": "Google BigQuery",
    "big query": "Google BigQuery",
}

_DIALECT_ALIASES = {
    "sparksql": "SparkSQL",
    "spark sql": "SparkSQL",
    "spark": "SparkSQL",
    "snowflakesql": "SnowflakeSQL",
    "snowflake sql": "SnowflakeSQL",
    "snowflake": "SnowflakeSQL",
    "tsql": "TSQL",
    "t-sql": "TSQL",
    "t sql": "TSQL",
    "t-sql (fabric sql)": "TSQL",
    "fabric sql": "TSQL",
    "bigquerysql": "BigQuerySQL",
    "bigquery sql": "BigQuerySQL",
    "bigquery": "BigQuerySQL",
}


def resolve_platform(platform_name: str | None) -> tuple[str, dict]:
    """
    Resolve a user-provided platform string to (canonical_name, config_dict).

    Matching is CASE-INSENSITIVE and alias-aware (e.g. "snowflake",
    "fabrics", "ms fabric" all resolve correctly). Falls back to
    'Databricks' only if `platform_name` is empty or genuinely unknown.
    """
    if not platform_name:
        return "Databricks", DATA_PLATFORMS["Databricks"]

    key = str(platform_name).strip().lower()
    canon = _PLATFORM_ALIASES.get(key)
    if canon is None:
        for k in DATA_PLATFORMS:
            if k.lower() == key:
                canon = k
                break
    if not canon or canon not in DATA_PLATFORMS:
        return "Databricks", DATA_PLATFORMS["Databricks"]
    return canon, DATA_PLATFORMS[canon]


def resolve_dialect(platform_name: str, sql_dialect: str | None) -> str:
    """
    Resolve dialect — use the (alias/case-insensitive) override if it maps
    to a known dialect, otherwise the canonical platform's default dialect.
    """
    if sql_dialect:
        key = str(sql_dialect).strip().lower()
        canon = _DIALECT_ALIASES.get(key)
        if canon is None:
            for k in SQL_DIALECTS:
                if k.lower() == key:
                    canon = k
                    break
        if canon and canon in SQL_DIALECTS:
            return canon
    return PLATFORM_DIALECT_DEFAULTS.get(platform_name, "SparkSQL")
