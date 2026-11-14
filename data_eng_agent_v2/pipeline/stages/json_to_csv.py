"""
Stage 7 — Flatten the canonical STTM JSON into a single CSV.

Wraps `json_to_csv.convert_json_to_csv`. Useful for Data Engineers /
business reviewers who prefer a spreadsheet view of the mapping.
"""

from __future__ import annotations

import os
from typing import Any, Dict

from pipeline.base import PipelineStage
from modules.json_to_csv import convert_json_to_csv


class JsonToCsvStage(PipelineStage):
    """Produces a row-per-column CSV view of the parsed STTM."""

    def __init__(self, config):
        super().__init__(config, name="STEP 7 — JSON → CSV (flat mapping)")

    def _run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        cfg = self.config
        summary = convert_json_to_csv(
            cfg.output_json_file, cfg.csv_output_file
        )

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

        return {"csv_summary": summary}
