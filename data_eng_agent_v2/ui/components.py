"""
Reusable Streamlit UI Components
=================================
Ported verbatim from `LangGraphAgenticPipeline/ui/components.py`, with
two narrow adaptations:

  • `DATA_PLATFORMS` / `SQL_DIALECTS` / `PLATFORM_DIALECT_DEFAULTS` are
    imported from `modules.ddl_constants` instead of `config.constants`
    (this project's home for those registries).
  • The LLM dropdown matches the model names supported by this
    project's `modules.openai_call.convert_with_llm` — "openai",
    "claude", "gpt-5-chat", "gpt-5".

All branding, CSS, colour scheme, and layout are preserved exactly.
"""

import streamlit as st
import json
import time
import base64
import os


def render_header():
    """Render the Allianz / Next-Gen Data Intelligence branded header."""
    try:
        st.set_page_config(
            page_title="Allianz — Next-Gen Data Intelligence",
            page_icon="",
            layout="wide",
            initial_sidebar_state="expanded"
        )
    except st.errors.StreamlitAPIException:
        pass

    st.markdown("""
    <style>
        .block-container { padding-top: 0.2rem; }

        .exl-header {
            background: #003781;
            border: 1px solid #3a3a3a;
            border-radius: 16px;
            padding: 2.5rem 2rem 2rem 2rem;
            margin-bottom: 2rem;
            text-align: center;
            position: relative;
            overflow: hidden;
        }
        .exl-header::before {
            content: '';
            position: absolute;
            top: 0; left: 0; right: 0;
            height: 3px;
            background: linear-gradient(90deg, #003781, #4a90d9, #003781);
        }
        .exl-badge {
            display: inline-block;
            padding: 0.4rem 1.5rem;
            border: 1.5px solid #003781;
            border-radius: 25px;
            color: #ffffff;
            font-size: 0.85rem;
            font-weight: 500;
            letter-spacing: 1px;
            margin-bottom: 1.2rem;
            background: rgba(232, 99, 43, 0.08);
        }
        .exl-title {
            font-size: 2.8rem;
            font-weight: 700;
            margin: 0; padding: 0;
            line-height: 1.2;
        }
        .exl-title .white { color: #ffffff; }
        .exl-title .orange { color: #ffffff; }
        .exl-subtitle {
            color: #888888;
            font-size: 1rem;
            margin-top: 0.8rem;
            letter-spacing: 0.5px;
        }

        .step-card {
            background: #f8f9fa;
            border-left: 4px solid #0f3460;
            padding: 1rem;
            margin: 0.5rem 0;
            border-radius: 0 8px 8px 0;
        }
        .step-card.success { border-left-color: #28a745; }
        .step-card.running { border-left-color: #ffc107; }
        .step-card.error   { border-left-color: #dc3545; }

        .log-entry {
            font-family: 'Courier New', monospace;
            font-size: 0.8rem;
            padding: 0.2rem 0;
        }
        .log-info    { color: #2196F3; }
        .log-warning { color: #FF9800; }
        .log-error   { color: #f44336; }

        .approval-gate {
            background: #003781;
            border: 1px solid #003781;
            border-radius: 12px;
            padding: 1.5rem 2rem;
            margin: 1.5rem 0;
            text-align: center;
        }
        .approval-gate h4 { color: #ffffff; margin: 0 0 0.3rem 0; }
        .approval-gate p { color: #a8a8a8; margin: 0 0 1rem 0; font-size: 0.9rem; }

        .stage-header {
            background: #f8f9fa;
            border-left: 5px solid #003781;
            padding: 1rem 1.5rem;
            border-radius: 0 10px 10px 0;
            margin: 1.5rem 0 1rem 0;
        }
        .stage-header h3 { margin: 0; color: #1a1a2e; }
        .stage-header p { margin: 0.2rem 0 0 0; color: #666; font-size: 0.85rem; }

        .landing-card {
            background: #003781;
            border: 1px solid #003781;
            border-radius: 12px;
            padding: 2rem 2rem 2.5rem 2rem;
            text-align: center;
            height: 100%;
            display: flex;
            flex-direction: column;
            justify-content: center;
            min-height: 140px;
        }
        .landing-card h4 { color: #ffffff; margin-bottom: 0.5rem; font-size: 1.3rem; }
        .landing-card p { color: #a8a8a8; font-size: 0.9rem; margin: 0; }

        .agent-status {
            background: #f0f2f6;
            border-left: 3px solid #003781;
            padding: 0.6rem 1rem;
            margin: 0.3rem 0;
            border-radius: 0 6px 6px 0;
            font-size: 0.9rem;
            color: #1a1a2e;
        }

        .structure-preview {
            background: #f8f9fa;
            border: 1px solid #ddd;
            border-radius: 8px;
            padding: 0.5rem;
            margin-top: 0.5rem;
            max-height: 200px;
            overflow-y: auto;
            font-size: 0.75rem;
        }

        .stButton > button[kind="primary"] {
            background-color: #003781 !important;
            border-color: #003781 !important;
            color: #ffffff !important;
        }
        .stButton > button[kind="primary"]:hover {
            background-color: #00529b !important;
            border-color: #00529b !important;
        }

        [data-testid="stCheckbox"] svg {
            color: #003781 !important;
        }
        [data-testid="stCheckbox"] [role="checkbox"][aria-checked="true"] {
            background-color: #003781 !important;
            border-color: #003781 !important;
        }
        .st-emotion-cache-1w9h4tq {
            background-color: #003781 !important;
            border-color: #003781 !important;
        }
        label[data-baseweb="checkbox"] > span:first-child {
            background-color: #003781 !important;
            border-color: #003781 !important;
        }
    </style>
    """, unsafe_allow_html=True)

    logo_path = os.path.join("assets", "allianz_logo.png")
    if os.path.exists(logo_path):
        with open(logo_path, "rb") as f:
            logo_data = base64.b64encode(f.read()).decode()
        st.markdown(
            f'<div style="margin-bottom: 0.3rem; padding: 0.3rem 0;">'
            f'<img src="data:image/png;base64,{logo_data}" style="height: 100px; background: white; padding: 10px 20px; border-radius: 8px; object-fit: contain;">'
            f'</div>',
            unsafe_allow_html=True
        )

    st.markdown("""
    <div class="exl-header">
        <div class="exl-badge">Next-Gen Data Intelligence</div>
        <h1 class="exl-title">
            <span class="white">Welcome to </span><span class="orange">Allianz</span>
        </h1>
        <p class="exl-subtitle">Automated Data Warehouse Pipeline — Erwin XML to STTM to DDLs to Configs</p>
    </div>
    """, unsafe_allow_html=True)


