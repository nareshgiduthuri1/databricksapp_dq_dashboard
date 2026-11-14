"""
Stage 6 — Assemble Databricks notebooks from the per-table configs.

Wraps `notebook_creation.db_notebook`, which:
  • emits a single `scd2_dim_config.py` notebook from all non-SCD1 DIM
    config files,
  • copies each SCD-1 DIM load notebook as-is,
  • emits a single `fact_config.py` notebook from all FACT config files.

Databricks-only: the produced `.py` files use the Databricks cell-magic
header (`# Databricks notebook source`) and `# COMMAND ----------`
separator, plus `dbutils.widgets.*` for catalog / schema parameters.
"""

from __future__ import annotations

from typing import Any, Dict

from pipeline.base import PipelineStage
from notebook_creation import db_notebook as _db_notebook


class NotebookAssemblyStage(PipelineStage):
    """Builds Databricks-ready `.py` notebooks from generated configs."""

    def __init__(self, config):
        super().__init__(
            config, name="STEP 6 — Databricks Notebook Assembly"
        )

    def _run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        _db_notebook()
        return {"notebook_output_dir": self.config.notebook_output_dir}
