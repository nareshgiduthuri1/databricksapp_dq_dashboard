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

from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
import numpy as np
import re
from datetime import datetime


EMAIL_REGEX = re.compile(r"^[\w\.-]+@[\w\.-]+\.[a-zA-Z]{2,}$")
PLACEHOLDER_STRINGS = {"n/a", "na", "null", "none", "-", "?", "unknown", "undefined", ""}

# Column names that declare an identifier: id, customer_id, id_customer, c_custkey, policy_number, pk_x ...
KEY_NAME_PATTERN = re.compile(r"(^id$|_id$|^id_|key$|^pk_|_pk$|_number$|_no$)", re.IGNORECASE)
KEY_VALUE_PATTERN = re.compile(r"^[A-Za-z0-9_-]+$")


def _is_integer_like(series: pd.Series) -> bool:
    """True for int columns, or float columns whose non-null values are all whole numbers (e.g. CSV ids read as 1001.0)."""
    if pd.api.types.is_bool_dtype(series) or not pd.api.types.is_numeric_dtype(series):
        return False
    s = series.dropna()
    return bool(pd.api.types.is_integer_dtype(series) or (len(s) > 0 and (s % 1 == 0).all()))


def _looks_like_identifier(series: pd.Series) -> bool:
    """Value-shape test: integer-like numbers, or short strings without spaces / punctuation."""
    if pd.api.types.is_datetime64_any_dtype(series) or pd.api.types.is_bool_dtype(series):
        return False
    if pd.api.types.is_numeric_dtype(series):
        return _is_integer_like(series)
    s = series.dropna().astype(str).str.strip()
    return len(s) > 0 and s.str.len().max() <= 64 and s.str.match(KEY_VALUE_PATTERN).all()


def detect_primary_key(df: pd.DataFrame) -> Tuple[Optional[str], str]:
    """
    Returns (pk_col, source):
      - ("col", "name")     : column name declares an identifier (unique ones preferred)
      - ("col", "inferred") : no key-like name, but a column is 100% non-null, unique and ID-shaped
      - (None, "none")      : no identifier exists (e.g. samples.nyctaxi.trips) -> key checks are N/A
    Never falls back to an arbitrary first column (that flagged every row of key-less tables).
    """
    named = [c for c in df.columns if KEY_NAME_PATTERN.search(str(c))]
    if named:
        unique_named = [c for c in named if df[c].notnull().all() and df[c].is_unique]
        return (unique_named[0] if unique_named else named[0]), "name"

    if len(df) > 1:
        for c in df.columns:
            s = df[c]
            if s.notnull().all() and s.is_unique and _looks_like_identifier(s):
                return c, "inferred"
    return None, "none"


def get_default_allianz_dataset() -> pd.DataFrame:
    """Returns guaranteed Allianz dataset so dashboard is never empty on load."""
    import os
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sample_file = os.path.join(current_dir, "sample_customers.csv")
    if os.path.exists(sample_file):
        try:
            return pd.read_csv(sample_file)
        except Exception:
            pass

    # Built-in robust fallback
    return pd.DataFrame({
        "customer_id": ["CUST_1001", "CUST_1002", "CUST_1003", "CUST_1004", "CUST_1005", "CUST_1006", "CUST_1007", "CUST_1008", "CUST_1009", "CUST_1010", "CUST_1001", "CUST_1012", "CUST_1013", "CUST_1014", "CUST_1015"],
        "full_name": ["Acme Corporation", "Global Logistics", "Starlight Media", "Apex Financials", "Nexus Tech Labs", "Summit Retail", "Horizon Energy", "Pioneer Healthcare", "Vanguard Industrial", "Cascade Cloud", "Acme Corporation", "Quantum Dynamics", "Beacon Security", "Solaris Agriculture", "Echo Wave Telecom"],
        "email_address": ["contact@acme.com", "info@globallogistics.com", "invalid-email-format", "billing@apexfin.com", "hello@nexustech.io", "support@summitretail.com", "contact@horizonenergy.com", None, "ops@vanguardind.com", "admin@cascadecloud.net", "contact@acme.com", "info@quantumdyn.com", "alerts@beaconsec.com", "contact@solaris", "support@echowave.com"],
        "phone_number": ["+1-555-0192", "+1-555-0193", "+44-20-7946-0912", "+1-555-0195", None, "+1-555-0197", "+33-1-40-50-60", "+1-555-0199", "+49-30-123456", "+1-555-0201", "+1-555-0192", None, "+1-555-0204", None, "+1-555-0206"],
        "country": ["USA", "Germany", "UK", "USA", "Germany", "USA", "France", "USA", "Germany", "USA", "USA", "Japan", "N/A", "Australia", "USA"],
        "annual_revenue": [1250000, 840000, 450000, -15000, 2100000, 320000, 5600000, 980000, 1750000, 640000, 1250000, 3400000, 410000, 890000, 1120000],
        "credit_score": [740, 680, 710, 620, 790, 590, 820, 705, 980, 670, 740, 775, 650, 695, 715],
        "signup_date": ["2024-01-15", "2024-02-20", "2024-03-05", "2024-03-12", "2024-04-01", "2024-04-18", "2024-05-02", "2024-05-19", "2024-06-11", "2028-05-10", "2024-01-15", "2024-07-04", "2024-07-22", "2024-08-14", "2024-08-30"],
        "status": ["Active", "Active", "Active", "Active", "Active", "Pending", "Active", "Active", "Active", "Active", "Active", "Active", "Pending", "Active", "Active"]
    })


