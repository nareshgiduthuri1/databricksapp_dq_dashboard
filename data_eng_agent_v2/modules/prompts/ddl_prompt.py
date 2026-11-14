"""
DDL Prompt Builder
==================

Platform-aware DDL prompt template, ported from
`LangGraphAgenticPipeline/config/prompts.py` and isolated here so the
existing stage-SQL / SCD / config prompts elsewhere in the project
remain untouched.

The single public helper is `build_ddl_prompt(...)`.
"""

from __future__ import annotations

from modules.ddl_constants import DATA_PLATFORMS


DDL_PROMPT_TEMPLATE = """
You are a SQL generator for {platform_name}.
Generate a CREATE TABLE statement and constraints using the input JSON.

TARGET PLATFORM: {platform_name}
SQL DIALECT: {sql_dialect}

PLATFORM-SPECIFIC RULES:
{platform_rules}

STRICT RULES:
- Table name must be in lowercase.
- Column names must be in lowercase.
- Preserve column order exactly as given.
- Add NOT NULL only for primary key columns.
- Use data types appropriate for {platform_name}:
  {data_type_rules}
- If column name is "is_weekend", force datatype to {char_type}.
- Do NOT add extra columns.
- Do NOT add comments or explanations.

Output must contain:
1. CREATE TABLE statement
2. {pk_constraint_instruction}
3. Constraint naming format: XPK<UPPER_TABLE_NAME>

{fk_instruction}

INPUT:
{input_json}

OUTPUT FORMAT:
CREATE TABLE <table_name>
(
  <column_name> <datatype> [NOT NULL],
  ...
);

{pk_output_format}
""".strip()


# Per-platform "house rules" injected into the prompt body
_PLATFORM_RULES_MAP = {
    "Databricks": (
        "- Use Delta Lake compatible syntax\n"
        "- Unity Catalog format: catalog.schema.table\n"
        "- STRING is native (do not use VARCHAR)"
    ),
    "Snowflake": (
        "- Use VARCHAR instead of STRING\n"
        "- Use NUMBER(38,0) for integer types\n"
        "- Use TIMESTAMP_NTZ for timestamps\n"
        "- Snowflake supports AUTOINCREMENT for identity columns"
    ),
    "Microsoft Fabric": (
        "- Use T-SQL compatible syntax\n"
        "- Use VARCHAR(MAX) for variable strings\n"
        "- Use DATETIME2 for timestamps\n"
        "- Use IDENTITY(1,1) for auto-increment"
    ),
    "Google BigQuery": (
        "- Use BigQuery Standard SQL\n"
        "- Use INT64 instead of BIGINT/INTEGER\n"
        "- Do NOT use ALTER TABLE for constraints (not supported)\n"
        "- Primary keys are informational only"
    ),
}


def build_ddl_prompt(
    input_json: str,
    platform_name: str,
    sql_dialect: str,
    platform_config: dict | None = None,
) -> str:
    """
    Build a platform-aware DDL prompt for the LLM.

    Parameters
    ----------
    input_json : str
        DDL-ready JSON for a single table (already serialised to a string).
    platform_name : str
        One of the keys in DATA_PLATFORMS (e.g. "Databricks", "Snowflake",
        "Microsoft Fabric").
    sql_dialect : str
        Dialect label (e.g. "SparkSQL", "SnowflakeSQL", "TSQL").
    platform_config : dict, optional
        Pre-resolved platform configuration. If omitted, the function will
        look it up from DATA_PLATFORMS using `platform_name`.
    """
    if platform_config is None:
        platform_config = DATA_PLATFORMS.get(
            platform_name, DATA_PLATFORMS["Databricks"]
        )

    # Data-type mapping rules
    data_type_rules = (
        f'"STRING" → {platform_config["string_type"]}, '
        f'"INTEGER" → {platform_config["integer_type"]}, '
        f'"BIGINT" → {platform_config["integer_type"]}, '
        f'"TIMESTAMP" → {platform_config["timestamp_type"]}, '
        f'"BOOLEAN" → {platform_config["boolean_type"]}'
    )

    # PK constraint instruction
    if platform_config.get("supports_alter_pk", True):
        pk_instruction = "ALTER TABLE statement for primary key"
        pk_format = (
            "ALTER TABLE <table_name>\n"
            "ADD CONSTRAINT <constraint_name> PRIMARY KEY (<pk_columns>);"
        )
    else:
        pk_instruction = (
            "PRIMARY KEY as inline comment "
            "(this platform does not enforce PK constraints)"
        )
        pk_format = "-- PRIMARY KEY: (<pk_columns>)  -- Not enforced by platform"

    # FK constraint instruction
    if platform_config.get("supports_alter_fk", True):
        fk_instruction = (
            "If foreign_keys are present:\n"
            "- Generate ALTER TABLE statements for each foreign key\n"
            "- Foreign key format:\n"
            "  ALTER TABLE <table_name>\n"
            "  ADD CONSTRAINT <constraint_name>\n"
            "  FOREIGN KEY (<column>)\n"
            "  REFERENCES <ref_table> (<ref_column>);\n"
            "- Foreign key naming: FK_<TABLE_NAME>__<REFERENCED_TABLE>"
        )
    else:
        fk_instruction = (
            f"NOTE: {platform_name} does not support foreign key "
            "constraints. Add FK relationships as comments only."
        )

    return DDL_PROMPT_TEMPLATE.format(
        platform_name=platform_name,
        sql_dialect=sql_dialect,
        platform_rules=_PLATFORM_RULES_MAP.get(platform_name, ""),
        data_type_rules=data_type_rules,
        char_type=platform_config.get("string_type", "CHAR(1)")[:7],
        pk_constraint_instruction=pk_instruction,
        fk_instruction=fk_instruction,
        pk_output_format=pk_format,
        input_json=input_json,
    )
