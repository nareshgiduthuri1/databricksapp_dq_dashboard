"""
JSON to CSV Converter
=====================

Flattens nested JSON (with Column_Mappings and SourceMapping)
into a single flat CSV where each row = one column mapping.

Usage:
    python json_to_csv.py
    python json_to_csv.py --input data.json --output result.csv
    python json_to_csv.py -i input/tables.json -o output/tables.csv
"""

import json
import csv
import os
import sys
import argparse


# ============================================================
# Column definitions for the output CSV
# ============================================================

# Table-level fields (repeated on every row for that table)
TABLE_LEVEL_FIELDS = [
    "Target_Table",
    "Target_Table_Type",
    "Table_Definition",
    "Source_Data_Vault_Table",
    "Source_Logical_Table",
    "Business_Key",
    "SCD_Type",
    "Table_Type",
    "Loading_Order",
    "Dependency",
    "Retention_Type",
    "Retention_Attribute",
    "Retention_Reference_Table",
    "Watermark_Date_Columns",
    "Watermark_Time_Columns",
    "Where_Clause",
    "Contains_PII",
    "Database_Name",
    "Schema_Name",
]

# Column-level fields (from each item in Column_Mappings)
COLUMN_LEVEL_FIELDS = [
    "Target_Column",
    "Data_Type",
    "Column_Order",
    "Is_PK",
    "Is_FK",
    "Column_Definition",
]

# Source mapping fields (nested inside each Column_Mapping)
SOURCE_MAPPING_FIELDS = [
    "Source_Table",
    "Source_Column",
    "Transformation_Logic",
]


def get_csv_headers() -> list:
    """Build the full ordered list of CSV column headers."""
    return TABLE_LEVEL_FIELDS + COLUMN_LEVEL_FIELDS + SOURCE_MAPPING_FIELDS


def safe_str(value) -> str:
    """
    Convert a value to a clean string for CSV output.
    Returns empty string for None.
    """
    if value is None:
        return ""
    if isinstance(value, (list, dict)):
        return json.dumps(value, ensure_ascii=False)
    return str(value).strip()


# ============================================================
# Core flattening logic
# ============================================================

def flatten_table(table: dict) -> list:
    """
    Flatten one table entry into a list of flat row dictionaries.

    Each Column_Mapping becomes one row. Table-level fields are
    repeated on every row for that table.

    Args:
        table: A single table dictionary from the input JSON.

    Returns:
        List of flat dictionaries, one per column mapping.
    """
    rows = []

    # Extract table-level values once
    table_values = {}
    for field in TABLE_LEVEL_FIELDS:
        table_values[field] = safe_str(table.get(field))

    # Process each column mapping
    column_mappings = table.get("Column_Mappings", [])

    if not column_mappings:
        # Table with no columns — still emit one row
        row = dict(table_values)
        for field in COLUMN_LEVEL_FIELDS:
            row[field] = ""
        for field in SOURCE_MAPPING_FIELDS:
            row[field] = ""
        rows.append(row)
        return rows

    for mapping in column_mappings:
        row = dict(table_values)  # Copy table-level fields

        # Add column-level fields
        for field in COLUMN_LEVEL_FIELDS:
            row[field] = safe_str(mapping.get(field))

        # Add source mapping fields (nested one level deeper)
        source_mapping = mapping.get("SourceMapping", {}) or {}
        for field in SOURCE_MAPPING_FIELDS:
            row[field] = safe_str(source_mapping.get(field))

        rows.append(row)

    return rows


def flatten_all_tables(tables: list) -> list:
    """
    Flatten all tables from the input JSON into flat rows.

    Args:
        tables: List of table dictionaries.

    Returns:
        List of flat row dictionaries ready for CSV writing.
    """
    all_rows = []

    for table in tables:
        table_rows = flatten_table(table)
        all_rows.extend(table_rows)

    return all_rows


# ============================================================
# I/O functions
# ============================================================