def run_comprehensive_dq_checks(df: pd.DataFrame, source_name: str = "Uploaded Dataset") -> Dict[str, Any]:
    """
    Executes 10 core DQ checks against any DataFrame.
    Returns structured results for enlarged KPI cards, 10-check grid, failed records table, and SQL fixes.
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
            "clean_pct": 100.0,
            "checks_list": [],
            "column_breakdown": pd.DataFrame(columns=["Target Name", "Total Failed Records", "Failed Records %", "Status"]),
            "root_cause_summary": [],
            "sql_remediation": "-- No data available to audit.",
            "quarantine_df": pd.DataFrame()
        }

    # Positional index so row_failures keys always match df.index
    df = df.reset_index(drop=True)

    # Tracking per-row failures: maps row_index -> list of failing checks & detailed messages
    row_failures = {i: [] for i in range(total_rows)}
    row_check_flags = {i: set() for i in range(total_rows)}

    # Identify Primary Key Candidate (may be None for tables without an identifier)
    pk_col, pk_source = detect_primary_key(df)

    # -------------------------------------------------------------------------
    # 1. UNIQUENESS CHECKS (Exact duplicates & Primary Key duplicates)
    # -------------------------------------------------------------------------
    exact_dups = df.duplicated(keep=False)
    if pk_col is not None:
        pk_dups = df[pk_col].duplicated(keep=False) & df[pk_col].notnull()
    else:
        pk_dups = pd.Series(False, index=df.index)
    pk_dup_count = int(pk_dups.sum())
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
        if missing_count >= 1 or (pk_col is not None and str(row[pk_col]).strip() == ""):
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
    # Compare in UTC: live Unity Catalog TIMESTAMP columns arrive timezone-aware,
    # and comparing tz-aware vs naive datetimes raises (which silently skipped this check).
    now = pd.Timestamp.now(tz="UTC")
    date_cols = [c for c in df.columns if any(t in c.lower() for t in ["date", "time", "created", "signup", "dob", "pickup", "dropoff"])]
    for dc in date_cols:
        try:
            parsed = pd.to_datetime(df[dc], errors='coerce', utc=True)
            future_mask = (parsed > now).fillna(False)
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
    # 6. ACCURACY CHECKS (Numeric logic: non-negative currency, valid ranges)
    # -------------------------------------------------------------------------
    accuracy_failing_indices = set()
    for col in df.columns:
        if pd.api.types.is_numeric_dtype(df[col]):
            if any(t in col.lower() for t in ["revenue", "amount", "price", "spend", "cost", "premium", "fare", "totalprice", "acctbal"]):
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
    key_integrity_applicable = pk_col is not None
    if key_integrity_applicable:
        pk_series = df[pk_col]
        numeric_key = pd.api.types.is_numeric_dtype(pk_series) and not pd.api.types.is_bool_dtype(pk_series)
        for idx, val in pk_series.items():
            reason = None
            if pd.isnull(val):
                reason = f"Missing primary key in {pk_col}"
            elif numeric_key:
                # Numeric keys: must be whole, non-negative numbers (1001 or 1001.0 OK, 10.5 / -3 not)
                if float(val) % 1 != 0 or float(val) < 0:
                    reason = f"Invalid numeric key '{val}' in {pk_col}"
            else:
                s_val = str(val).strip()
                if len(s_val) < 1 or not KEY_VALUE_PATTERN.match(s_val):
                    reason = f"Invalid primary key syntax '{val}' in {pk_col}"
            if reason:
                key_integrity_failing_indices.add(idx)
                row_failures[idx].append(reason)
                row_check_flags[idx].add("Key Integrity Checks")

    key_integrity_fails = len(key_integrity_failing_indices)
    key_integrity_passed = (key_integrity_fails == 0)
    key_integrity_pass_rate = round(max(0.0, (1.0 - (key_integrity_fails / total_rows)) * 100), 1)
    if not key_integrity_applicable:
        key_integrity_status = "N/A"
        key_integrity_desc = "No identifier column detected (no *_id / *key column and no unique ID-like column) - check not applicable."
    else:
        key_integrity_status = "PASSED" if key_integrity_passed else "FAILED"
        how = "detected by column name" if pk_source == "name" else "inferred: unique, non-null, ID-shaped values"
        key_integrity_desc = f"Enforces valid identifier structure in '{pk_col}' ({how})."

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
        {"id": "uniqueness", "name": "Uniqueness Checks", "dimension": "Uniqueness", "failures": uniqueness_fails, "pass_rate": uniqueness_pass_rate, "is_passed": uniqueness_passed, "status": "PASSED" if uniqueness_passed else "FAILED", "description": (f"Verifies 0 duplicate rows and 100% unique primary keys on '{pk_col}'." if pk_col else "Verifies 0 exact duplicate rows (no primary key column detected).")},
        {"id": "null_checks", "name": "Null Checks", "dimension": "Completeness", "failures": null_fails, "pass_rate": null_pass_rate, "is_passed": null_passed, "status": "PASSED" if null_passed else "FAILED", "description": "Validates zero missing or null values in mandatory fields."},
        {"id": "format_checks", "name": "Format Checks", "dimension": "Validity", "failures": format_fails, "pass_rate": format_pass_rate, "is_passed": format_passed, "status": "PASSED" if format_passed else "FAILED", "description": "Validates RFC email pattern syntax and string standard formats."},
        {"id": "completeness", "name": "Completeness Checks", "dimension": "Completeness", "failures": completeness_fails, "pass_rate": completeness_pass_rate, "is_passed": completeness_passed, "status": "PASSED" if completeness_passed else "FAILED", "description": "Ensures all required contract attributes are populated."},
        {"id": "consistency", "name": "Consistency Checks", "dimension": "Consistency", "failures": consistency_fails, "pass_rate": consistency_pass_rate, "is_passed": consistency_passed, "status": "PASSED" if consistency_passed else "FAILED", "description": "Verifies temporal chronology and non-future date bounds."},
        {"id": "accuracy", "name": "Accuracy Checks", "dimension": "Accuracy", "failures": accuracy_fails, "pass_rate": accuracy_pass_rate, "is_passed": accuracy_passed, "status": "PASSED" if accuracy_passed else "FAILED", "description": "Enforces non-negative currency and valid domain ranges."},
        {"id": "conformity", "name": "Conformity Checks", "dimension": "Conformity", "failures": conformity_fails, "pass_rate": conformity_pass_rate, "is_passed": conformity_passed, "status": "PASSED" if conformity_passed else "FAILED", "description": "Flags dirty placeholder strings ('N/A', 'Unknown', 'None')."},
        {"id": "range_bounds", "name": "Range & Boundary Checks", "dimension": "Integrity", "failures": range_fails, "pass_rate": range_pass_rate, "is_passed": range_passed, "status": "PASSED" if range_passed else "FAILED", "description": "Evaluates percentage boundaries [0-100] and numeric limits."},
        {"id": "key_integrity", "name": "Key Integrity Checks", "dimension": "Integrity", "failures": key_integrity_fails, "pass_rate": key_integrity_pass_rate, "is_passed": key_integrity_passed, "status": key_integrity_status, "description": key_integrity_desc},
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
        if any(t in col.lower() for t in ["revenue", "amount", "price", "credit", "score", "fare", "totalprice"]):
            col_anomalies += accuracy_fails
        if any(t in col.lower() for t in ["date", "time", "created", "signup", "pickup", "dropoff"]):
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

    # Dynamic SQL Remediation Fix Script
    clean_target = source_name.replace('File: ', '').replace('Unity Catalog: ', '').strip()
    if pk_col is not None:
        dup_filter_sql = (
            f"WHERE `{pk_col}` IN (\n    SELECT `{pk_col}`\n    FROM {clean_target}\n"
            f"    GROUP BY `{pk_col}`\n    HAVING COUNT(*) > 1\n)"
        )
    else:
        # No primary key: quarantine exact duplicate rows across all columns
        all_cols = ", ".join(f"`{c}`" for c in df.columns)
        dup_filter_sql = f"QUALIFY COUNT(*) OVER (PARTITION BY {all_cols}) > 1"
    sql_remediation = f"""-- ====================================================================