def render_sidebar():
    """Render sidebar with configuration options."""
    # Late import — keeps the import graph clean and avoids surfacing
    # backend deps if a user runs `streamlit run app.py` for the first time.
    from modules.ddl_constants import (
        DATA_PLATFORMS,
        SQL_DIALECTS,
        PLATFORM_DIALECT_DEFAULTS,
    )

    with st.sidebar:
        st.markdown("## Configuration")
        st.divider()

        # ── File Upload ───────────────────────────────────
        uploaded_file = st.file_uploader(
            "Upload Erwin XML",
            type=["xml"],
            help="Upload the Repository Version XML exported from Erwin Data Modeler"
        )

        st.divider()

        # ── STTM Structure Upload (UI-only) ───────────────
        st.markdown("### STTM Output Structure")
        sttm_structure_file = st.file_uploader(
            "Upload STTM structure template",
            type=["json"],
            help="Upload a JSON file defining the desired STTM output structure",
            key="sttm_structure_upload"
        )

        if sttm_structure_file is not None:
            try:
                sttm_structure_content = json.loads(sttm_structure_file.getvalue().decode("utf-8"))
                with st.expander("Preview: STTM Structure", expanded=False):
                    st.json(sttm_structure_content)
                st.caption("Structure template loaded successfully")
            except json.JSONDecodeError:
                st.error("Invalid JSON file. Please upload a valid JSON structure.")

        st.divider()

        # ── Config Structure Upload (UI-only) ─────────────
        st.markdown("### Config Output Structure")
        config_structure_file = st.file_uploader(
            "Upload Config structure template",
            type=["json"],
            help="Upload a JSON file defining the desired Config output structure",
            key="config_structure_upload"
        )

        if config_structure_file is not None:
            try:
                config_structure_content = json.loads(config_structure_file.getvalue().decode("utf-8"))
                with st.expander("Preview: Config Structure", expanded=False):
                    st.json(config_structure_content)
                st.caption("Structure template loaded successfully")
            except json.JSONDecodeError:
                st.error("Invalid JSON file. Please upload a valid JSON structure.")

        st.divider()

        # ── Data Platform ─────────────────────────────────
        st.markdown("### Data Platform")

        platform_options = list(DATA_PLATFORMS.keys())
        platform_choice = st.selectbox(
            "Target Platform",
            platform_options,
            index=0,
            help="Select the target data platform for DDL generation",
            key="platform_select"
        )

        platform_config = DATA_PLATFORMS[platform_choice]
        st.caption(f"{platform_config['notes']}")

        st.divider()

        # ── SQL Dialect ───────────────────────────────────
        st.markdown("### SQL Dialect")

        dialect_options = list(SQL_DIALECTS.keys())
        recommended = PLATFORM_DIALECT_DEFAULTS.get(platform_choice, "SparkSQL")
        default_idx = dialect_options.index(recommended) if recommended in dialect_options else 0

        dialect_choice = st.selectbox(
            "SQL Dialect",
            dialect_options,
            index=default_idx,
            help="Select the SQL dialect for Stage SQL generation",
            key="dialect_select"
        )

        dialect_config = SQL_DIALECTS[dialect_choice]
        st.caption(f"{dialect_config['notes']}")

        if dialect_choice != recommended:
            st.info(f"Recommended dialect for {platform_choice}: {recommended}")

        st.divider()

        # ── LLM Settings ─────────────────────────────────
        st.markdown("### LLM Settings")
        # Models supported by modules/openai_call.py in this project
        model_choice = st.selectbox(
            "Model",
            ["openai", "claude", "gpt-5-chat", "gpt-5", "gemini", "openai-direct"],
            index=0,
            help="Select the LLM used by all generation stages (DDL, Stage SQL, Configs). "
                 "Fill the matching providers.* section in config.yaml."
        )

        st.divider()

        # ── Pipeline Options ──────────────────────────────
        st.markdown("### Pipeline Options")
        save_intermediates = st.checkbox(
            "Save intermediate outputs",
            value=True,
            help="Save all intermediate JSON/SQL files to disk"
        )

        st.divider()

        # ── Current Selection Summary ─────────────────────
        st.markdown("### Current Selection")
        st.markdown(f"""
        | Setting | Value |
        |---------|-------|
        | **Platform** | {platform_choice} |
        | **Dialect** | {dialect_choice} |
        | **LLM** | {model_choice} |
        | **String Type** | `{platform_config['string_type']}` |
        | **Timestamp** | `{platform_config['timestamp_type']}` |
        | **PK Support** | {'Yes' if platform_config['supports_alter_pk'] else 'No'} |
        | **FK Support** | {'Yes' if platform_config['supports_alter_fk'] else 'No'} |
        """)

        st.divider()

        # Run button
        run_pipeline = st.button(
            "Run Pipeline",
            type="primary",
            use_container_width=True,
            disabled=uploaded_file is None
        )

        return {
            "uploaded_file": uploaded_file,
            "data_platform": platform_choice,
            "sql_dialect": dialect_choice,
            "model_choice": model_choice,
            "save_intermediates": save_intermediates,
            "run_pipeline": run_pipeline
        }


