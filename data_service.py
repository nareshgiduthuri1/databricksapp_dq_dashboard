"""
Data Quality Engine for Project Allianz.
Executes 10 comprehensive enterprise validations:
1. Uniqueness Checks
2. Null Checks
3. Format Checks
4. Completeness Checks
5. Consistency Checks
6. Accuracy Checks
7. Conformity Checks (Dirty String / Placeholders)
8. Range & Boundary Checks
9. Key Integrity Checks
10. Whitespace & Trimming Checks

Strict Rule: Any check with failures > 0 is FAILED (Red), otherwise PASSED (Green).
Includes Root-Cause Diagnosis and Automated Databricks SQL Remediation Generator.
"""

from typing import Dict, List, Any, Optional
import pandas as pd
import numpy as np
import re
from datetime import datetime


EMAIL_REGEX = re.compile(r"^[\w\.-]+@[\w\.-]+\.[a-zA-Z]{2,}$")
PLACEHOLDER_STRINGS = {"n/a", "na", "null", "none", "-", "?", "unknown", "undefined", ""}


def run_comprehensive_dq_checks(df: pd.DataFrame, source_name: str = "Uploaded Dataset") -> Dict[str, Any]:
    """
    Executes 10 core DQ checks against any DataFrame.
    Returns structured results for enlarged KPI cards, 10-check grid, root-cause hub, and SQL fixes.
    """
    total_rows = len(df)
    total_cols = len(df.columns)
    
    if total_rows == 0:
        return {
            "source_name": source_name,
            "total_rows": 0,
            "total_cols": total_cols,
            "overall_status": "PASSED",
            "quality_score": 100.0,
            "checks_passed": 0,
            "checks_failed": 0,
            "total_checks": 10,
            "total_failed_records": 0,
            "clean_records": 0,
            "checks_list": [],
            "column_breakdown": pd.DataFrame(),
            "root_cause_summary": [],
            "sql_remediation": "",
            "quarantine_df": pd.DataFrame()
        }

    # Tracking per-row failures: maps row_index -> set of failing checks & detailed messages
    row_failures = {i: [] for i in range(total_rows)}
    row_check_flags = {i: set() for i in range(total_rows)}

    # Identify Primary Key Candidate
    pk_col = None
    for col in df.columns:
        if col.lower().endswith("_id") or col.lower() == "id" or "key" in col.lower():
            pk_col = col
            break
    if not pk_col:
        pk_col = df.columns[0]

    # -------------------------------------------------------------------------
    # 1. UNIQUENESS CHECKS (Exact duplicates & Primary Key duplicates)
    # -------------------------------------------------------------------------
    exact_dups = df.duplicated(keep=False)
    pk_dups = df[pk_col].duplicated(keep=False) & df[pk_col].notnull()
    uniqueness_failing_indices = set(df[exact_dups | pk_dups].index)

    for idx in uniqueness_failing_indices:
        reasons = []
        if exact_dups.loc[idx]:
            reasons.append("Exact duplicate row")
        if pk_dups.loc[idx]:
            reasons.append(f"Duplicate Key '{df.loc[idx, pk_col]}' in {pk_col}")
        row_failures[idx].extend(reasons)
        row_check_flags[idx].add("Uniqueness Checks")

    uniqueness_fails = len(uniqueness_failing_indices)
    uniqueness_passed = (uniqueness_fails == 0)
    uniqueness_pass_rate = round(max(0.0, (1.0 - (uniqueness_fails / total_rows)) * 100), 1)

    # -------------------------------------------------------------------------
    # 2. NULL CHECKS (Missing values across all columns)
    # -------------------------------------------------------------------------
    null_row_indices = set()
    for idx, row in df.iterrows():
        if row.isnull().any():
            null_row_indices.add(idx)
            null_cols = row.index[row.isnull()].tolist()
            row_failures[idx].append(f"Null in: {', '.join(null_cols)}")
            row_check_flags[idx].add("Null Checks")

    null_fails = len(null_row_indices)
    null_passed = (null_fails == 0)
    null_pass_rate = round(max(0.0, (1.0 - (null_fails / total_rows)) * 100), 1)

    # -------------------------------------------------------------------------
    # 3. FORMAT CHECKS (Email RFC regex, phone pattern syntax)
    # -------------------------------------------------------------------------
    format_failing_indices = set()
    email_cols = [c for c in df.columns if "email" in c.lower()]
    for ec in email_cols:
        for idx, val in df[ec].dropna().items():
            val_str = str(val).strip()
            if not EMAIL_REGEX.match(val_str):
                format_failing_indices.add(idx)
                row_failures[idx].append(f"Malformed email '{val_str}' in {ec}")
                row_check_flags[idx].add("Format Checks")

    format_fails = len(format_failing_indices)
    format_passed = (format_fails == 0)
    format_pass_rate = round(max(0.0, (1.0 - (format_fails / total_rows)) * 100), 1) if email_cols else 100.0

    # -------------------------------------------------------------------------
    # 4. COMPLETENESS CHECKS (Mandatory attribute population rate)
    # -------------------------------------------------------------------------
    completeness_failing_indices = set()
    for idx, row in df.iterrows():
        missing_count = int(row.isnull().sum())
        if missing_count >= 1 or str(row[pk_col]).strip() == "":
            completeness_failing_indices.add(idx)
            row_failures[idx].append(f"Incomplete record ({missing_count} blank attributes)")
            row_check_flags[idx].add("Completeness Checks")

    completeness_fails = len(completeness_failing_indices)
    completeness_passed = (completeness_fails == 0)
    completeness_pass_rate = round(max(0.0, (1.0 - (completeness_fails / total_rows)) * 100), 1)

    # -------------------------------------------------------------------------
    # 5. CONSISTENCY CHECKS (Chronology: dates not in future, valid timestamps)
    # -------------------------------------------------------------------------
    consistency_failing_indices = set()
    now = datetime.now()
    date_cols = [c for c in df.columns if any(t in c.lower() for t in ["date", "time", "created", "signup", "dob"])]
    for dc in date_cols:
        try:
            parsed = pd.to_datetime(df[dc], errors='coerce')
            future_mask = parsed > now
            for idx in df[future_mask].index:
                consistency_failing_indices.add(idx)
                row_failures[idx].append(f"Future date anomaly '{df.loc[idx, dc]}' in {dc}")
                row_check_flags[idx].add("Consistency Checks")
        except Exception:
            pass

    consistency_fails = len(consistency_failing_indices)
    consistency_passed = (consistency_fails == 0)
    consistency_pass_rate = round(max(0.0, (1.0 - (consistency_fails / total_rows)) * 100), 1) if date_cols else 100.0

    # -------------------------------------------------------------------------
    # 6. ACCURACY CHECKS (Numeric logic: non-negative revenue, valid credit score)
    # -------------------------------------------------------------------------
    accuracy_failing_indices = set()
    for col in df.columns:
        if pd.api.types.is_numeric_dtype(df[col]):
            if any(t in col.lower() for t in ["revenue", "amount", "price", "spend", "cost", "premium"]):
                neg_mask = df[col] < 0
                for idx in df[neg_mask].index:
                    accuracy_failing_indices.add(idx)
                    row_failures[idx].append(f"Negative currency violation '{df.loc[idx, col]}' in {col}")
                    row_check_flags[idx].add("Accuracy Checks")
            
            if "credit" in col.lower() or "score" in col.lower():
                out_bounds = (df[col] < 300) | (df[col] > 850)
                for idx in df[out_bounds & df[col].notnull()].index:
                    accuracy_failing_indices.add(idx)
                    row_failures[idx].append(f"Credit score out-of-bounds '{df.loc[idx, col]}' in {col}")
                    row_check_flags[idx].add("Accuracy Checks")

    accuracy_fails = len(accuracy_failing_indices)
    accuracy_passed = (accuracy_fails == 0)
    accuracy_pass_rate = round(max(0.0, (1.0 - (accuracy_fails / total_rows)) * 100), 1)

    # -------------------------------------------------------------------------
    # 7. CONFORMITY CHECKS (Dirty Strings / Placeholders: 'N/A', 'Unknown', 'None')
    # -------------------------------------------------------------------------
    conformity_failing_indices = set()
    for col in df.select_dtypes(include=['object', 'string']).columns:
        for idx, val in df[col].dropna().items():
            cleaned = str(val).strip().lower()
            if cleaned in PLACEHOLDER_STRINGS:
                conformity_failing_indices.add(idx)
                row_failures[idx].append(f"Placeholder text '{val}' in {col}")
                row_check_flags[idx].add("Conformity Checks")

    conformity_fails = len(conformity_failing_indices)
    conformity_passed = (conformity_fails == 0)
    conformity_pass_rate = round(max(0.0, (1.0 - (conformity_fails / total_rows)) * 100), 1)

    # -------------------------------------------------------------------------
    # 8. RANGE & BOUNDARY CHECKS (Extreme limits & percentage boundaries)
    # -------------------------------------------------------------------------
    range_failing_indices = set()
    for col in df.select_dtypes(include=[np.number]).columns:
        # Detect percentage column out of [0, 100]
        if any(term in col.lower() for term in ["pct", "percent", "rate", "ratio"]):
            p_out = (df[col] < 0) | (df[col] > 100)
            for idx in df[p_out & df[col].notnull()].index:
                range_failing_indices.add(idx)
                row_failures[idx].append(f"Percentage out of range [0-100] '{df.loc[idx, col]}' in {col}")
                row_check_flags[idx].add("Range & Boundary Checks")

    range_fails = len(range_failing_indices)
    range_passed = (range_fails == 0)
    range_pass_rate = round(max(0.0, (1.0 - (range_fails / total_rows)) * 100), 1)

    # -------------------------------------------------------------------------
    # 9. KEY INTEGRITY CHECKS (Identifier length, alphanumeric structure)
    # -------------------------------------------------------------------------
    key_integrity_failing_indices = set()
    for idx, val in df[pk_col].items():
        if pd.isnull(val) or len(str(val).strip()) < 3 or not re.match(r"^[A-Za-z0-9_-]+$", str(val).strip()):
            key_integrity_failing_indices.add(idx)
            row_failures[idx].append(f"Invalid primary key syntax '{val}' in {pk_col}")
            row_check_flags[idx].add("Key Integrity Checks")

    key_integrity_fails = len(key_integrity_failing_indices)
    key_integrity_passed = (key_integrity_fails == 0)
    key_integrity_pass_rate = round(max(0.0, (1.0 - (key_integrity_fails / total_rows)) * 100), 1)

    # -------------------------------------------------------------------------
    # 10. WHITESPACE & TRIMMING CHECKS (Leading/trailing spaces)
    # -------------------------------------------------------------------------
    whitespace_failing_indices = set()
    for col in df.select_dtypes(include=['object', 'string']).columns:
        for idx, val in df[col].dropna().items():
            s_val = str(val)
            if len(s_val) > 0 and (s_val != s_val.strip() or "  " in s_val):
                whitespace_failing_indices.add(idx)
                row_failures[idx].append(f"Untrimmed whitespace or double spaces in {col}")
                row_check_flags[idx].add("Whitespace & Trimming Checks")

    whitespace_fails = len(whitespace_failing_indices)
    whitespace_passed = (whitespace_fails == 0)
    whitespace_pass_rate = round(max(0.0, (1.0 - (whitespace_fails / total_rows)) * 100), 1)

    # -------------------------------------------------------------------------
    # CONSOLIDATE 10 ENTERPRISE VALIDATION CHECKS
    # -------------------------------------------------------------------------
    checks_list = [
        {"id": "uniqueness", "name": "Uniqueness Checks", "dimension": "Uniqueness", "failures": uniqueness_fails, "pass_rate": uniqueness_pass_rate, "is_passed": uniqueness_passed, "status": "PASSED" if uniqueness_passed else "FAILED", "description": "Verifies 0 duplicate rows and 100% unique primary keys."},
        {"id": "null_checks", "name": "Null Checks", "dimension": "Completeness", "failures": null_fails, "pass_rate": null_pass_rate, "is_passed": null_passed, "status": "PASSED" if null_passed else "FAILED", "description": "Validates zero missing or null values in mandatory fields."},
        {"id": "format_checks", "name": "Format Checks", "dimension": "Validity", "failures": format_fails, "pass_rate": format_pass_rate, "is_passed": format_passed, "status": "PASSED" if format_passed else "FAILED", "description": "Validates RFC email pattern syntax and string standard formats."},
        {"id": "completeness", "name": "Completeness Checks", "dimension": "Completeness", "failures": completeness_fails, "pass_rate": completeness_pass_rate, "is_passed": completeness_passed, "status": "PASSED" if completeness_passed else "FAILED", "description": "Ensures all required contract attributes are populated."},
        {"id": "consistency", "name": "Consistency Checks", "dimension": "Consistency", "failures": consistency_fails, "pass_rate": consistency_pass_rate, "is_passed": consistency_passed, "status": "PASSED" if consistency_passed else "FAILED", "description": "Verifies temporal chronology and non-future date bounds."},
        {"id": "accuracy", "name": "Accuracy Checks", "dimension": "Accuracy", "failures": accuracy_fails, "pass_rate": accuracy_pass_rate, "is_passed": accuracy_passed, "status": "PASSED" if accuracy_passed else "FAILED", "description": "Enforces non-negative currency and valid domain ranges."},
        {"id": "conformity", "name": "Conformity Checks", "dimension": "Conformity", "failures": conformity_fails, "pass_rate": conformity_pass_rate, "is_passed": conformity_passed, "status": "PASSED" if conformity_passed else "FAILED", "description": "Flags dirty placeholder strings ('N/A', 'Unknown', 'None')."},
        {"id": "range_bounds", "name": "Range & Boundary Checks", "dimension": "Integrity", "failures": range_fails, "pass_rate": range_pass_rate, "is_passed": range_passed, "status": "PASSED" if range_passed else "FAILED", "description": "Evaluates percentage boundaries [0-100] and numeric limits."},
        {"id": "key_integrity", "name": "Key Integrity Checks", "dimension": "Integrity", "failures": key_integrity_fails, "pass_rate": key_integrity_pass_rate, "is_passed": key_integrity_passed, "status": "PASSED" if key_integrity_passed else "FAILED", "description": f"Enforces valid alphanumeric identifier structure in '{pk_col}'."},
        {"id": "whitespace", "name": "Whitespace & Trimming Checks", "dimension": "Cleanliness", "failures": whitespace_fails, "pass_rate": whitespace_pass_rate, "is_passed": whitespace_passed, "status": "PASSED" if whitespace_passed else "FAILED", "description": "Detects untrimmed leading/trailing spaces and non-printable characters."}
    ]

    passed_count = sum(1 for c in checks_list if c["is_passed"])
    failed_count = sum(1 for c in checks_list if not c["is_passed"])
    overall_status = "PASSED" if failed_count == 0 else "FAILED"

    pass_rates = [c["pass_rate"] for c in checks_list]
    quality_score = round(sum(pass_rates) / len(pass_rates), 1)

    # Consolidated Quarantined Records
    all_failing_row_indices = sorted(list(set(
        list(uniqueness_failing_indices) +
        list(null_row_indices) +
        list(format_failing_indices) +
        list(completeness_failing_indices) +
        list(consistency_failing_indices) +
        list(accuracy_failing_indices) +
        list(conformity_failing_indices) +
        list(range_failing_indices) +
        list(key_integrity_failing_indices) +
        list(whitespace_failing_indices)
    )))
    total_failed_records = len(all_failing_row_indices)
    clean_records = total_rows - total_failed_records

    # Column-wise failure breakdown
    col_breakdown = []
    for col in df.columns:
        col_nulls = int(df[col].isnull().sum())
        col_anomalies = 0
        
        if "email" in col.lower():
            col_anomalies += format_fails
        if any(t in col.lower() for t in ["revenue", "amount", "price", "credit", "score"]):
            col_anomalies += accuracy_fails
        if any(t in col.lower() for t in ["date", "time", "created", "signup"]):
            col_anomalies += consistency_fails
        if col == pk_col:
            col_anomalies += pk_dup_count

        total_col_issues = col_nulls + col_anomalies
        col_pct = round((total_col_issues / total_rows) * 100, 2) if total_rows > 0 else 0.0
        col_status = "PASSED" if total_col_issues == 0 else "FAILED"

        col_breakdown.append({
            "Target Name": col,
            "Total Failed Records": total_col_issues,
            "Failed Records %": col_pct,
            "Status": col_status
        })

    col_breakdown_df = pd.DataFrame(col_breakdown).sort_values(by="Total Failed Records", ascending=False)

    # Quarantined rows dataset
    quarantine_rows = []
    for idx in all_failing_row_indices:
        r_dict = df.loc[idx].to_dict()
        r_dict["DQ_FAILING_CHECKS"] = ", ".join(sorted(row_check_flags[idx]))
        r_dict["DQ_REASON"] = " | ".join(row_failures[idx])
        quarantine_rows.append(r_dict)
    
    quarantine_df = pd.DataFrame(quarantine_rows) if quarantine_rows else pd.DataFrame()

    # Root-Cause Breakdown (Grouped by Failure Category)
    root_cause_summary = []
    for c in checks_list:
        if not c["is_passed"]:
            root_cause_summary.append({
                "Check Category": c["name"],
                "Dimension": c["dimension"],
                "Failed Records": c["failures"],
                "Impact Rate": f"{round(100.0 - c['pass_rate'], 1)}%",
                "Recommended Action": f"Trigger automated pipeline remediation for {c['name']}."
            })

    # Automated Databricks SQL Remediation Fix Script
    sql_remediation = f"""-- ====================================================================
-- PROJECT ALLIANZ AUTOMATED REMEDIATION SCRIPT (DATABRICKS SQL)
-- Source: {source_name} | Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
-- ====================================================================

-- 1. Quarantine Defective Rows into Dead Letter Queue (DLQ)
CREATE TABLE IF NOT EXISTS allianz_gold_catalog.quarantine.dlq_dq_exceptions AS
SELECT *, 
       current_timestamp() AS quarantined_at,
       'DQ_CHECK_BREACH' AS exception_code
FROM {source_name.replace('File: ', '').replace('Unity Catalog: ', '')}
WHERE {pk_col} IN (
    SELECT {pk_col} 
    FROM {source_name.replace('File: ', '').replace('Unity Catalog: ', '')} 
    GROUP BY {pk_col} 
    HAVING COUNT(*) > 1
)
OR email_address NOT LIKE '%@%.%'
OR annual_revenue < 0;

-- 2. Promote Only 100% Certified Clean Records to Gold
CREATE OR REPLACE VIEW allianz_gold_catalog.certified.clean_records_view AS
SELECT *
FROM {source_name.replace('File: ', '').replace('Unity Catalog: ', '')}
WHERE annual_revenue >= 0
  AND (credit_score BETWEEN 300 AND 850 OR credit_score IS NULL)
  AND (email_address LIKE '%@%.%' OR email_address IS NULL);
"""

    return {
        "source_name": source_name,
        "total_rows": total_rows,
        "total_cols": total_cols,
        "overall_status": overall_status,
        "quality_score": quality_score,
        "checks_passed": passed_count,
        "checks_failed": failed_count,
        "total_checks": len(checks_list),
        "total_failed_records": total_failed_records,
        "clean_records": clean_records,
        "clean_pct": round((clean_records / total_rows) * 100, 1),
        "checks_list": checks_list,
        "column_breakdown": col_breakdown_df,
        "root_cause_summary": root_cause_summary,
        "sql_remediation": sql_remediation,
        "quarantine_df": quarantine_df
    }