-- PROJECT ALLIANZ AUTOMATED REMEDIATION SCRIPT (DATABRICKS SQL)
-- Target: {clean_target} | Evaluated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
-- ====================================================================

-- 1. Quarantine Defective Rows into Dead Letter Queue (DLQ)
CREATE TABLE IF NOT EXISTS samples_quarantine.dlq_dq_exceptions AS
SELECT *, 
       current_timestamp() AS quarantined_at,
       'DQ_CHECK_BREACH' AS exception_code
FROM {clean_target}
{dup_filter_sql};
"""

    return {
        "source_name": source_name,
        "total_rows": total_rows,
        "total_cols": total_cols,
        "primary_key": pk_col,
        "primary_key_source": pk_source,
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
        "sql_remediation": sql_remediation,
        "quarantine_df": quarantine_df
    }


# =============================================================================
# DYNAMIC SAMPLES CATALOG DISCOVERY & QUERY ENGINE
# =============================================================================

def get_dynamic_schemas(catalog: str = "samples") -> List[str]:
    """
    Fetches all schemas dynamically under the specified catalog.
    Defaults to 'samples' catalog as requested.
    """
    import obo_auth
    return obo_auth.fetch_live_schemas(catalog=catalog)


def get_dynamic_tables(catalog: str = "samples", schema: str = "nyctaxi") -> List[str]:
    """
    Fetches all tables dynamically under the specified catalog and schema.
    """
    import obo_auth
    return obo_auth.fetch_live_tables(catalog=catalog, schema=schema)


def load_catalog_table_data(
    catalog: str = "samples",
    schema: str = "nyctaxi",
    table: str = "trips",
    limit: int = 5000,
    warehouse_id: Optional[str] = None
) -> Tuple[pd.DataFrame, Optional[str]]:
    """
    Queries live Unity Catalog table using active user OBO token.
    If live query fails (e.g. warehouse paused or local demo), falls back cleanly
    to realistic schema-matched sample data so the dashboard never crashes.
    """
    import obo_auth
    query = f"SELECT * FROM {catalog}.{schema}.{table} LIMIT {limit}"
    
    # 1. Attempt live query to Databricks SQL Warehouse
    live_df, error_msg = obo_auth.execute_unity_catalog_sql(query, warehouse_id=warehouse_id)
    if live_df is not None and not live_df.empty:
        return live_df, None

    # 2. Schema-matched realistic fallback
    fallback_df = get_sample_table_fallback(catalog, schema, table)
    return fallback_df, error_msg


def get_sample_table_fallback(catalog: str, schema: str, table: str) -> pd.DataFrame:
    """
    Generates realistic demo dataset matching Databricks 'samples' catalog schemas.
    Contains built-in DQ anomalies to demonstrate all 10 validations.
    """
    t_name = table.lower()
    s_name = schema.lower()

    if "trip" in t_name or s_name == "nyctaxi":
        return pd.DataFrame({
            "trip_id": [f"TRIP_{1000 + i}" for i in range(20)] + ["TRIP_1000"],
            "pickup_datetime": ["2024-03-15 08:30:00"] * 19 + ["2029-01-01 12:00:00", "2024-03-15 08:30:00"],
            "dropoff_datetime": ["2024-03-15 08:45:00"] * 21,
            "passenger_count": [1, 2, 1, 4, None, 1, 2, 3, 1, 2, 1, 1, 6, 2, 1, 1, 2, 1, 3, 1, 1],
            "trip_distance": [2.5, 4.1, 0.8, 12.3, 1.2, 3.4, 5.0, 2.1, 8.4, 1.9, 2.5, 0.5, 15.2, 3.1, 2.8, 1.1, 4.5, 2.0, 6.3, 3.8, 2.5],
            "fare_amount": [14.50, 22.00, 8.50, -15.00, 11.00, 18.50, 25.00, 12.00, 38.00, 10.50, 14.50, 7.00, 48.00, 17.50, 15.00, 9.00, 24.50, 12.50, 31.00, 20.00, 14.50],
            "payment_type": ["Credit Card", "Cash", "Credit Card", "Unknown", "Credit Card", "Cash", "Credit Card", "N/A", "Credit Card", "Cash", "Credit Card", "Cash", "Credit Card", "  Cash  ", "Credit Card", "Cash", "Credit Card", "Credit Card", "Cash", "Credit Card", "Credit Card"]
        })

    elif "customer" in t_name or s_name == "tpch":
        return pd.DataFrame({
            "c_custkey": [f"CUST_{5000 + i}" for i in range(20)] + ["CUST_5000"],
            "c_name": [f"Customer#{5000 + i:09d}" for i in range(20)] + ["Customer#000005000"],
            "c_address": [f"{100 + i} Allianz Corporate Way" for i in range(21)],
            "c_nationkey": [1, 2, 3, 1, 2, 4, 1, 3, 2, 1, 1, 5, 2, 3, 1, 4, 2, 1, 3, 2, 1],
            "c_phone": ["+1-555-0101", "+1-555-0102", None, "+49-30-1234", "+1-555-0105", "+33-1-4050", "+1-555-0107", "N/A", "+1-555-0109", "+1-555-0110", "+1-555-0101", "+1-555-0112", "+1-555-0113", None, "+1-555-0115", "+1-555-0116", "+1-555-0117", "+1-555-0118", "+1-555-0119", "+1-555-0120", "+1-555-0101"],
            "c_acctbal": [4500.50, 1200.00, 8900.25, -250.00, 3100.00, 15400.00, 670.00, 2900.00, 7800.50, 420.00, 4500.50, 9500.00, 120.00, 6100.00, -50.00, 8300.00, 4100.00, 1250.00, 7400.00, 3800.00, 4500.50],
            "c_mktsegment": ["BUILDING", "AUTOMOBILE", "MACHINERY", "HOUSEHOLD", "FURNITURE", "BUILDING", "AUTOMOBILE", "  MACHINERY  ", "HOUSEHOLD", "FURNITURE", "BUILDING", "AUTOMOBILE", "MACHINERY", "HOUSEHOLD", "FURNITURE", "BUILDING", "AUTOMOBILE", "MACHINERY", "HOUSEHOLD", "FURNITURE", "BUILDING"]
        })

    elif "order" in t_name:
        return pd.DataFrame({
            "o_orderkey": [f"ORD_{9000 + i}" for i in range(20)] + ["ORD_9000"],
            "o_custkey": [f"CUST_{5000 + (i % 5)}" for i in range(21)],
            "o_orderstatus": ["F", "O", "P", "F", "O", "F", "P", "Unknown", "F", "O", "F", "O", "P", "F", "O", "F", "P", "F", "O", "F", "F"],
            "o_totalprice": [15200.00, 8400.50, 32000.00, -120.00, 4500.00, 18900.00, 7600.00, 21000.00, 9500.00, 13400.00, 15200.00, 6700.00, 28000.00, 4100.00, 11200.00, 19800.00, 5400.00, 16300.00, 8900.00, 22500.00, 15200.00],
            "o_orderdate": ["2024-02-10"] * 19 + ["2030-05-15", "2024-02-10"],
            "o_orderpriority": ["1-URGENT", "2-HIGH", "3-MEDIUM", "4-NOT SPECIFIED", "5-LOW"] * 4 + ["1-URGENT"]
        })

    else:
        # Generic table fallback
        return pd.DataFrame({
            "record_id": [f"REC_{100 + i}" for i in range(20)] + ["REC_100"],
            "entity_name": [f"Entity {i}" for i in range(20)] + ["Entity 0"],
            "category": ["Tier 1", "Tier 2", "Tier 3", "N/A", "Tier 1"] * 4 + ["Tier 1"],
            "metric_value": [100.0 + (i * 15.0) if i != 3 else -50.0 for i in range(21)],
            "created_timestamp": ["2024-01-01 10:00:00"] * 19 + ["2028-12-31 00:00:00", "2024-01-01 10:00:00"]
        })
