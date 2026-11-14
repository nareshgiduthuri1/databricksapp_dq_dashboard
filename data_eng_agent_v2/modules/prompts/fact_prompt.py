"""Platform-aware FACT staging-SQL prompt builder."""

from __future__ import annotations

import json

from modules.prompts._profiles import stage_sql_platform_rules, apply_dialect_tokens


def build_fact_stage_sql_prompt(config_json: dict, platform: str = "Databricks", sql_dialect: str = "Spark SQL", conversion_type: str = "Data Vault to Dimensional") -> str:
    """Build the full LLM prompt for FACT stage SQL generation.

    `conversion_type` selects the source-model paradigm:
      - "Data Vault to Dimensional" (default): FROM starts at hub_<grain>,
        HUB/SAT/LINK join graph — original behaviour, rendered byte-identical.
      - "3NF to Dimensional": FROM starts at the base grain source table
        and joins follow the STTM Transformation_Logic exactly (no
        HUB/SAT/LINK fabrication).
    """

    config_str = json.dumps(config_json, indent=2, default=str)

    target_table = config_json.get("target_table", "")
    name = config_json.get("name", "") or ""

    foreign_keys = config_json.get("foreign_keys") or []

    # Increment keys drive PARTITION BY in dedup CTE
    increment_keys = config_json.get("increment_keys") or []
    if increment_keys:
        partition_by_cols = ", ".join(increment_keys)
    else:
        # Safe fallback — should rarely trigger because derive_increment_keys covers both tiers
        partition_by_cols = (
            config_json.get("primary_key")
            or (foreign_keys[0] if foreign_keys else "")
        )

    # Derive grain (used for FROM-clause grain rule)
    if name.lower().startswith("fact_"):
        grain = name[len("fact_"):]
    else:
        grain = name
    expected_grain_hub = f"hub_{grain}" if grain else "<HUB_GRAIN>"
    expected_grain_src = grain if grain else "<GRAIN_TABLE>"

    # ── Conversion-aware fragments ────────────────────────────────────
    # For Data Vault the DV branch below reproduces the ORIGINAL prompt
    # text byte-for-byte, so DV output is unchanged. For 3NF the FROM
    # clause / join graph / watermark alias are driven by the base grain
    # source table and the STTM Transformation_Logic instead of hubs/sats.
    is_3nf = str(conversion_type or "").strip().lower().startswith("3nf")

    if is_3nf:
        ts_alias = "<grain_alias>"
        ts_table_desc = "the base grain source table for this fact"
        ref_kinds = "base / lookup / reference / DIM"
        null_ex_table, null_ex_alias = "policy", "p"
        item12_tail = "the corresponding hub / base source table"
        grain_from_checklist = (
            f"the base grain source table {expected_grain_src} "
            f"(no HUB/SAT/LINK tables)"
        )

        schema_routing_block = f"""- 3NF source tables (base grain table, lookup / reference tables — e.g. {expected_grain_src}, lkp_status, ref_*):
    use {{vault_schema}}

- DIM_*:
    use {{gold_schema_name}}

- Watermark / control tables:
    use {{control_schema_name}}.{{watermark_table_name}}

CORRECT:
FROM {{catalog_name}}.{{vault_schema}}.{expected_grain_src} <g_alias>

CORRECT:
LEFT JOIN {{catalog_name}}.{{gold_schema_name}}.dim_customer dc

CORRECT:
FROM {{catalog_name}}.{{control_schema_name}}.{{watermark_table_name}} wm

WRONG:
FROM {{catalog_name}}.{{vault_schema_name}}.{expected_grain_src}
FROM {{catalog_name}}.{{schema_name}}.{expected_grain_src}"""

        from_grain_block = f"""The FROM clause of the `src` CTE MUST start from the GRAIN (base) SOURCE TABLE of this fact.

Grain source table for this fact = {expected_grain_src}

Example: for FACT_LEAD the FROM clause must start from lead.
         for FACT_QUOTE  the FROM clause must start from quote.
         for FACT_POLICY the FROM clause must start from policy.
         for FACT_COMPLAINT the FROM clause must start from complaint.

All other lookup / reference / dim tables are reached via the JOINs defined in
the STTM Transformation_Logic (LEFT JOIN for DIM surrogate-key resolution)."""

        join_graph_block = """- the base grain source table is the primary source (the FROM clause)
- reference / lookup tables are joined EXACTLY as the STTM Transformation_Logic
  specifies — use INNER JOIN / LEFT JOIN exactly as written, never substitute one for the other
- DIM joins are ONLY for surrogate-key resolution
- DIM joins MUST NEVER drive row cardinality
- ALL DIM joins MUST use LEFT JOIN
- do NOT introduce HUB / SAT / LINK (Data Vault) tables — they do not exist in a 3NF source
- preserve fact grain exactly"""

        skeleton_source_block = f"""    FROM {{catalog_name}}.{{vault_schema}}.{expected_grain_src} <g_alias>

    <INNER|LEFT> JOIN {{catalog_name}}.{{vault_schema}}.<LOOKUP_OR_REFERENCE_TABLE> <alias>
        ON ...        -- exactly as written in the STTM Transformation_Logic

    LEFT JOIN {{catalog_name}}.{{gold_schema_name}}.<DIM_TABLE> <d_alias>
        ON ...

    WHERE to_timestamp(<grain_alias>.load_date) > (SELECT watermark FROM wm)"""
    else:
        ts_alias = "<sat_alias>"
        ts_table_desc = "the primary SAT table for this fact's grain"
        ref_kinds = "HUB / LINK / SAT / DIM"
        null_ex_table, null_ex_alias = "SAT_POLICY", "sp"
        item12_tail = "the corresponding hub table"
        grain_from_checklist = expected_grain_hub

        schema_routing_block = """- HUB_* / SAT_* / LINK_*:
    use {vault_schema}

- DIM_*:
    use {gold_schema_name}

- Watermark / control tables:
    use {control_schema_name}.{watermark_table_name}

CORRECT:
FROM {catalog_name}.{vault_schema}.hub_order ho

CORRECT:
LEFT JOIN {catalog_name}.{gold_schema_name}.dim_customer dc

CORRECT:
FROM {catalog_name}.{control_schema_name}.{watermark_table_name} wm

WRONG:
FROM {catalog_name}.{vault_schema_name}.hub_order
FROM {catalog_name}.{schema_name}.hub_order"""

        from_grain_block = f"""The FROM clause of the `src` CTE MUST start from the GRAIN HUB of this fact.

Grain hub for this fact = {expected_grain_hub}

Example: for FACT_LEAD the FROM clause must start from hub_lead.
         for FACT_QUOTE  the FROM clause must start from hub_quote.
         for FACT_POLICY the FROM clause must start from hub_policy.
         for FACT_COMPLAINT the FROM clause must start from hub_complaint.

All other hubs / links / sats / dims are reached via LEFT JOINs."""

        join_graph_block = """- HUB + SAT joins form the primary source graph
- LINK tables bridge HUB relationships
- DIM joins are ONLY for surrogate-key resolution
- DIM joins MUST NEVER drive row cardinality
- ALL DIM joins MUST use LEFT JOIN
- preserve fact grain exactly"""

        skeleton_source_block = f"""    FROM {{catalog_name}}.{{vault_schema}}.{expected_grain_hub} <h_alias>

    LEFT JOIN {{catalog_name}}.{{vault_schema}}.<SAT_TABLE> <s_alias>
        ON ...

    LEFT JOIN {{catalog_name}}.{{vault_schema}}.<LINK_TABLE> <l_alias>
        ON ...

    LEFT JOIN {{catalog_name}}.{{gold_schema_name}}.<DIM_TABLE> <d_alias>
        ON ...

    WHERE to_timestamp(<sat_alias>.load_date) > (SELECT watermark FROM wm)"""

    platform = platform or "Databricks"
    sql_dialect = sql_dialect or "Spark SQL"
    platform_rules = stage_sql_platform_rules(platform, sql_dialect)
    prompt = f"""You are an expert {platform} SQL ({sql_dialect}) engineer.

PLATFORM-SPECIFIC SQL RULES (the generated SQL MUST be valid for {platform} / {sql_dialect}):
{platform_rules}

Platform: {platform}
SQL dialect: {sql_dialect}

============================================================================
OBJECTIVE
============================================================================

Write a staging SELECT query for the FACT table:
{target_table}

The query must:
- Generate optimized {sql_dialect}
- Preserve correct fact grain
- Resolve surrogate keys
- Support incremental processing via watermark CTE
- Use CTE-based modular SQL (wm, src, dedup)
- Return RAW SQL ONLY

DO NOT RETURN:
- markdown
- comments
- explanations
- code fences

The SQL MUST start with:
WITH
or
SELECT

============================================================================
SCHEMA PLACEHOLDER RULES (CRITICAL)
============================================================================

ALL table references MUST use these placeholders DIRECTLY:

{{catalog_name}}
{{vault_schema}}
{{gold_schema_name}}
{{control_schema_name}}
{{watermark_table_name}}

NEVER USE:
{{schema_name}}
{{vault_schema_name}}

NEVER WRAP TABLE REFERENCES IN:
f"..."
"..."
'...'

SCHEMA ROUTING RULES:

{schema_routing_block}

DO NOT:
- hardcode catalog names
- hardcode schema names
- hardcode the watermark table name

============================================================================
CRITICAL MAPPING RULES
============================================================================

Use config_json as the SINGLE SOURCE OF TRUTH for:
- joins
- transformations
- filters
- source tables
- dimensions
- link relationships
- surrogate keys
- measures
- business keys

FOR EACH COLUMN MAPPING:

a) transformation:
    - apply ALL transformations exactly as defined
    - only adjust syntax for valid {sql_dialect}
    - join predicates (AND/ON conditions) must be used EXACTLY as written
    - NEVER substitute AND with OR (and vice versa) in join conditions
    - NEVER simplify multi-condition join predicates

b) source_table and source_column:
    - derive complete JOIN graph from the supplied Transformation_Logic
    - do NOT invent additional joins
    - do NOT duplicate joins: if a hub already participates in the join graph
      through one path, do NOT re-join the same hub through a different path
      unless STTM explicitly requires it

c) foreign keys ({foreign_keys}):

    - EVERY FK ending in _SK or _sk
      MUST come from the corresponding DIM table surrogate key

    - ALL FK joins MUST use LEFT JOIN

    - ALL FK projections MUST use:
        COALESCE(dim_alias.<surrogate_key>, -1)

    - FK columns MUST appear FIRST in final projection order

============================================================================
STTM MAPPING ENFORCEMENT (HIGHEST PRIORITY)
============================================================================

The supplied config_json originates from a validated Source-To-Target Mapping
(S2T) specification.

The generated SQL MUST reproduce the S2T mapping structure exactly.

STRICT REQUIREMENTS:

1. Every target_column present in config_json.columns MUST appear exactly once
   in the final SELECT output (with the exception of the internal helper
   column 'event_ts' — see EVENT TIMESTAMP RULES).

2. No target column may be omitted.

3. Do not invent additional business columns.

4. Preserve target column ordering using column_order when provided.

5. If a column contains Transformation_Logic:
   - use the supplied joins exactly
   - use the supplied traversal path exactly
   - use the supplied predicates exactly (preserving AND / OR exactly)

6. Do NOT rewrite join conditions.

7. Do NOT simplify join chains.

8. Do NOT replace supplied joins with alternative joins.

9. Do NOT infer additional joins.

10. If Transformation_Logic references {ref_kinds} tables,
    those joins must be reflected in the SQL exactly as provided.

11. If Transformation_Logic is NULL, use source_table.source_column directly.

    Example:
        source_table:  {null_ex_table}
        source_column: GROSS_REVENUE
        target_column: policy_gross_revenue_amt
        Generate:      {null_ex_alias}.gross_revenue AS policy_gross_revenue_amt

12. For the column `person_id` (or any non-SK identifier whose
    SourceMapping.Source_Table is a DIM_ table), source the value
    from the DIM table alias (e.g. dp.person_id) — NEVER substitute
    with {item12_tail}.

13. Transformation_Logic ALWAYS WINS over any inferred logic.

============================================================================
FROM CLAUSE GRAIN RULE (CRITICAL)
============================================================================

{from_grain_block}

============================================================================
FACT GRAIN RULES
============================================================================

Determine fact behavior primarily from the supplied STTM mappings.

Do NOT introduce:
- SCD2 logic
- AS-OF joins
- effective dating
- temporal validity predicates
- bridge relationships

unless they are explicitly present in the supplied Transformation_Logic.

============================================================================
FACT JOIN GRAPH RULES
============================================================================

{join_graph_block}

============================================================================
EVENT TIMESTAMP RULES
============================================================================

The src CTE MUST derive an internal event timestamp:

    to_timestamp({ts_alias}.load_date) AS event_ts

where {ts_alias} is the alias of {ts_table_desc}.

event_ts is used ONLY for:
- ORDER BY inside the dedup CTE's ROW_NUMBER()

event_ts MUST NEVER appear in the final SELECT.

============================================================================
WATERMARK CTE PATTERN (MANDATORY)
============================================================================

The first CTE MUST be the watermark CTE in this exact shape:

WITH wm AS (
    SELECT
        COALESCE(
            MAX(watermark),
            TIMESTAMP('1900-01-01 00:00:00')
        ) AS watermark
    FROM {{catalog_name}}.{{control_schema_name}}.{{watermark_table_name}}
    WHERE table_name = '{{catalog_name}}.{{gold_schema_name}}.{name}'
)

Notes:
- The WHERE clause MUST use the FULLY QUALIFIED target table name
  ('{{catalog_name}}.{{gold_schema_name}}.{name}') as a string literal.
- Do NOT use bare 'fact_xxx' in the WHERE clause.
- Do NOT use any '${{watermark_col}}' or '${{watermark_value}}' style
  placeholders anywhere in the SQL.

============================================================================
WATERMARK FILTER (MANDATORY)
============================================================================

In the src CTE, apply the incremental filter EXACTLY as:

    WHERE to_timestamp({ts_alias}.load_date) > (SELECT watermark FROM wm)

where {ts_alias} is the alias of {ts_table_desc}.

Do NOT use:
- greatest()
- coalesce() over multiple sat load_date columns
- '${{watermark_col}}'
- '${{watermark_value}}'

============================================================================
MANDATORY AUDIT COLUMNS (CRITICAL)
============================================================================

Inside the `src` CTE, the SELECT list MUST INCLUDE — at the END of the
src SELECT, in this EXACT order, with these EXACT literals:

    'ETL_SYSTEM'                          AS created_by,
    current_timestamp()                   AS created_ts,
    current_timestamp()                   AS load_ts,
    to_timestamp({ts_alias}.load_date)   AS event_ts

Rules:
- Use the literal string 'ETL_SYSTEM' (single-quoted) — NEVER slugify or
  derive this from STTM Source_Column hints like
  "'ETL_SYSTEM' or current_user() or <batch_user>".
- Use current_timestamp() as a SQL function call — NEVER reference it as
  a column (e.g. NEVER write `sp.current_timestamp`).
- These four columns MUST appear in src EVEN IF the STTM mapping for
  created_by / created_ts / load_ts has Source_Table = null.

In the FINAL SELECT (after the dedup CTE), include these three audit
columns at the END in this EXACT order:

    created_by,
    created_ts,
    load_ts

The internal `event_ts` column MUST NOT appear in the final SELECT.

============================================================================
DEDUPLICATION CTE (MANDATORY)
============================================================================

The query MUST contain a `dedup` CTE in this exact shape:

dedup AS (
    SELECT
        src.*,
        ROW_NUMBER() OVER (
            PARTITION BY {partition_by_cols}
            ORDER BY event_ts DESC
        ) AS rn
    FROM src
)

Then the final SELECT MUST:
- read FROM dedup
- end with: WHERE rn = 1

Notes:
- PARTITION BY columns are: {partition_by_cols}
- ORDER BY is always event_ts DESC.
- Do NOT order by created_ts / load_ts / watermark_col / load_date.

============================================================================
ALIAS SAFETY RULES
============================================================================

- NEVER use SQL reserved words as table aliases.
- Specifically forbidden aliases: do, as, is, in, or, and, on, by, to.
- For dim_override use the alias `dov` (not `do`).
- Aliases must be short snake_case identifiers.

============================================================================
FORBIDDEN COLUMNS
============================================================================

The following columns must NEVER appear as projected columns
in ANY SELECT list (neither src nor final):

attr_hash
last_updated_by
last_updated_ts
record_version
load_date
insert_ts
watermark_col

THEY MAY ONLY APPEAR inside expressions / filters / temporal logic.

ALLOWED EXAMPLE:
to_timestamp(sp.load_date) AS event_ts          -- inside expression: OK
to_timestamp(sp.load_date) > (SELECT watermark FROM wm)  -- inside filter: OK

FORBIDDEN EXAMPLE:
sp.load_date          -- bare projection: NOT OK

============================================================================
MEASURE RULES
============================================================================

- preserve source precision and scale
- DO NOT aggregate unless explicitly specified
- derived measures must exactly follow transformation logic
- DO NOT introduce implicit GROUP BY logic

============================================================================
FINAL SELECT RULES
============================================================================

FINAL SELECT ORDER:

1. FK surrogate keys (with COALESCE(..., -1))
2. business / degenerate keys (including person_id when present)
3. measures
4. attributes
5. created_by
6. created_ts
7. load_ts

FINAL SELECT MUST:
- read FROM dedup
- end with WHERE rn = 1
- preserve fact grain
- exclude rn
- exclude event_ts
- exclude watermark_col

============================================================================
STRUCTURAL SKELETON (follow this STRUCTURE exactly — CTE layout, column order, join graph, dedup; but translate ALL functions, casts, type names and literals to {sql_dialect} per the PLATFORM-SPECIFIC SQL RULES above)
============================================================================

WITH wm AS (

    SELECT
        COALESCE(
            MAX(watermark),
            TIMESTAMP('1900-01-01 00:00:00')
        ) AS watermark
    FROM {{catalog_name}}.{{control_schema_name}}.{{watermark_table_name}}
    WHERE table_name = '{{catalog_name}}.{{gold_schema_name}}.{name}'

),

src AS (

    SELECT

        <fk surrogate keys with COALESCE(..., -1)>,
        <business / degenerate keys>,
        <measures and attributes>,

        'ETL_SYSTEM'                          AS created_by,
        current_timestamp()                   AS created_ts,
        current_timestamp()                   AS load_ts,
        to_timestamp({ts_alias}.load_date)   AS event_ts

{skeleton_source_block}

),

dedup AS (

    SELECT
        src.*,
        ROW_NUMBER() OVER (
            PARTITION BY {partition_by_cols}
            ORDER BY event_ts DESC
        ) AS rn
    FROM src

)

SELECT

    <fk surrogate keys>,
    <business / degenerate keys>,
    <measures and attributes>,
    created_by,
    created_ts,
    load_ts

FROM dedup
WHERE rn = 1

============================================================================
TABLE NAMING RULES
============================================================================

Vault tables:
{{catalog_name}}.{{vault_schema}}.<table>

Gold tables:
{{catalog_name}}.{{gold_schema_name}}.<table>

Control tables:
{{catalog_name}}.{{control_schema_name}}.{{watermark_table_name}}

NEVER use:
{{schema_name}}
{{vault_schema_name}}

============================================================================
OUTPUT REQUIREMENTS
============================================================================

Output a SINGLE {sql_dialect} query that:

- implements all STTM transformations exactly
- preserves correct fact grain
- resolves FK surrogate keys via LEFT JOIN + COALESCE(..., -1)
- uses the 3-CTE structure (wm, src, dedup)
- uses proper schema placeholders
- starts with WITH
- returns RAW SQL ONLY

config_json:
{config_str}


IDENTIFIER NAMING RULES (CRITICAL):
- All projected column aliases in the SELECT clause MUST use snake_case
  identifiers without spaces, hyphens, or special characters.
- NEVER use backticks (`) anywhere in the SQL — not for column aliases,
  not for table references, not for any identifier.
- If a target column name in the STTM contains spaces, hyphens, slashes,
  parentheses, or other non-alphanumeric characters, you MUST normalise it:
    - Convert to lowercase.
    - Replace spaces, hyphens, slashes, dots with underscores.
    - Strip parentheses and other punctuation entirely.
    - Collapse consecutive underscores into a single underscore.
- Examples of the required transformation:
    - "Insured Object Identifier"   -> insured_object_identifier
    - "Insured Object Sub-Type"     -> insured_object_sub_type
    - "Created By"                  -> created_by
    - "Premium Amount (USD)"        -> premium_amount_usd
- Apply this rule to:
    - The alias on the right side of AS in every projection
    - Every column referenced in PARTITION BY and ORDER BY
- Source column references (left side of AS) MAY stay as-is from the
  source table since they reflect the actual physical column name.
- Goal: every output column from the staging query is a clean snake_case
  identifier that can be referenced without quoting downstream.


FINAL VALIDATION CHECKLIST

Before returning SQL verify:

1. Every target_column from config_json.columns appears in final SELECT
   (except event_ts, which is internal-only).

2. FK columns appear first in target order, each wrapped in COALESCE(..., -1).

3. Measures appear in target order.

4. Attribute columns appear in target order.

5. created_by, created_ts, load_ts appear at the END of the final SELECT
   in that exact order.

6. event_ts is present in src and used in dedup ORDER BY, but is NOT in
   the final SELECT.

7. The dedup CTE uses PARTITION BY {partition_by_cols} ORDER BY event_ts DESC.

8. The wm CTE uses {{watermark_table_name}} and a fully qualified
   target table name in its WHERE clause.

9. No '${{watermark_col}}' / '${{watermark_value}}' placeholders anywhere.

10. No '{{vault_schema_name}}' or '{{schema_name}}' anywhere — only
    '{{vault_schema}}', '{{gold_schema_name}}', '{{control_schema_name}}',
    '{{watermark_table_name}}', '{{catalog_name}}'.

11. No SQL reserved words used as aliases (use `dov` not `do` for dim_override).

12. Join predicates use AND / OR exactly as Transformation_Logic specifies.

13. FROM clause of src starts from {grain_from_checklist}.

Now output ONLY the final {sql_dialect} query.
"""
    return apply_dialect_tokens(prompt, platform)
