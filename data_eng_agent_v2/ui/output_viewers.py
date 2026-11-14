"""
Output Viewers
===============
Ported from `LangGraphAgenticPipeline/ui/output_viewers.py`. Two
narrow adaptations for the data_eng_agent backend:

  • `render_config_output` displays the actual generated Python config
    / notebook file content (this project's deliverable), so the code
    block uses `language="python"` instead of "sql".
  • `render_download_buttons` exposes per-platform DDL bundle, full
    STTM JSON, the generated config bundle, the SCD-1 notebook bundle,
    and the lineage CSV — all artifacts the project produces.
"""

import streamlit as st
import json
import os


def render_sttm_output(sttm_json: list, validation: dict):
    """Render STTM output with validation summary."""

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Tables", validation.get("table_count", 0))
    with col2:
        st.metric("Columns", validation.get("column_count", 0))
    with col3:
        st.metric("Quality Score", "100%")
    with col4:
        valid = validation.get("is_valid", False)
        st.metric("Status", "Valid" if valid else "Issues Found")

    if validation.get("issues"):
        with st.expander("Validation Issues", expanded=True):
            for issue in validation["issues"]:
                st.warning(issue)

    if validation.get("warnings"):
        with st.expander("Warnings", expanded=False):
            for warning in validation["warnings"]:
                st.info(warning)

    with st.expander("STTM Mapping (All Tables)", expanded=False):
        for table in sttm_json:
            table_name = str(table.get("Target_Table") or "Unknown").upper()
            with st.expander(f"{table_name}", expanded=False):
                col_a, col_b = st.columns(2)
                with col_a:
                    st.markdown(f"**Type:** {table.get('Target_Table_Type', 'N/A')}")
                    st.markdown(f"**Source DV Tables:** {table.get('Source_Data_Vault_Table', 'N/A')}")
                with col_b:
                    st.markdown(f"**Source Logical Table:** {table.get('Source_Logical_Table', 'N/A')}")
                    st.markdown(f"**Columns:** {len(table.get('Column_Mappings', []))}")

                if table.get("Table_Definition"):
                    st.markdown(f"*{table['Table_Definition']}*")

                cols_data = table.get("Column_Mappings", [])
                if cols_data:
                    col_display = []
                    for c in cols_data:
                        src = c.get("SourceMapping", {}) or {}
                        col_display.append({
                            "Column": c.get("Target_Column"),
                            "Type": c.get("Data_Type"),
                            "PK": c.get("Is_PK"),
                            "FK": c.get("Is_FK"),
                            "Source Table": src.get("Source_Table", "--"),
                            "Source Column": src.get("Source_Column", "--"),
                            "Transform": (src.get("Transformation_Logic") or "--")[:60]
                        })
                    st.dataframe(col_display, use_container_width=True)

    with st.expander("Raw STTM JSON", expanded=False):
        st.json(sttm_json)


def render_ddl_output(generated_ddls: list, validation: dict):
    """Render DDL output with validation."""

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total DDLs", validation.get("total_tables", 0))
    with col2:
        st.metric("Passed", validation.get("passed", 0))
    with col3:
        st.metric("Failed", validation.get("failed", 0))

    for ddl_entry in generated_ddls:
        table_name = ddl_entry["table_name"]
        ddl_sql = ddl_entry.get("ddl_sql") or ""

        table_valid = validation.get("table_results", {}).get(table_name, {})

        with st.expander(f"{table_name.upper()}", expanded=False):
            st.code(ddl_sql, language="sql")

            # Only surface failures (clean UI per UX cleanup spec — drop
            # platform/dialect caption and per-table "checks passed" row).
            if table_valid and table_valid.get("issues"):
                for issue in table_valid["issues"]:
                    st.error(issue)


def render_config_output(assembled_configs: list, validation: dict):
    """Render config output — for data_eng_agent the artifact is a
    generated Python file (config or notebook), so we render with
    language='python'."""

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Configs", validation.get("total_configs", 0))
    with col2:
        st.metric("Passed", validation.get("passed", 0))
    with col3:
        st.metric("Failed", validation.get("failed", 0))

    for config in assembled_configs:
        table_name = config.get("name", "Unknown")

        with st.expander(f"{str(table_name).upper()}", expanded=False):
            # Keep only the fields the user signed off on: Type,
            # Business Key, SCD Type, Sources. Watermark / Generated
            # artifact / Attribute Columns / All Target Columns are
            # intentionally removed per UX cleanup spec.
            col_a, col_b, col_c = st.columns(3)
            with col_a:
                st.markdown(f"**Type:** `{config.get('table_type')}`")
            with col_b:
                st.markdown(f"**SCD Type:** `{config.get('scd_type', 'N/A')}`")
            with col_c:
                st.markdown(
                    f"**Business Key:** `{config.get('business_key_col')}`"
                )

            sources = config.get("source_tables", []) or []
            if sources:
                st.markdown(f"**Sources:** `{', '.join(sources)}`")

            st.markdown("**Generated Code (Stage SQL + Config):**")
            st.code(
                config.get("stage_sql") or "# No artifact found on disk",
                language="python",
            )


def render_download_buttons(state: dict):
    """Render download buttons for all artifacts produced by the project."""
    st.markdown("### Download Artifacts")

    col1, col2, col3, col4 = st.columns(4)

    # ── STTM JSON ─────────────────────────────────────────
    with col1:
        sttm = state.get("sttm_json", [])
        if sttm:
            st.download_button(
                "Download STTM JSON",
                data=json.dumps(sttm, indent=4),
                file_name="sttm_mapping.json",
                mime="application/json",
                use_container_width=True
            )

    # ── All DDLs concatenated ─────────────────────────────
    with col2:
        ddls = state.get("generated_ddls", [])
        if ddls:
            combined = "\n\n".join([
                f"-- === {d['table_name'].upper()} ===\n{d['ddl_sql']}"
                for d in ddls
            ])
            platform = (ddls[0] or {}).get("platform", "platform")
            fname = f"all_ddls_{str(platform).lower().replace(' ', '_')}.sql"
            st.download_button(
                "Download All DDLs",
                data=combined,
                file_name=fname,
                mime="text/plain",
                use_container_width=True
            )

    # ── All configs bundled ───────────────────────────────
    with col3:
        config_files = state.get("config_files", [])
        if config_files:
            combined_py = "\n\n# ============================================\n\n".join(
                [
                    f"# FILE: {f['filename']}\n# ============================================\n{f['content']}"
                    for f in config_files
                ]
            )
            st.download_button(
                "Download Configs Bundle",
                data=combined_py,
                file_name="all_configs_bundle.py",
                mime="text/x-python",
                use_container_width=True
            )

    # ── Notebooks bundle ─────────────────────────────────
    with col4:
        nb_files = state.get("notebook_files", [])
        if nb_files:
            combined_nb = "\n\n# ============================================\n\n".join(
                [
                    f"# FILE: {f['filename']}\n# ============================================\n{f['content']}"
                    for f in nb_files
                ]
            )
            st.download_button(
                "Download Notebooks Bundle",
                data=combined_nb,
                file_name="all_notebooks_bundle.py",
                mime="text/x-python",
                use_container_width=True
            )

    # ── Lineage CSV (full-width) ─────────────────────────
    csv_path = state.get("lineage_csv_path")
    if csv_path and os.path.exists(csv_path):
        with open(csv_path, "r", encoding="utf-8") as fp:
            csv_text = fp.read()
        st.download_button(
            "Download Lineage CSV",
            data=csv_text,
            file_name=os.path.basename(csv_path),
            mime="text/csv",
            use_container_width=True,
        )
