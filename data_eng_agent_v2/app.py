"""
Allianz — Next-Gen Data Intelligence (Streamlit UI)
====================================================

Stage-based, human-in-the-loop UI for the Data Engineering Agent:

    Stage 1 — STTM Generation  (Erwin XML → STTM JSON + slicing)
    Stage 2 — DDL Generation   (multi-platform: Databricks / Snowflake /
                                Microsoft Fabric / Google BigQuery)
    Stage 3 — Stage SQL + Config + Notebook + Lineage CSV
              (Databricks-only for now)

Run:
    streamlit run app.py

UI ported from LangGraphAgenticPipeline; backend wired via
`pipeline.graph.run_stage1 / run_stage2 / run_stage3` which call the
existing — unchanged — generator modules. The CLI entry point
(`python main.py`) is preserved alongside this app.
"""

import streamlit as st
import os
import time
import tempfile

from ui.components import (
    render_header,
    render_sidebar,
    render_stage_header,
    render_approval_gate,
    render_agent_processing,
    render_log_viewer,
)
from ui.output_viewers import (
    render_sttm_output,
    render_ddl_output,
    render_config_output,
    render_download_buttons,
)
from ui.pipeline_tracker import render_pipeline_tracker
from pipeline.graph import run_stage1, run_stage2, run_stage3


# ── "Agent processing" replay (same visual as LangGraph) ──────────
STAGE_AGENTS = {
    "stage1": ["XML Parsing Agent", "STTM Validation Agent"],
    "stage2": [
        "DDL Preparation Agent",
        "DDL Generation Agent",
        "DDL Validation Agent",
    ],
    "stage3": [
        "Config Preparation Agent",
        "Rule Engine Agent",
        "Stage SQL Generation Agent",
        "Config Assembler Agent",
        "Config Validation Agent",
    ],
}