def load_json(input_path: str) -> list:
    """
    Load and validate the input JSON file.

    Handles both:
      - A raw list of tables: [{ ... }, { ... }]
      - A wrapper dict: { "tables": [{ ... }, { ... }] }

    Args:
        input_path: Path to the JSON file.

    Returns:
        List of table dictionaries.
    """
    if not os.path.exists(input_path):
        print(f"ERROR: Input file not found: {input_path}")
        print(f"  Absolute path: {os.path.abspath(input_path)}")
        sys.exit(1)

    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Handle different JSON structures
    if isinstance(data, list):
        return data
    elif isinstance(data, dict):
        # Try common wrapper keys
        for key in ["tables", "Tables", "data", "records"]:
            if key in data and isinstance(data[key], list):
                return data[key]
        # Single table wrapped in a dict
        if "Target_Table" in data:
            return [data]
        # Unknown structure
        print("WARNING: Dict input without recognized list key. Wrapping as single table.")
        return [data]
    else:
        print(f"ERROR: Unexpected JSON root type: {type(data).__name__}")
        sys.exit(1)


def write_csv(rows: list, output_path: str) -> None:
    """
    Write flat rows to a CSV file.

    Args:
        rows: List of flat dictionaries.
        output_path: Path to the output CSV file.
    """
    if not rows:
        print("WARNING: No rows to write.")
        return

    headers = get_csv_headers()

    # Create output directory if needed
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=headers,
            extrasaction="ignore",  # Skip any unexpected fields
            quoting=csv.QUOTE_MINIMAL,
        )
        writer.writeheader()
        writer.writerows(rows)


# ============================================================
# Main conversion function
# ============================================================

def convert_json_to_csv(input_path: str, output_path: str) -> dict:
    """
    Full pipeline: load JSON → flatten → write CSV.

    Args:
        input_path: Path to the input JSON file.
        output_path: Path to the output CSV file.

    Returns:
        Summary dictionary with counts.
    """
    print(f"Loading JSON: {input_path}")
    tables = load_json(input_path)
    print(f"Found {len(tables)} table(s)")

    print("Flattening to rows...")
    rows = flatten_all_tables(tables)
    print(f"Generated {len(rows)} row(s)")

    print(f"Writing CSV: {output_path}")
    write_csv(rows, output_path)

    # Summary per table
    table_summary = {}
    for table in tables:
        name = table.get("Target_Table", "UNKNOWN")
        col_count = len(table.get("Column_Mappings", []))
        table_summary[name] = col_count

    summary = {
        "input_file": input_path,
        "output_file": output_path,
        "table_count": len(tables),
        "total_rows": len(rows),
        "tables": table_summary,
    }

    return summary


# ============================================================
# CLI entry point
# ============================================================

def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Convert nested JSON table definitions to flat CSV.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python json_to_csv.py\n"
            "  python json_to_csv.py -i tables.json -o tables.csv\n"
            "  python json_to_csv.py --input input/data.json --output output/flat.csv\n"
        ),
    )
    parser.add_argument(
        "--input", "-i",
        default="input/normalized_input_c360_updated.json",
        help="Path to input JSON file",
    )
    parser.add_argument(
        "--output", "-o",
        default="output/tables_flat.csv",
        help="Path to output CSV file",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    print("=" * 55)
    print("  JSON → CSV Converter")
    print("=" * 55)
    print()

    input_abs = "./input/erwin_customer360_final_mapping_file_08052026.json"
    output_abs = "./output/erwin_customer360_final_mapping_file_08052026.csv"

    summary = convert_json_to_csv(input_abs, output_abs)

    print()
    print("─" * 55)
    print("  Summary")
    print("─" * 55)
    print(f"  Tables processed : {summary['table_count']}")
    print(f"  Total CSV rows   : {summary['total_rows']}")
    print()

    for table_name, col_count in summary["tables"].items():
        print(f"    {table_name}: {col_count} columns")

    print()
    print(f"  Output: {os.path.abspath(summary['output_file'])}")
    print("=" * 55)