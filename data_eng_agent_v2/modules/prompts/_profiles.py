"""
Per-platform SQL rules + dialect token translation for stage-SQL prompts
========================================================================

The stage-SQL / config / DDL **output structure is identical across all
data platforms** (same config keys, same `{catalog_name}`/`{gold_schema_name}`
placeholders, same `${watermark_*}` widget conventions). The ONLY thing
that varies between platforms is the *prompt* — the dialect label, a block
of dialect-specific syntax rules, and the concrete SQL functions/types.

Two helpers are exposed:

  • ``stage_sql_platform_rules(platform, sql_dialect)`` — the rule block that
    is injected near the top of every stage-SQL prompt. It enumerates the
    dialect-correct equivalents (types, current-timestamp, cast-to-timestamp,
    sentinels, hashing) and ends with a strict "translate everything to this
    dialect" directive.

  • ``apply_dialect_tokens(prompt_text, platform)`` — a deterministic
    post-processing pass that rewrites the Spark-only function literals that
    appear in the prompt skeletons/examples (``current_timestamp()``,
    ``to_timestamp(x)``, ``TIMESTAMP('x')``) into the target dialect, so the
    examples the LLM is told to "follow exactly" are already dialect-correct.
    For Databricks every substitution is a no-op.
"""

from __future__ import annotations

import re


# ══════════════════════════════════════════════════════════════════════
# Per-platform rule blocks (injected into the prompt body)
# ══════════════════════════════════════════════════════════════════════
_DATABRICKS = (
    "- Target dialect: Databricks SQL (Spark SQL) on Delta Lake / Unity Catalog.\n"
    "- Types: STRING (text), BIGINT (integer), DECIMAL(p,s) (decimal), TIMESTAMP, BOOLEAN.\n"
    "- Current timestamp: current_timestamp().\n"
    "- Cast a column/string to timestamp: to_timestamp(<expr>).\n"
    "- Low/epoch sentinel: TIMESTAMP('1900-01-01 00:00:00'). Far-future: TIMESTAMP '9999-12-31 00:00:00'.\n"
    "- Hashing: SHA2(CONCAT_WS('||', <cols cast to string>), 256).\n"
    "- Surrogate-key cast: CAST(<expr> AS BIGINT).\n"
    "- Identifiers: lowercase snake_case; NEVER use backticks or double quotes."
)

_SNOWFLAKE = (
    "- Target dialect: Snowflake SQL.\n"
    "- Types: VARCHAR (text), NUMBER(38,0) (integer), NUMBER(38,4) (decimal), TIMESTAMP_NTZ, BOOLEAN.\n"
    "- Current timestamp: CURRENT_TIMESTAMP().\n"
    "- Cast a column/string to timestamp: TO_TIMESTAMP_NTZ(<expr>)  (NEVER use Spark to_timestamp()).\n"
    "- Low/epoch sentinel: TO_TIMESTAMP_NTZ('1900-01-01 00:00:00'). Far-future: TO_TIMESTAMP_NTZ('9999-12-31 00:00:00').\n"
    "- Hashing: SHA2(CONCAT_WS('||', <cols cast to string>), 256).\n"
    "- Surrogate-key cast: <expr>::NUMBER(38,0). String cast: <expr>::VARCHAR.\n"
    "- Identifiers: lowercase snake_case, unquoted (no double quotes, no backticks)."
)

_FABRIC = (
    "- Target dialect: Microsoft Fabric T-SQL (Warehouse / SQL analytics endpoint).\n"
    "- Types: VARCHAR(MAX) (text), BIGINT (integer), DECIMAL(38,6) (decimal), DATETIME2, BIT.\n"
    "- Current timestamp: SYSUTCDATETIME().\n"
    "- Cast a column/string to timestamp: CAST(<expr> AS DATETIME2)  (NEVER use Spark to_timestamp()).\n"
    "- Low/epoch sentinel: CAST('1900-01-01 00:00:00' AS DATETIME2). Far-future: CAST('9999-12-31 00:00:00' AS DATETIME2).\n"
    "- Hashing: CONVERT(VARCHAR(64), HASHBYTES('SHA2_256', CONCAT_WS('||', <cols>)), 2).\n"
    "- Surrogate-key cast: CAST(<expr> AS BIGINT).\n"
    "- No LIMIT — use TOP / row-number filtering. Identifiers: lowercase snake_case; no backticks."
)

_BIGQUERY = (
    "- Target dialect: Google BigQuery Standard SQL.\n"
    "- Types: STRING (text), INT64 (integer), NUMERIC (decimal), TIMESTAMP, BOOL.\n"
    "- Current timestamp: CURRENT_TIMESTAMP().\n"
    "- Cast a column/string to timestamp: TIMESTAMP(<expr>)  (NEVER use Spark to_timestamp()).\n"
    "- Low/epoch sentinel: TIMESTAMP '1900-01-01 00:00:00'. Far-future: TIMESTAMP '9999-12-31 00:00:00'.\n"
    "- Hashing: TO_HEX(SHA256(CONCAT('||', <cols cast to string>))).\n"
    "- Surrogate-key cast: CAST(<expr> AS INT64).\n"
    "- Identifiers: lowercase snake_case; no backticks. PK/FK are not enforced by BigQuery."
)