def init_session_state():
    """Initialize all session state variables."""
    defaults = {
        "stage1_state": None,
        "stage2_state": None,
        "stage3_state": None,
        "stage1_completed": False,
        "stage2_completed": False,
        "stage3_completed": False,
        "sttm_approved": False,
        "ddl_approved": False,
        "config_approved": False,
        "completed_steps": [],
        "current_step": None,
        "xml_path": None,
        "stage1_error": None,
        "stage2_error": None,
        "stage3_error": None,
        "run_platform": None,
        "run_dialect": None,
        "run_model": None,
        "stage1_agents_shown": False,
        "stage2_agents_shown": False,
        "stage3_agents_shown": False,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def get_all_logs():
    """Collect logs from all stages for the bottom log viewer."""
    logs = []
    for key in ["stage1_state", "stage2_state", "stage3_state"]:
        state = st.session_state.get(key)
        if state and isinstance(state, dict):
            logs.extend(state.get("pipeline_logs", []))
    return logs


def _reset_for_new_run() -> None:
    for key in [
        "stage1_state", "stage2_state", "stage3_state",
    ]:
        st.session_state[key] = None
    for key in [
        "stage1_completed", "stage2_completed", "stage3_completed",
        "sttm_approved", "ddl_approved", "config_approved",
        "stage1_agents_shown", "stage2_agents_shown", "stage3_agents_shown",
    ]:
        st.session_state[key] = False
    for key in ["stage1_error", "stage2_error", "stage3_error"]:
        st.session_state[key] = None
    st.session_state.completed_steps = []
    st.session_state.current_step = None


def main():
    render_header()
    init_session_state()
    sidebar_config = render_sidebar()

    # ── File Upload handling ─────────────────────────────
    if (
        sidebar_config["uploaded_file"] is not None
        and st.session_state.xml_path is None
    ):
        with tempfile.NamedTemporaryFile(
            delete=False, suffix=".xml", prefix="erwin_"
        ) as tmp_file:
            tmp_file.write(sidebar_config["uploaded_file"].getvalue())
            st.session_state.xml_path = tmp_file.name

    # ── Run Pipeline -> Trigger Stage 1 ──────────────────
    if sidebar_config["run_pipeline"] and st.session_state.xml_path:
        _reset_for_new_run()

        st.session_state.run_platform = sidebar_config["data_platform"]
        st.session_state.run_dialect = sidebar_config["sql_dialect"]
        st.session_state.run_model = sidebar_config["model_choice"]

        try:
            with st.spinner(
                "Running Stage 1: Parsing Erwin XML & Generating STTM..."
            ):
                result = run_stage1(
                    st.session_state.xml_path,
                    data_platform=sidebar_config["data_platform"],
                    sql_dialect=sidebar_config["sql_dialect"],
                    model_name=sidebar_config["model_choice"],
                )

            # Agent processing replay (same visual rhythm as LangGraph)
            render_agent_processing(STAGE_AGENTS["stage1"], delay_per_agent=2.0)

            delay_placeholder = st.empty()
            delay_placeholder.info("Finalizing STTM generation...")
            time.sleep(2)
            delay_placeholder.empty()

            st.session_state.stage1_state = result
            st.session_state.stage1_completed = True
            st.session_state.stage1_agents_shown = True
            st.session_state.completed_steps = ["parse_xml", "validate_sttm"]
        except Exception as e:
            st.session_state.stage1_error = str(e)
            st.error(f"Stage 1 failed: {e}")

        st.rerun()

    # ══════════════════════════════════════════════════════
    # LANDING PAGE
    # ══════════════════════════════════════════════════════
    if (
        not st.session_state.stage1_completed
        and not st.session_state.stage1_error
    ):
        st.markdown("---")

        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("""
            <div class="landing-card">
                <h4>Upload</h4>
                <p>Upload the Erwin XML model file exported from Erwin Data Modeler</p>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown("""
            <div class="landing-card">
                <h4>Generate</h4>
                <p>AI-powered pipeline generates STTM, DDLs, and Config files automatically</p>
            </div>
            """, unsafe_allow_html=True)
        with col3:
            st.markdown("""
            <div class="landing-card">
                <h4>Review & Deploy</h4>
                <p>Review each stage output, approve, and download ready-to-deploy artifacts</p>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")
        st.info(
            "Upload an Erwin XML file, select your target Data Platform, "
            "SQL Dialect and LLM, then click **Run Pipeline** to begin."
        )

        with st.expander("Pipeline Architecture", expanded=False):
            st.code("""
    +------------------------------------------------------------------+
    |                ALLIANZ DATA-ENG ACCELERATOR PIPELINE              |
    +------------------------------------------------------------------+
    |                                                                    |
    |   Platform: [Databricks | Snowflake | Fabric | BigQuery]          |
    |   Dialect:  [SparkSQL | SnowflakeSQL | TSQL | BigQuerySQL]        |
    |                                                                    |
    |   +--- STAGE 1 ----------------------+                            |
    |   |  [Parse XML] -> [Validate STTM]  |                            |
    |   +---------------+------------------+                            |
    |                   |                                                |
    |           [ Review & Approve STTM ]                                |
    |                   |                                                |
    |   +--- STAGE 2 --------------------------------------+            |
    |   |  [Prepare DDL] -> [Generate DDL] -> [Validate]   |            |
    |   +---------------+----------------------------------+            |
    |                   |                                                |
    |           [ Review & Approve DDLs ]                                |
    |                   |                                                |
    |   +--- STAGE 3 ----------------------------------------------+   |
    |   |  [Config Prep] -> [Stage SQL] -> [Assemble Configs]      |   |
    |   |                 -> [Notebooks] -> [Lineage CSV]           |   |
    |   +---------------+------------------------------------------+   |
    |                   |                                                |
    |           [ Review & Approve Configs ]                             |
    |                                                                    |
    +------------------------------------------------------------------+
            """, language="text")
        return

    # ── Active Configuration Banner ──────────────────────
    platform = st.session_state.get("run_platform", "Databricks")
    dialect = st.session_state.get("run_dialect", "SparkSQL")
    model = st.session_state.get("run_model", "openai")

    st.markdown(
        f"**Active Configuration:** **{platform}** | **{dialect}** | "
        f"**LLM: {model}**"
    )

    # ── Pipeline Progress Tracker ─────────────────────────
    st.markdown("---")
    render_pipeline_tracker(
        current_step=st.session_state.get("current_step", ""),
        completed_steps=st.session_state.completed_steps,
    )
    st.markdown("---")

    # ══════════════════════════════════════════════════════
    # STAGE 1: STTM
    # ══════════════════════════════════════════════════════
    if st.session_state.stage1_completed:
        state1 = st.session_state.stage1_state
        render_stage_header(
            1, "STTM Generation",
            "Parse Erwin XML -> Extract Metadata -> Validate Mappings",
        )
        render_sttm_output(
            state1.get("sttm_json", []),
            state1.get("sttm_validation", {}),
        )
        sttm_decision = render_approval_gate(
            stage_name="stage1",
            artifact_name="STTM",
            approve_key="sttm",
            details=(
                "Review the Source-to-Target Mapping above. "
                "Approve to proceed to DDL generation."
            ),
        )
        if sttm_decision == "regenerate":
            st.session_state.stage1_completed = False
            st.session_state.stage1_state = None
            st.session_state.completed_steps = []
            st.rerun()

    elif st.session_state.stage1_error:
        render_stage_header(
            1, "STTM Generation",
            "Parse Erwin XML -> Extract Metadata -> Validate Mappings",
        )
        st.error(f"Stage 1 failed: {st.session_state.stage1_error}")

    # ══════════════════════════════════════════════════════
    # STAGE 2: DDLs
    # ══════════════════════════════════════════════════════
    if st.session_state.get("sttm_approved", False):
        if (
            not st.session_state.stage2_completed
            and not st.session_state.stage2_error
        ):
            try:
                with st.spinner(
                    f"Running Stage 2: Generating DDLs for {platform}..."
                ):
                    result = run_stage2(dict(st.session_state.stage1_state))

                render_agent_processing(
                    STAGE_AGENTS["stage2"], delay_per_agent=2.0
                )

                st.session_state.stage2_state = result
                st.session_state.stage2_completed = True
                st.session_state.stage2_agents_shown = True
                st.session_state.completed_steps.extend(
                    ["prepare_ddl", "generate_ddl", "validate_ddl"]
                )
            except Exception as e:
                st.session_state.stage2_error = str(e)
            st.rerun()

        if st.session_state.stage2_completed:
            state2 = st.session_state.stage2_state
            st.markdown("---")
            render_stage_header(
                2, f"DDL Generation ({platform})",
                f"Transform STTM -> LLM generates {platform}-compatible DDLs -> Validate SQL",
            )
            render_ddl_output(
                state2.get("generated_ddls", []),
                state2.get("ddl_validation", {}),
            )
            ddl_decision = render_approval_gate(
                stage_name="stage2",
                artifact_name="DDLs",
                approve_key="ddl",
                details=(
                    f"Review the generated {platform} DDL statements above. "
                    "Approve to proceed to Config & Stage SQL generation."
                ),
            )
            if ddl_decision == "regenerate":
                st.session_state.stage2_completed = False
                st.session_state.stage2_state = None
                st.session_state.ddl_approved = False
                st.session_state.completed_steps = [
                    s for s in st.session_state.completed_steps
                    if s not in ["prepare_ddl", "generate_ddl", "validate_ddl"]
                ]
                st.rerun()

        elif st.session_state.stage2_error:
            st.markdown("---")
            render_stage_header(2, "DDL Generation", "")
            st.error(f"Stage 2 failed: {st.session_state.stage2_error}")

    # ══════════════════════════════════════════════════════
    # STAGE 3: Stage SQL + Config + Notebook + Lineage CSV
    # ══════════════════════════════════════════════════════
    if st.session_state.get("ddl_approved", False):
        if (
            not st.session_state.stage3_completed
            and not st.session_state.stage3_error
        ):
            try:
                with st.spinner(
                    f"Running Stage 3: Generating Stage SQL & Configs "
                    f"({dialect})..."
                ):
                    result = run_stage3(dict(st.session_state.stage2_state))

                render_agent_processing(
                    STAGE_AGENTS["stage3"], delay_per_agent=2.0
                )

                st.session_state.stage3_state = result
                st.session_state.stage3_completed = True
                st.session_state.stage3_agents_shown = True
                st.session_state.completed_steps.extend(
                    [
                        "prepare_config",
                        "generate_stage_sql",
                        "assemble_config",
                        "validate_config",
                        "save_outputs",
                    ]
                )
            except Exception as e:
                st.session_state.stage3_error = str(e)
            st.rerun()

        if st.session_state.stage3_completed:
            state3 = st.session_state.stage3_state
            st.markdown("---")
            render_stage_header(
                3, f"Config & Stage SQL Generation ({dialect})",
                f"Derive Configs -> LLM generates Stage SQL -> Assemble -> Validate -> Save",
            )

            render_config_output(
                state3.get("assembled_configs", []),
                state3.get("config_validation", {}),
            )

            config_decision = render_approval_gate(
                stage_name="stage3",
                artifact_name="Configs",
                approve_key="config",
                details=(
                    "Review the generated configs, notebooks and stage SQL "
                    "above. Approve to mark the run as complete and reveal "
                    "downloads."
                ),
            )
            if config_decision == "regenerate":
                st.session_state.stage3_completed = False
                st.session_state.stage3_state = None
                st.session_state.config_approved = False
                st.session_state.completed_steps = [
                    s for s in st.session_state.completed_steps
                    if s not in [
                        "prepare_config", "generate_stage_sql",
                        "assemble_config", "validate_config", "save_outputs",
                    ]
                ]
                st.rerun()

        elif st.session_state.stage3_error:
            st.markdown("---")
            render_stage_header(3, "Config & Stage SQL Generation", "")
            st.error(f"Stage 3 failed: {st.session_state.stage3_error}")

    # ══════════════════════════════════════════════════════
    # COMPLETION + DOWNLOADS
    # ══════════════════════════════════════════════════════
    if st.session_state.get("config_approved", False):
        st.markdown("---")
        st.success(
            f"Pipeline completed successfully. "
            f"All artifacts generated for {platform} using {dialect} "
            f"(LLM: {model})."
        )

        # Merge all relevant artifact references for download
        state1 = st.session_state.stage1_state or {}
        state2 = st.session_state.stage2_state or {}
        state3 = st.session_state.stage3_state or {}
        render_download_buttons(
            {
                "sttm_json": state1.get("sttm_json", []),
                "generated_ddls": state2.get("generated_ddls", []),
                "config_files": state3.get("config_files", []),
                "notebook_files": state3.get("notebook_files", []),
                "lineage_csv_path": state3.get("lineage_csv_path"),
            }
        )

    # ── Pipeline Logs (bottom) ────────────────────────────
    all_logs = get_all_logs()
    if all_logs:
        st.markdown("---")
        render_log_viewer(all_logs)


if __name__ == "__main__":
    main()
