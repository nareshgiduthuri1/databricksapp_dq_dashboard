import shutil
import re
import textwrap
from pathlib import Path

# ──────────────────────────────────────────────
# 1. PATHS
# ──────────────────────────────────────────────

PROJECT_ROOT = Path(__file__).resolve().parent

CONFIG_DIR = PROJECT_ROOT / "output" / "configs"

NOTEBOOK_OUT_DIR = PROJECT_ROOT / "db_notebooks"

CELL_SEP = "\n# COMMAND ----------\n\n"


# ──────────────────────────────────────────────
# 2. WIDGET CELLS
# ──────────────────────────────────────────────

DIM_WIDGETS_CELL = textwrap.dedent("""\
    # Databricks notebook source
    # DBTITLE 1,Variables

    dbutils.widgets.text("catalog_name", "allianz_coe", "Catalog Name")
    dbutils.widgets.text("gold_schema_name", "gold_c360", "Gold Schema Name")
    dbutils.widgets.text("vault_schema_name", "dvault_faker01", "Vault Schema Name")

    catalog_name = dbutils.widgets.get("catalog_name")
    gold_schema_name = dbutils.widgets.get("gold_schema_name")
    vault_schema_name = dbutils.widgets.get("vault_schema_name")
""")

FACT_WIDGETS_CELL = textwrap.dedent("""\
    # Databricks notebook source
    # DBTITLE 1,Variables

    dbutils.widgets.text("catalog_name", "allianz_coe")
    dbutils.widgets.text("gold_schema_name", "agentic_testing")
    dbutils.widgets.text("vault_schema_name", "dvault_faker01")
    dbutils.widgets.text("control_schema_name", "agentic_testing")
    dbutils.widgets.text("watermark_table_name", "application_watermark")

    catalog_name = dbutils.widgets.get("catalog_name")
    gold_schema_name = dbutils.widgets.get("gold_schema_name")
    vault_schema_name = dbutils.widgets.get("vault_schema_name")
    control_schema_name = dbutils.widgets.get("control_schema_name")
    watermark_table_name = dbutils.widgets.get("watermark_table_name")
""")


# ──────────────────────────────────────────────
# 3. HELPERS
# ──────────────────────────────────────────────

def discover_config_files(directory: Path) -> list[Path]:

    if not directory.exists():
        print(f"[WARN] Directory not found: {directory}")
        return []

    return sorted([
        f for f in directory.glob("*.py")
        if f.name != "__init__.py"
    ])


def read_file(filepath: Path) -> str:
    return filepath.read_text(encoding="utf-8")


def extract_config_dict_name(source: str) -> str | None:

    match = re.search(
        r'^([A-Z][A-Z0-9_]+)\s*=\s*\{',
        source,
        re.MULTILINE
    )

    if match:
        return match.group(1)

    return None


def is_fact_table(filename: str) -> bool:
    return filename.lower().startswith("fact_")


def is_scd1_dim(filename: str) -> bool:

    filename = filename.lower()

    return (
        filename.startswith("dim_")
        and "scd1_load" in filename
    )


def is_non_scd1_dim(filename: str) -> bool:

    filename = filename.lower()

    return (
        filename.startswith("dim_")
        and "scd1_load" not in filename
    )


def build_config_cell(filepath: Path) -> str:

    source = read_file(filepath)

    var_name = extract_config_dict_name(source)

    if not var_name:
        raise ValueError(
            f"Could not find config dict in {filepath.name}"
        )

    title = (
        var_name.replace("_CFG", "")
        if var_name.endswith("_CFG")
        else var_name
    )

    return "\n".join([
        f"# DBTITLE 1,{title}",
        source.rstrip()
    ])


def assemble_notebook(
    config_files: list[Path],
    widgets_cell: str
) -> str:

    cells = [widgets_cell.rstrip()]

    for cf in config_files:

        try:
            cell = build_config_cell(cf)

            cells.append(cell)

            print(f"  [OK] Added: {cf.name}")

        except Exception as exc:
            print(f"  [SKIP] {cf.name}: {exc}")

    return CELL_SEP.join(cells) + "\n"


# ──────────────────────────────────────────────
# 4. MAIN
# ──────────────────────────────────────────────

def db_notebook():

    NOTEBOOK_OUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    # ==========================================
    # DISCOVER CONFIG FILES
    # ==========================================

    all_configs = discover_config_files(CONFIG_DIR)

    fact_configs = []
    scd1_dim_configs = []
    scd2_dim_configs = []

    for cf in all_configs:

        filename = cf.name.lower()

        if is_fact_table(filename):
            fact_configs.append(cf)

        elif is_scd1_dim(filename):
            scd1_dim_configs.append(cf)

        elif is_non_scd1_dim(filename):
            scd2_dim_configs.append(cf)

    # ==========================================
    # 1. NON-SCD1 DIM NOTEBOOK
    # ==========================================

    print("\n=== Building scd2_dim_config notebook ===")

    non_scd1_notebook = assemble_notebook(
        scd2_dim_configs,
        DIM_WIDGETS_CELL
    )

    non_scd1_output = (
        NOTEBOOK_OUT_DIR /
        "scd2_dim_config.py"
    )

    non_scd1_output.write_text(
        non_scd1_notebook,
        encoding="utf-8"
    )

    print(f"\nWritten: {non_scd1_output}")

    # ==========================================
    # 2. COPY SCD1 FILES AS-IS
    # ==========================================

    print("\n=== Copying SCD1 files directly ===")

    for cf in scd1_dim_configs:

        destination = NOTEBOOK_OUT_DIR / cf.name

        shutil.copy2(cf, destination)

        print(f"Copied: {cf.name}")

    # ==========================================
    # 3. FACT NOTEBOOK
    # ==========================================

    print("\n=== Building fact_config notebook ===")

    fact_notebook = assemble_notebook(
        fact_configs,
        FACT_WIDGETS_CELL
    )

    fact_output = (
        NOTEBOOK_OUT_DIR /
        "fact_config.py"
    )

    fact_output.write_text(
        fact_notebook,
        encoding="utf-8"
    )

    print(f"\nWritten: {fact_output}")

    print("\nDone.")
    print("Import generated .py files into Databricks.")


# if __name__ == "__main__":
#     db_notebook()
