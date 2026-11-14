"""
generation_profiles
====================
Target-model generation profiles for the STTM-to-Code pipeline.

The pipeline supports multiple *target* models. Until now only the
Dimensional model (DIM / FACT) was produced; Business Vault (BV) adds a
second target whose SCD-2 "master" tables and SCD-1 "xref" tables use a
different, smaller set of audit / SCD-tracking columns and different
column names.

Only a handful of things differ between target models:
  * which target columns count as audit/SCD columns (excluded from the
    business `attribute_cols`),
  * the `effective_from` / record-version (flag) config column NAMES,
  * the audit tail appended to `insert_cols`,
  * the audit-column name swaps applied to the stage-SQL prompt.

Everything else (parsing, config structure, stage-SQL skeleton, notebook
assembly) is shared. The Dimensional profile reproduces the pipeline's
original hard-coded literals EXACTLY, so the Dimensional output is
unchanged.

The active target model is derived from `generation.type_of_conversion`
in config.yaml (e.g. "3NF to Dimensional" -> Dimensional,
"Data Vault to Business Vault" -> Business Vault).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Set

import config_loader

# ── Target-model identifiers ─────────────────────────────────────────
TARGET_DIMENSIONAL = "Dimensional"
TARGET_BUSINESS_VAULT = "Business Vault"
# Raw Data Vault target (Bronze -> Data Vault): hub / sat / link tables.
# It does NOT use the SCD/audit profile fields below; its generators key
# purely off get_target_model() == TARGET_RAW_DATA_VAULT.
TARGET_RAW_DATA_VAULT = "Raw Data Vault"

DEFAULT_CONVERSION = "Data Vault to Dimensional"


@dataclass(frozen=True)
class GenerationProfile:
    """Everything that varies between target models."""

    target_model: str
    # Target columns treated as audit/SCD columns (lower-cased). Excluded
    # from business attribute_cols in both SCD-1 and SCD-2 generators.
    audit_cols: Set[str]
    # SCD-2 config column NAMES emitted in the config dict.
    effective_from_col: str
    record_version_col: str
    # Ordered audit tail appended to insert_cols.
    scd2_insert_audit_tail: List[str]
    scd1_insert_audit_tail: List[str]
    # Prompt token renames applied ONLY for non-Dimensional targets.
    # Empty for Dimensional -> stage-SQL prompt stays byte-identical.
    audit_renames: Dict[str, str] = field(default_factory=dict)
    # Emitted as a "modelling_pattern" config key when set (BV only).
    modelling_pattern: str | None = None
    # Config-dict KEY name used for the record-version / active-flag entry:
    #   Dimensional -> "record_version_col"
    #   Business Vault -> "current_flag_col"
    record_version_key: str = "record_version_col"


# ── Dimensional (ORIGINAL behaviour — literals unchanged) ─────────────
_DIMENSIONAL = GenerationProfile(
    target_model=TARGET_DIMENSIONAL,
    audit_cols={
        "created_ts", "created_by", "updated_ts", "updated_by",
        "last_updated_ts", "last_updated_by", "effective_from_ts",
        "effective_to_ts", "record_version", "attr_hash",
        "load_date", "load_ts", "insert_ts",
    },
    effective_from_col="effective_from_ts",
    record_version_col="record_version",
    scd2_insert_audit_tail=[
        "attr_hash",
        "effective_from_ts",
        "effective_to_ts",
        "record_version",
        "created_by",
        "created_ts",
        "last_updated_by",
        "last_updated_ts",
    ],
    # SCD-1 tail is handled inside dim_scd1_generator's template
    # (business_keys + attribute_cols + attr_hash). Kept here for
    # completeness/consumers that want it.
    scd1_insert_audit_tail=["attr_hash"],
    audit_renames={},
)

# ── Business Vault ────────────────────────────────────────────────────
# Master (SCD-2) audit columns : effective_from, effective_to,
#                                current_active_flag.
# Xref  (SCD-1) audit columns  : load_timestamp.
_BUSINESS_VAULT = GenerationProfile(
    target_model=TARGET_BUSINESS_VAULT,
    audit_cols={
        "effective_from", "effective_to", "current_active_flag",
        "load_timestamp",
    },
    effective_from_col="effective_from",
    record_version_col="current_active_flag",
    scd2_insert_audit_tail=[
        "effective_from",
        "effective_to",
        "current_active_flag",
    ],
    scd1_insert_audit_tail=["load_timestamp"],
    audit_renames={
        # NOTE: order matters if applied via str.replace — the "_ts"
        # variants are full tokens and unambiguous, so a plain replace is
        # safe (there is no bare "effective_from"/"effective_to" in the
        # Dimensional prompt text).
        "effective_from_ts": "effective_from",
        "effective_to_ts": "effective_to",
        "record_version": "current_active_flag",
    },
    modelling_pattern="business_vault",
    record_version_key="current_flag_col",
)

_PROFILES: Dict[str, GenerationProfile] = {
    TARGET_DIMENSIONAL: _DIMENSIONAL,
    TARGET_BUSINESS_VAULT: _BUSINESS_VAULT,
}


# ── Resolution helpers ────────────────────────────────────────────────

def target_model_from_conversion(conversion_type: str) -> str:
    """Map a 'X to Y' conversion string to a target-model identifier.

    Rule: look at the text AFTER the last 'to'. If it mentions
    'business vault' -> Business Vault; otherwise -> Dimensional
    (the safe default that preserves existing behaviour).
    """
    text = str(conversion_type or "").strip().lower()
    # Take the segment after the final ' to ' if present.
    parts = re.split(r"\bto\b", text)
    tail = parts[-1] if parts else text
    if "business vault" in tail or "business_vault" in tail:
        return TARGET_BUSINESS_VAULT
    # Order matters: check "business vault" first. The Raw Data Vault
    # target accepts either phrasing: "... to Data Vault" / "... to Raw
    # Vault" / "... to Raw Data Vault".
    if (
        "data vault" in tail or "data_vault" in tail
        or "raw vault" in tail or "raw_vault" in tail
    ):
        return TARGET_RAW_DATA_VAULT
    return TARGET_DIMENSIONAL


def get_target_model() -> str:
    """Read the active target model from config.yaml (DV/Dimensional default)."""
    try:
        conv = config_loader.get(
            "generation.type_of_conversion", DEFAULT_CONVERSION
        ) or DEFAULT_CONVERSION
    except Exception:
        conv = DEFAULT_CONVERSION
    return target_model_from_conversion(conv)


def get_profile(target_model: str | None = None) -> GenerationProfile:
    """Return the profile for the given (or active) target model."""
    tm = target_model or get_target_model()
    return _PROFILES.get(tm, _DIMENSIONAL)


# Appended to the SCD-2 / SCD-1 stage-SQL prompt for Business Vault ONLY.
# Keeps the shared dimensional prompt's structure (watermark CTE, schema
# placeholders) while enforcing source fidelity against the mapping.
BV_SOURCE_FIDELITY_RULES = """\
============================================================================
BUSINESS VAULT SOURCE-FIDELITY RULES (CRITICAL)
============================================================================
- The column-level `transformation` (the mapping's Transformation Rule) is the
  SINGLE SOURCE OF TRUTH for all joins, conditions and expressions. Reproduce
  them EXACTLY; only adjust to valid dialect syntax.
- NEVER merge two source tables into a single name. A `source_table` value like
  "sat_home_crm, sat_home_sap" denotes TWO SEPARATE source tables (a CRM source
  and a SAP source); model them separately. NEVER emit a fused name such as
  "sat_home_crm_sat_home_sap".
- Do NOT invent tables, columns, joins, or predicates that are not present in
  config_json. If something is missing, omit it — never fabricate.
- Project ONLY the target columns present in config_json (plus the standard
  effective_from / effective_to audit columns produced by the SCD-2 wrapper).
- Preserve EVERY join predicate and WHERE / record_source / filter condition
  present in the transformation — never drop them.
- Prefer a clean, consistent structure: one CTE per distinct source system
  (e.g. a CRM CTE and a SAP CTE), then a combining `src` CTE, then dedup, then
  the final SELECT — mirroring the transformation's own structure.
"""


# ── Business Vault audit / system column detection (concept-based) ────
# Naming-agnostic across data products: matches effective_from* /
# effective_to* / current_*flag / load_(ts|timestamp|date). Deliberately
# does NOT match source-backed business flags (fraud_flag, total_loss_flag,
# ...) or effective_loss_date, since those don't start with the audit
# concept prefixes.
_BV_AUDIT_PATTERNS = [
    re.compile(r"^effective_from"),
    re.compile(r"^effective_to"),
    re.compile(r"^current_.*flag"),
    re.compile(r"^load_(ts|timestamp|date)"),
]


def bv_is_audit_col(name: str) -> bool:
    """True if the (BV) target column is an audit/system column by concept."""
    n = str(name or "").strip().lower()
    return bool(n) and any(p.search(n) for p in _BV_AUDIT_PATTERNS)


def bv_audit_columns(names) -> list:
    """Ordered, de-duplicated list of BV audit column names (lowercased)
    detected among the given target column names."""
    out, seen = [], set()
    for n in names or []:
        nl = str(n or "").strip().lower()
        if nl and nl not in seen and bv_is_audit_col(nl):
            seen.add(nl)
            out.append(nl)
    return out


def bv_effective_from_col(names, default: str = "effective_from") -> str:
    """The mapping's effective_from* column name, else the default."""
    for n in names or []:
        nl = str(n or "").strip().lower()
        if nl.startswith("effective_from"):
            return nl
    return default


def bv_current_flag_col(names, default: str = "current_active_flag") -> str:
    """The mapping's current_*flag column name, else the default."""
    for n in names or []:
        nl = str(n or "").strip().lower()
        if re.search(r"^current_.*flag", nl):
            return nl
    return default


def append_bv_fidelity_rules(text: str, profile: GenerationProfile | None = None) -> str:
    """Append the BV source-fidelity rules for Business Vault only.

    No-op for every other target model, so the Dimensional / Raw-Vault
    prompts stay byte-identical.
    """
    prof = profile or get_profile()
    if prof.target_model == TARGET_BUSINESS_VAULT:
        return text + "\n" + BV_SOURCE_FIDELITY_RULES
    return text


def apply_audit_renames(text: str, profile: GenerationProfile | None = None) -> str:
    """Apply a profile's audit-name swaps to a prompt/SQL string.

    No-op for Dimensional (empty rename map) -> guarantees the
    Dimensional prompt/SQL is byte-identical to the original.
    """
    if not text:
        return text
    prof = profile or get_profile()
    for old, new in prof.audit_renames.items():
        text = text.replace(old, new)
    return text
