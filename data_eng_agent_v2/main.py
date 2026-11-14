"""
STTM-to-Code — main entry point
===============================

Thin orchestration layer. All real work lives in the `pipeline` package
(class-based wrappers) and the generator modules (`xmltojson.py`,
`dim_scd2_generator.py`, `dim_scd1_generator.py`, `fact_generator.py`,
`ddl_generator.py`, `notebook_creation.py`, `json_to_csv.py`), with the
platform-aware LLM prompts in `modules/prompts/`.

Usage
-----
    python main.py
    python main.py <input_json> <output_config_dir>     # legacy positional
"""

from __future__ import annotations

import sys

from pipeline import Pipeline, PipelineConfig


def main() -> int:
    # Legacy positional arg: optional override for config output directory.
    config_output_dir = sys.argv[2] if len(sys.argv) > 2 else None

    # token_usage.reset()  # start a fresh usage ledger for this run

    cfg = PipelineConfig.from_config(config_output_dir=config_output_dir)
    results = Pipeline(cfg).run()

    return 0 if all(r.success for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())
