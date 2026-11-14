"""Platform-aware SCD-2 dimension staging-SQL prompt builder."""

from __future__ import annotations

import json

from modules.prompts._profiles import stage_sql_platform_rules, apply_dialect_tokens


def build_dim_scd2_stage_sql_prompt(config_json: dict, platform: str = "Databricks", sql_dialect: str = "Spark SQL") -> str:
    """Build the full LLM prompt for stage SQL generation."""
    config_str = json.dumps(config_json, indent=2, default=str)
    target_table = config_json.get("target_table", "")

    # CHANGE C (Edit 1): derive a SQL-ready business-key string from the
    # list-typed business_key in config_json. Falls back to primary_key
    # when business_key list is empty. Renders as:
    #   single-BK : "policy_id"
    #   multi-BK  : "marketing_preference_id, marketing_engagement_id"
    bk_list = config_json.get("business_key") or []
    if not bk_list:
        pk = config_json.get("primary_key")
        if pk:
            bk_list = [pk]
        else:
            bk_list = []
    business_key_sql = ", ".join(bk_list) if bk_list else ""

    platform = platform or "Databricks"
    sql_dialect = sql_dialect or "Spark SQL"
    platform_rules = stage_sql_platform_rules(platform, sql_dialect)
    prompt = f"""You are an expert {platform} SQL ({sql_dialect}) engineer.

PLATFORM-SPECIFIC SQL RULES (the generated SQL MUST be valid for {platform} / {sql_dialect}):
{platform_rules}

    Platform: {platform}
    SQL dialect: {sql_dialect}

    Objective:
    - Write a staging SELECT query for the dimension table: {target_table}
    - Pull only incremental records using a parameterised watermark column: ${{watermark_value}}.
    - Deduplicate to one row per business key ({business_key_sql}), with the latest record winning.
    - Set effective_to_ts to a far-future sentinel value (e.g. TIMESTAMP '9999-12-31 00:00:00') in the stage output.
    - The downstream loader will handle SCD2 closing of prior records (effective_to_ts updates),
    so the stage query should only produce the current open-ended rows.

    SQL requirements:
    - Produce idiomatic, optimised {sql_dialect} using CTEs.
    - Return RAW SQL ONLY: no markdown, no code fences, no comments, no explanation.
    - The SQL must start with WITH or SELECT.
    # ===== CHANGE 4: Schema split — extended schema-placeholder block (vault vs gold) =====
    - All table references (source and target) MUST use three-part names using
    the placeholders {{catalog_name}} and the appropriate schema placeholder
    ({{vault_schema_name}} OR {{gold_schema_name}}) directly — NOT wrapped
    in any f-string quotes.

    - Schema placeholder selection rule (CRITICAL):
        - For Data Vault tables (HUB_*, SAT_*, LINK_*, hub_*, sat_*, link_*),
          use {{vault_schema_name}}.
        - For Dimension tables (DIM_*, dim_*) referenced as join sources,
          use {{gold_schema_name}}.
        - CORRECT:   FROM {{catalog_name}}.{{vault_schema_name}}.HUB_PRODUCT hp
        - CORRECT:   LEFT JOIN {{catalog_name}}.{{vault_schema_name}}.SAT_PRODUCT sp
        - CORRECT:   LEFT JOIN {{catalog_name}}.{{gold_schema_name}}.DIM_GEOGRAPHY dg
        - WRONG:     FROM {{catalog_name}}.{{schema_name}}.HUB_PRODUCT hp
        - WRONG:     FROM f"{{catalog_name}}.{{vault_schema_name}}.HUB_PRODUCT" hp
        - WRONG:     FROM "{{catalog_name}}.{{vault_schema_name}}.HUB_PRODUCT" hp
    - Do NOT use a generic {{schema_name}} placeholder anywhere in the SQL.
    - Do NOT hardcode any catalog or schema names in the SQL.
    - Do NOT wrap table references in f"...", "...", or any quoting.
    # ===== END CHANGE 4 =====

    Critical mapping rules from config_json:
    - Use the provided config_json as the single source of truth for all joins, filters, and column logic.
    - For each column mapping:
    a) transformation:
        - May contain JOIN clauses between source tables
        (e.g. "hub_x ha LEFT JOIN sat_x sa ON sa.hash_key = ha.hash_key"),
        derived expressions (e.g. "nextval()"), or conditional logic.
        - You MUST incorporate ALL joins and transformations exactly as specified,
        adapting only to valid {sql_dialect} syntax.
    b) source_column and source_table:
        - Only include columns in the SELECT list where source_table is non-null.
        - Columns with null source_table are purely derived and must NOT appear in the stage SELECT output.
        - However, if Transformation_Logic is NULL but source_table is NON-NULL,
          the column MUST be projected as
              <source_table_alias>.<source_column> AS <target_column>
          reusing the SAT/HUB/DIM alias already present in the join graph for
          that source_table. This column MUST NOT be silently dropped.
        - Use source_table together with transformation to derive the complete JOIN graph.
    c) effective_from_ts and effective_to_ts:
        - If these columns exist in the mapping, they MUST be included in the stage SQL output.
        - effective_to_ts should be set to a far-future sentinel value for all staged rows.

    Join and transformation handling:
    - Derive the full JOIN structure from the combination of transformation and source_table fields.
    - Apply every transformation expression exactly as defined, only adjusting syntax to {sql_dialect}.
    - Correctly handle surrogate keys, audit columns, and sentinel values as indicated.
    - Use the business key ({business_key_sql}) as the partition key for deduplication.
      If multiple business keys are listed (comma-separated), use them ALL as a
      composite partition key directly — do NOT concatenate them into a synthetic
      single column via CONCAT_WS / CONCAT / ||. The PARTITION BY clause must
      reference the business key columns individually, e.g.
          ROW_NUMBER() OVER(PARTITION BY {business_key_sql} ORDER BY <watermark> DESC)
    - Filter the source data using the parameterised watermark ${{watermark_value}} to pull incremental records only.
    - Optimise the query for execution time and minimal data volume (push filters down,
    avoid unnecessary columns, use CTEs effectively).

    # ===== CHANGE 7: NEW — WATERMARK COLUMN PARAMETRIZATION block =====
    WATERMARK COLUMN PARAMETRIZATION (CRITICAL):

    PLACEHOLDER SYNTAX:
    - Use ${{watermark_col}} (double braces) anywhere the watermark column name
      is referenced in the SQL.
    - Use ${{watermark_value}} (double braces) for the runtime watermark value.
    - Single braces will break the wrapping Python f-string at file-read time.

    QUALIFICATION RULE:
    - ALWAYS qualify the watermark column with the SAT alias
      (e.g., sp.${{watermark_col}}, snp.${{watermark_col}}).
    - NEVER qualify with the HUB alias — HUB tables typically do not have
      a load_date / watermark column.

    # (CHANGE A1) — NEW OVERRIDE RULE sub-section
    OVERRIDE RULE (HIGHEST PRIORITY):
    - The watermark column projection rules in this section OVERRIDE any
      transformation logic provided in the column-level `transformation` field.
    - Specifically, even if a column-level transformation says
      "greatest(coalesce(<single_sat>.load_date, ...))", you MUST NOT use that
      expression for the `watermark_col` projection in single-source tables.
    - The watermark column derivation is determined SOLELY by counting how many
      distinct SAT_* tables appear in the join graph:
        - If exactly ONE SAT_* table → use the single-source pattern below.
        - If TWO or more SAT_* tables → use the multi-sat pattern below.
    - The `transformation` field's greatest(coalesce(...)) form may still be
      used for the SEPARATE `effective_from_ts` projection (see "BOTH
      PROJECTIONS RULE" below).
    # (END CHANGE A1)

    # (CHANGE A2) — REPLACED SOURCE-CTE RULES with expanded BOTH PROJECTIONS version
    SOURCE-CTE RULES (the FIRST CTE that reads from physical source tables):

    BOTH PROJECTIONS RULE (CRITICAL):
    - The source CTE MUST contain TWO SEPARATE projections:
        1. effective_from_ts (derived from the column-level transformation)
        2. watermark_col     (derived per the watermark-counting rule below)
    - Do NOT merge them into a single projection.
    - Do NOT skip effective_from_ts.

    PROJECTION 1 — effective_from_ts:
    - Use the transformation expression exactly as defined in the column-level
      transformation field for the effective_from_ts column.
    - Single-source example:
        greatest(COALESCE(sp.load_date, DATE('1900-01-01'))) AS effective_from_ts
    - Multi-sat example:
        greatest(COALESCE(sp.load_date, DATE('1900-01-01')),
                 COALESCE(snp.load_date, DATE('1900-01-01')),
                 ... ) AS effective_from_ts

    PROJECTION 2 — watermark_col:
    - Single-source case (exactly ONE SAT_* in the join graph):
        <sat_alias>.${{watermark_col}} AS watermark_col
        -- NEVER wrap this in greatest() or coalesce() for single-sat tables.
    - Multi-sat case (TWO or more SAT_* tables in the join graph):
        greatest(COALESCE(<sat_a>.${{watermark_col}}, DATE('1900-01-01')),
                 COALESCE(<sat_b>.${{watermark_col}}, DATE('1900-01-01')),
                 ... ) AS watermark_col

    WHERE CLAUSE — must mirror the watermark_col expression:
    - Single-source case:
        WHERE <sat_alias>.${{watermark_col}} > ${{watermark_value}}
        -- For single-source tables: NEVER use greatest(coalesce(...)) here.
        -- Use the bare <sat_alias>.${{watermark_col}} reference.
    - Multi-sat case:
        WHERE greatest(COALESCE(<sat_a>.${{watermark_col}}, DATE('1900-01-01')),
                       COALESCE(<sat_b>.${{watermark_col}}, DATE('1900-01-01')),
                       ... ) > ${{watermark_value}}
    # (END CHANGE A2)

    INTERMEDIATE-CTE RULES (every CTE between source CTE and the final SELECT,
    regardless of how many CTE levels exist — could be 1, 2, 3, or more):
    - MUST carry `watermark_col` forward as a projected column.
    - It must NEVER be dropped at any intermediate level.

    DEDUPLICATION-CTE RULES (the CTE that contains ROW_NUMBER() over business key):
    - MUST use ORDER BY watermark_col DESC inside the ROW_NUMBER() window.
    - Do NOT use ORDER BY effective_from_ts.

    FINAL SELECT RULES (the outermost SELECT, not wrapped in a CTE):
    - MUST project: watermark_col AS effective_from_ts
    - Do NOT project effective_from_ts directly — it MUST be re-aliased from watermark_col.

    # (CHANGE A3) — UPDATED STRUCTURAL SKELETON to show both projections + variant
    STRUCTURAL SKELETON (column names omitted intentionally — 3 levels shown as
    illustration only; actual tables may have more or fewer CTE levels):

      WITH src AS (
        SELECT
          <attribute columns from sources>,
          <effective_from_ts derivation expression> AS effective_from_ts,
          -- For single-sat tables (use this line):
          <sat_alias>.${{watermark_col}} AS watermark_col
          -- For multi-sat tables (replace the line above with):
          -- greatest(COALESCE(<sat_a>.${{watermark_col}}, DATE('1900-01-01')),
          --          COALESCE(<sat_b>.${{watermark_col}}, DATE('1900-01-01')),
          --          ... ) AS watermark_col
        FROM {{catalog_name}}.{{vault_schema_name}}.<HUB_TABLE> hp
        LEFT JOIN {{catalog_name}}.{{vault_schema_name}}.<SAT_TABLE> sp
          ON <hub_hash_key join>
        WHERE <sat_alias>.${{watermark_col}} > ${{watermark_value}}
        -- For multi-sat (replace the WHERE above with):
        -- WHERE greatest(COALESCE(<sat_a>.${{watermark_col}}, DATE('1900-01-01')),
        --                COALESCE(<sat_b>.${{watermark_col}}, DATE('1900-01-01')),
        --                ... ) > ${{watermark_value}}
      ),
      <any intermediate CTEs as needed> AS (
        SELECT
          <attribute columns>,
          effective_from_ts,
          watermark_col,
          <other derivations>
        FROM src
      ),
      dedup AS (
        SELECT
          <attribute columns>,
          effective_from_ts,
          watermark_col,
          ROW_NUMBER() OVER (
            PARTITION BY {business_key_sql}
            ORDER BY watermark_col DESC
          ) AS rn
        FROM <previous_cte>
      )
      SELECT
        <attribute columns>,
        watermark_col AS effective_from_ts,
        TIMESTAMP '9999-12-31 00:00:00' AS effective_to_ts
      FROM dedup
      WHERE rn = 1
    # (END CHANGE A3)
    # ===== END CHANGE 7 =====

    # ===== CHANGE 5: Reworded "Table naming rules" block for vault/gold split =====
    Table naming rules (CRITICAL):
    - Every table reference must be of the form
      {{catalog_name}}.{{vault_schema_name}}.<table_name>  (for HUB_*, SAT_*, LINK_*)
      or
      {{catalog_name}}.{{gold_schema_name}}.<table_name>   (for DIM_*)
      using the placeholders directly (no f"..." wrapping, no quoting).
    - Do NOT hardcode catalog or schema names.
    - Do NOT use a generic {{schema_name}} placeholder.
    # ===== END CHANGE 5 =====

    FORBIDDEN COLUMNS (CRITICAL):
    - The following columns must NEVER appear as projected columns in ANY SELECT
    clause at ANY CTE level (the source CTE, intermediate CTEs, deduplication
    CTEs, and the final SELECT) — even if they are present in source tables
    and even if other CTEs use them. They must not be carried through any
    layer of the query:
        attr_hash, created_by, created_ts, last_updated_by, last_updated_ts,
        record_version, load_date, load_ts, insert_ts
    - These columns are populated by the downstream loader and must not be staged.
    - EXCEPTIONS — these ARE allowed and must be included where applicable:
        effective_from_ts, effective_to_ts
    - Banned columns MAY still appear inside WHERE clauses (e.g. for watermark
    filtering on load_date) and inside expressions aliased to an allowed name
    (e.g. greatest(COALESCE(sp.load_date, ...)) AS effective_from_ts).
    - The ban applies only to bare/qualified projections like `sp.attr_hash` or
    `d.created_ts AS CREATED_TS` in the SELECT list.

    Output:
    - A single {sql_dialect} SELECT statement (optionally with CTEs) that:
    - Reads from the appropriate source tables defined in config_json.
    - Implements all joins and transformations from the transformation and source_table fields.
    - Filters by the incremental watermark ${{watermark_value}}.
    - Deduplicates to one latest row per business key.
    - Includes effective_from_ts and effective_to_ts (sentinel) if present.
    # ===== CHANGE 6: Reworded "Output:" section dangling line for vault/gold split =====
    - References all tables using {{catalog_name}}.{{vault_schema_name}}.<table_name>
      for HUB_*, SAT_*, LINK_* and {{catalog_name}}.{{gold_schema_name}}.<table_name>
      for DIM_*.
    # ===== END CHANGE 6 =====

    config_json:
    {config_json}

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
        - Every reference inside SHA2/CONCAT_WS expressions
        - Every column referenced in PARTITION BY and ORDER BY
    - Source column references (left side of AS) MAY stay as-is from the
    source table since they reflect the actual physical column name.
    - Goal: every output column from the staging query is a clean snake_case
    identifier that can be referenced without quoting downstream.

    Now output ONLY the final {sql_dialect} query, starting with WITH or SELECT.
    """
    return apply_dialect_tokens(prompt, platform)