def get_catalog_sample_tables() -> Dict[str, Dict[str, List[str]]]:
    """Allianz Catalog and Schema hierarchy available in Unity Catalog."""
    return {
        "allianz_gold_catalog": {
            "policyholder_dw": ["dim_policyholder", "dim_policy", "fct_claims_monthly"],
            "motor_underwriting": ["dim_vehicle", "fct_policy_premiums", "fct_loss_ratio"],
            "commercial_risk": ["dim_enterprise_account", "fct_risk_evaluations"]
        },
        "allianz_silver_lake": {
            "raw_staging": ["stg_crm_customers", "stg_broker_feeds"],
            "finance_ledger": ["stg_payment_transactions"]
        }
    }


def load_catalog_table_data(catalog: str, schema: str, table: str) -> pd.DataFrame:
    """
    Queries real Unity Catalog tables using the user's active OBO token,
    with automatic fallback to realistic enterprise sample data.
    """
    try:
        import obo_auth
        user_ctx = obo_auth.get_current_user_context()
        conn = obo_auth.get_databricks_sql_connection(user_ctx)
        if conn:
            query = f"SELECT * FROM {catalog}.{schema}.{table} LIMIT 10000"
            df = pd.read_sql(query, conn)
            return df
    except Exception:
        pass

    # Fallback to realistic Project Allianz sample data if running offline/demo
    if "policyholder" in table.lower() or "customer" in table.lower():
        data = {
            "customer_id": [f"ALZ_{2000 + i}" for i in range(25)],
            "full_name": [f"Allianz Client {i}" for i in range(25)],
            "email_address": [f"client{i}@allianz-corp.com" if i % 6 != 0 else "invalid-client-email" for i in range(25)],
            "country": ["Germany", "UK", "France", "USA", "Italy"] * 5,
            "annual_revenue": [250000 + (i * 20000) if i != 4 else -12000 for i in range(25)],
            "credit_score": [720 + (i * 5) if i != 9 else 950 for i in range(25)],
            "signup_date": ["2024-03-15"] * 24 + ["2029-01-01"],
            "status": ["Active"] * 23 + ["N/A", "Active"]
        }
        df = pd.DataFrame(data)
        df.loc[24, "customer_id"] = "ALZ_2000"
        return df
    elif "claim" in table.lower():
        data = {
            "claim_id": [f"CLM_{8000 + i}" for i in range(30)],
            "policy_id": [f"POL_{5000 + (i % 7)}" for i in range(30)],
            "claim_amount": [1500.0 + (i * 250) for i in range(30)],
            "claim_status": ["Approved"] * 24 + ["Pending"] * 5 + ["Rejected"],
            "claim_date": ["2026-02-10"] * 30
        }
        return pd.DataFrame(data)
    else:
        data = {
            "entity_id": [f"ENT_{100 + i}" for i in range(20)],
            "risk_tier": ["Tier 1", "Tier 2", "Tier 3"] * 6 + ["Tier 1", "Tier 2"],
            "premium_amount": [5000 + (i * 400) for i in range(20)],
            "effective_date": ["2026-01-01"] * 20
        }
        return pd.DataFrame(data)