def render_stage_header(stage_num: int, title: str, description: str):
    """Render a styled stage header."""
    st.markdown(f"""
    <div class="stage-header">
        <h3>Stage {stage_num}: {title}</h3>
        <p>{description}</p>
    </div>
    """, unsafe_allow_html=True)


def render_approval_gate(
    stage_name: str,
    artifact_name: str,
    approve_key: str,
    details: str = ""
):
    """Render an inline approval gate."""
    if st.session_state.get(f"{approve_key}_approved", False):
        st.success(f"{artifact_name} approved — proceeding to next stage")
        return "approved"

    st.markdown(f"""
    <div class="approval-gate">
        <h4>Review & Approve: {artifact_name}</h4>
        <p>{details if details else f'Please review the generated {artifact_name} above before proceeding.'}</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1, 2])

    with col1:
        approve = st.button(
            f"Approve {artifact_name}",
            key=f"approve_{approve_key}",
            type="primary",
            use_container_width=True
        )
    with col2:
        regenerate = st.button(
            "Regenerate",
            key=f"regen_{approve_key}",
            use_container_width=True
        )

    if approve:
        st.session_state[f"{approve_key}_approved"] = True
        st.rerun()
    elif regenerate:
        return "regenerate"

    return "pending"


def render_agent_processing(agents: list, delay_per_agent: float = 5.0):
    """
    Display agent processing messages sequentially with timed delays.
    Each agent message shows for `delay_per_agent` seconds.
    """
    status_placeholder = st.empty()

    for agent_name in agents:
        status_placeholder.markdown(
            f'<div class="agent-status">Processing: <strong>{agent_name}</strong></div>',
            unsafe_allow_html=True
        )
        time.sleep(delay_per_agent)

    status_placeholder.empty()


def render_metrics_row(metrics: dict):
    """Render a row of metric cards."""
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric("Tables", metrics.get("tables_processed", 0))
    with col2:
        st.metric("Columns", metrics.get("columns_mapped", 0))
    with col3:
        st.metric("DDLs", metrics.get("ddls_generated", 0))
    with col4:
        st.metric("Configs", metrics.get("configs_generated", 0))
    with col5:
        st.metric("LLM Calls", metrics.get("llm_calls", 0))


def render_log_viewer(logs: list):
    """Render pipeline execution logs."""
    with st.expander("Pipeline Execution Log", expanded=False):
        if not logs:
            st.info("No logs yet.")
            return
        for log in logs:
            level = log.get("level", "INFO")
            color_class = {
                "INFO": "log-info",
                "WARNING": "log-warning",
                "ERROR": "log-error"
            }.get(level, "log-info")

            st.markdown(
                f'<div class="log-entry {color_class}">'
                f'[{log["timestamp"]}] [{log["level"]}] {log["step"]}: {log["message"]}'
                f'</div>',
                unsafe_allow_html=True
            )