# Accept the common spellings/casings used across the project + config.yaml.
_RULES = {
    "databricks": _DATABRICKS,
    "snowflake": _SNOWFLAKE,
    "microsoft fabric": _FABRIC,
    "fabric": _FABRIC,
    "fabrics": _FABRIC,
    "ms fabric": _FABRIC,
    "google bigquery": _BIGQUERY,
    "bigquery": _BIGQUERY,
    "big query": _BIGQUERY,
}


def _norm(platform: str) -> str:
    return str(platform or "Databricks").strip().lower()


def stage_sql_platform_rules(platform: str, sql_dialect: str | None = None) -> str:
    """
    Return the dialect-specific rule block + a strict translation directive.

    Falls back to the Databricks rules for unknown / empty platforms.
    """
    rules = _RULES.get(_norm(platform), _DATABRICKS)
    dia = sql_dialect or "the target SQL dialect"
    directive = (
        "\n\nDIALECT TRANSLATION (CRITICAL — HIGHEST PRIORITY):\n"
        "- Any SQL shown later in this prompt (skeletons, examples, 'EXACT literals') "
        "uses Spark SQL syntax for ILLUSTRATION of STRUCTURE ONLY.\n"
        f"- You MUST emit every function, cast, type name and literal in {dia} syntax, "
        "following the rules above.\n"
        f"- Do NOT emit Spark-only constructs (to_timestamp(), current_timestamp(), "
        f"TIMESTAMP('...'), STRING, BIGINT) unless {dia} IS Spark SQL.\n"
        "- Keep the QUERY STRUCTURE (CTE layout, column order, join graph, dedup, "
        "config keys) exactly as instructed — only the dialect SYNTAX changes."
    )
    return rules + directive


# ══════════════════════════════════════════════════════════════════════
# Deterministic dialect token translation
# ══════════════════════════════════════════════════════════════════════
# Per-platform concrete tokens for the Spark-only constructs that the
# prompt skeletons hard-code. `cast_open`/`cast_close` wrap a timestamp cast
# so `to_timestamp(X)` -> f"{cast_open}{X}{cast_close}".
_TOKENS = {
    "databricks": {
        "now_ts": "current_timestamp()",
        "cast_open": "to_timestamp(", "cast_close": ")",
        "ts_literal": lambda v: f"TIMESTAMP('{v}')",
    },
    "snowflake": {
        "now_ts": "CURRENT_TIMESTAMP()",
        "cast_open": "TO_TIMESTAMP_NTZ(", "cast_close": ")",
        "ts_literal": lambda v: f"TO_TIMESTAMP_NTZ('{v}')",
    },
    "microsoft fabric": {
        "now_ts": "SYSUTCDATETIME()",
        "cast_open": "CAST(", "cast_close": " AS DATETIME2)",
        "ts_literal": lambda v: f"CAST('{v}' AS DATETIME2)",
    },
    "google bigquery": {
        "now_ts": "CURRENT_TIMESTAMP()",
        "cast_open": "TIMESTAMP(", "cast_close": ")",
        "ts_literal": lambda v: f"TIMESTAMP '{v}'",
    },
}
# Alias spellings → canonical token key
_TOKENS.update({
    "fabric": _TOKENS["microsoft fabric"],
    "fabrics": _TOKENS["microsoft fabric"],
    "ms fabric": _TOKENS["microsoft fabric"],
    "bigquery": _TOKENS["google bigquery"],
    "big query": _TOKENS["google bigquery"],
})


def apply_dialect_tokens(prompt_text: str, platform: str) -> str:
    """
    Rewrite the Spark-only function literals embedded in a rendered prompt
    into the target dialect. No-op for Databricks / unknown platforms.

    Handles:
      • current_timestamp()        → dialect "now"
      • to_timestamp(<expr>)       → dialect timestamp cast
      • TIMESTAMP('<value>')       → dialect timestamp literal
    """
    tok = _TOKENS.get(_norm(platform))
    if tok is None:  # Databricks or unknown → leave Spark literals as-is
        return prompt_text

    text = prompt_text

    # TIMESTAMP('...') function-call literal → dialect literal
    text = re.sub(
        r"TIMESTAMP\('([^']*)'\)",
        lambda m: tok["ts_literal"](m.group(1)),
        text,
    )
    # to_timestamp(<expr>) → dialect cast  (no nested parens in our prompts)
    text = re.sub(
        r"to_timestamp\(([^()]*)\)",
        lambda m: f"{tok['cast_open']}{m.group(1)}{tok['cast_close']}",
        text,
    )
    # bare current_timestamp() → dialect now
    text = text.replace("current_timestamp()", tok["now_ts"])

    return text
