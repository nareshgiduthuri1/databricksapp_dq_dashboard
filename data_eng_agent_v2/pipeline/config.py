"""
PipelineConfig
--------------
Centralised, immutable configuration object for the STTM-to-Code pipeline.

Default values are read from `config.yaml` (loaded via `config_loader`)
so the same code can run locally, in CI, or as a Databricks job without
code changes — only the `config.yaml` / `APP_CONFIG_FILE` differs.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import config_loader


@dataclass(frozen=True)
class PipelineConfig:
    """
    Holds every path / flag the pipeline needs.

    Attributes
    ----------
    input_xml_file : str
        Absolute or relative path to the Erwin XML export.
    output_json_file : str
        Path where the normalised JSON (parsed STTM) will be written.
    scd1_json_file : str
        Intermediate JSON containing only SCD-1 dimension rows.
    scd2_json_file : str
        Intermediate JSON containing only SCD-2 dimension rows.
    fact_json_file : str
        Intermediate JSON containing only fact-table rows.
    config_output_dir : str
        Directory where generated `*_config.py` files are placed.
    notebook_output_dir : str
        Directory where the final Databricks `.py` notebooks land.
    csv_output_file : str
        Path of the flat-CSV mapping export (Data-Engineer-friendly view).
    project_root : Path
        Resolved project root — used to anchor relative paths.
    """

    input_xml_file: str
    output_json_file: str
    scd1_json_file: str = field(
        default_factory=lambda: config_loader.get(
            "io.scd1_json_file", "./input/scd1_tables.json"
        )
    )
    scd2_json_file: str = field(
        default_factory=lambda: config_loader.get(
            "io.scd2_json_file", "./input/scd2_tables.json"
        )
    )
    fact_json_file: str = field(
        default_factory=lambda: config_loader.get(
            "io.fact_json_file", "./input/fact_tables.json"
        )
    )
    # ── Raw Data Vault (Bronze -> Data Vault) slices ──────────────────
    # Intermediate JSON slices written by SttmFilterStage when the target
    # model is Raw Data Vault. Ignored by the Dimensional / Business Vault
    # flows.
    hub_json_file: str = field(
        default_factory=lambda: config_loader.get(
            "io.hub_json_file", "./output/sttm/hub_tables.json"
        )
    )
    sat_json_file: str = field(
        default_factory=lambda: config_loader.get(
            "io.sat_json_file", "./output/sttm/sat_tables.json"
        )
    )
    link_json_file: str = field(
        default_factory=lambda: config_loader.get(
            "io.link_json_file", "./output/sttm/link_tables.json"
        )
    )
    config_output_dir: str = field(
        default_factory=lambda: config_loader.get(
            "directories.config_output_dir", "output/configs/"
        )
    )
    notebook_output_dir: str = field(
        default_factory=lambda: config_loader.get(
            "directories.notebook_output_dir", "db_notebooks"
        )
    )
    csv_output_file: str = field(
        default_factory=lambda: config_loader.get(
            "io.csv_output_file",
            "./output/lineage/erwin_customer360_final_mapping_file.csv",
        )
    )

    # ── DDL generation (additive — does NOT affect existing stages) ──
    # `data_platform` and `sql_dialect` are designed to be supplied from
    # the Streamlit UI dropdown. Defaults come from `config.yaml`.
    data_platform: str = field(
        default_factory=lambda: config_loader.get(
            "generation.data_platform", "Databricks"
        )
    )
    sql_dialect: Optional[str] = field(  # None → platform default
        default_factory=lambda: config_loader.get("generation.sql_dialect")
    )
    ddl_output_dir: str = field(
        default_factory=lambda: config_loader.get(
            "directories.ddl_output_dir", "output/ddl/"
        )
    )
    enable_ddl_generation: bool = field(
        default_factory=lambda: bool(
            config_loader.get("generation.enable_ddl_generation", True)
        )
    )

    # ── LLM backend selection (used by all generators) ───────────────
    # Threaded through DDL + SCD-1/SCD-2/FACT generators. The
    # underlying `convert_with_llm(...)` is unchanged.
    model_name: str = field(
        default_factory=lambda: config_loader.get("llm.default_model", "openai")
    )

    project_root: Path = field(default_factory=lambda: Path.cwd())

    # ------------------------------------------------------------------
    # Factories
    # ------------------------------------------------------------------
    @classmethod
    def from_config(
        cls,
        config_output_dir: Optional[str] = None,
        data_platform: Optional[str] = None,
        sql_dialect: Optional[str] = None,
        ddl_output_dir: Optional[str] = None,
        enable_ddl_generation: Optional[bool] = None,
        model_name: Optional[str] = None,
    ) -> "PipelineConfig":
        """
        Build a config object by reading `io.input_xml_file` and
        `io.output_json_file` from `config.yaml` (via `config_loader`).

        DDL-related kwargs are optional. When omitted, they fall back to
        the corresponding `config.yaml` values (`generation.*`,
        `directories.*`, `llm.default_model`) and finally to the
        dataclass defaults. The Streamlit UI passes these in explicitly
        to override the file-level defaults at runtime.
        """
        input_xml = config_loader.get("io.input_xml_file")
        output_json = config_loader.get("io.output_json_file")

        if not input_xml or not output_json:
            raise ValueError(
                "io.input_xml_file and io.output_json_file must be set "
                "(check your config.yaml)."
            )

        kwargs: dict = {
            "input_xml_file": input_xml,
            "output_json_file": output_json,
        }
        if config_output_dir:
            kwargs["config_output_dir"] = config_output_dir

        # ── DDL knobs (UI-friendly: explicit > config.yaml > default) ──
        platform = data_platform or config_loader.get("generation.data_platform")
        if platform:
            kwargs["data_platform"] = platform

        dialect = sql_dialect or config_loader.get("generation.sql_dialect")
        if dialect:
            kwargs["sql_dialect"] = dialect

        ddl_dir = ddl_output_dir or config_loader.get(
            "directories.ddl_output_dir"
        )
        if ddl_dir:
            kwargs["ddl_output_dir"] = ddl_dir

        if enable_ddl_generation is not None:
            kwargs["enable_ddl_generation"] = enable_ddl_generation
        else:
            cfg_flag = config_loader.get("generation.enable_ddl_generation")
            if cfg_flag is not None:
                kwargs["enable_ddl_generation"] = (
                    str(cfg_flag).strip().lower() in ("1", "true", "yes", "y")
                    if isinstance(cfg_flag, str)
                    else bool(cfg_flag)
                )

        model = model_name or config_loader.get("llm.default_model")
        if model:
            kwargs["model_name"] = model

        return cls(**kwargs)

    # Backward-compatible alias — older callers used `from_env`.
    from_env = from_config

    # ------------------------------------------------------------------
    # Convenience
    # ------------------------------------------------------------------
    def describe(self) -> str:
        """Return a human-friendly, multi-line summary of all paths."""
        lines = [
            "PipelineConfig",
            "─" * 55,
            f"  Input  XML        : {self.input_xml_file}",
            f"  Output JSON       : {self.output_json_file}",
            f"  SCD1 JSON         : {self.scd1_json_file}",
            f"  SCD2 JSON         : {self.scd2_json_file}",
            f"  FACT JSON         : {self.fact_json_file}",
            f"  Configs dir       : {self.config_output_dir}",
            f"  Notebooks dir     : {self.notebook_output_dir}",
            f"  CSV output        : {self.csv_output_file}",
            f"  DDL output dir    : {self.ddl_output_dir}",
            f"  Data platform     : {self.data_platform}",
            f"  SQL dialect       : {self.sql_dialect or '(platform default)'}",
            f"  LLM model         : {self.model_name}",
            f"  DDL enabled       : {self.enable_ddl_generation}",
        ]
        return "\n".join(lines)
