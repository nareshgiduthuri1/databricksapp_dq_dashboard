"""
Pipeline Progress Tracker
===========================
Ported from `LangGraphAgenticPipeline/ui/pipeline_tracker.py`. Adapted
to the data_eng_agent's 3-stage flow (Stage 4 — loader / orchestrator
script generation — does not exist in this project and is omitted).
"""

import streamlit as st


STAGE_DEFINITIONS = {
    "stage_1": {
        "label": "STTM Generation",
        "steps": ["parse_xml", "validate_sttm"],
    },
    "stage_2": {
        "label": "DDL Generation",
        "steps": ["prepare_ddl", "generate_ddl", "validate_ddl"],
    },
    "stage_3": {
        "label": "Config & Stage SQL",
        "steps": [
            "prepare_config",
            "generate_stage_sql",
            "assemble_config",
            "validate_config",
            "save_outputs",
        ],
    },
}


STEP_LABELS = {
    "parse_xml":          "Parse Erwin XML",
    "validate_sttm":      "Validate STTM",
    "prepare_ddl":        "Prepare DDL Input",
    "generate_ddl":       "Generate DDLs (LLM)",
    "validate_ddl":       "Validate DDLs",
    "prepare_config":     "Prepare Config Input",
    "generate_stage_sql": "Generate Stage SQL (LLM)",
    "assemble_config":    "Assemble Configs",
    "validate_config":    "Validate Configs",
    "save_outputs":       "Save Artifacts",
}


def render_pipeline_tracker(
    current_step: str,
    completed_steps: list,
    failed_steps: list | None = None,
):
    """Render a visual pipeline progress tracker with stages."""
    if failed_steps is None:
        failed_steps = []

    st.markdown("### Pipeline Progress")

    cols = st.columns(len(STAGE_DEFINITIONS))

    for i, (stage_key, stage_info) in enumerate(STAGE_DEFINITIONS.items()):
        with cols[i]:
            stage_steps = stage_info["steps"]
            completed_in_stage = [s for s in stage_steps if s in completed_steps]
            failed_in_stage = [s for s in stage_steps if s in failed_steps]

            if failed_in_stage:
                indicator = "[FAILED]"
                status = "Failed"
            elif len(completed_in_stage) == len(stage_steps):
                indicator = "[DONE]"
                status = "Completed"
            elif completed_in_stage:
                indicator = "[IN PROGRESS]"
                status = "In Progress"
            elif current_step in stage_steps:
                indicator = "[RUNNING]"
                status = "Running"
            else:
                indicator = "[PENDING]"
                status = "Pending"

            st.markdown(f"**{indicator} Stage {i+1}**")
            st.caption(f"{stage_info['label']}\n{status}")

            if stage_steps:
                progress = len(completed_in_stage) / len(stage_steps)
                st.progress(progress)


def render_step_timeline(logs: list, step_timings: dict):
    """Render a timeline of step executions with durations."""
    st.markdown("### Execution Timeline")

    for step_key, step_label in STEP_LABELS.items():
        timing = step_timings.get(step_key)
        if timing is not None:
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.markdown(f"**{step_label}**")
            with col2:
                st.markdown(f"`{timing:.2f}s`")
            with col3:
                st.markdown("[DONE]")
        else:
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.markdown(f"*{step_label}*")
            with col2:
                st.markdown("`--`")
            with col3:
                st.markdown("[--]")
