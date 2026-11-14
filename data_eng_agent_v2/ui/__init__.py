"""
Streamlit UI package for the data_eng_agent.

Ported from `LangGraphAgenticPipeline/ui/`. Backend wiring goes through
`pipeline.graph` (run_stage1 / run_stage2 / run_stage3), so this UI is
a thin presentation layer on top of the existing — unchanged — STTM,
DDL, and SCD/Config/Notebook generators.
"""
