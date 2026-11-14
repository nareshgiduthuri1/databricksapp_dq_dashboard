# Data Engineering Agent

## Purpose

An LLM-powered accelerator that turns an **Erwin data-model export (XML)** into ready-to-use
data-engineering artifacts — **DDLs, staging SQL, per-table config scripts**. 
It removes the manual, error-prone effort of hand-writing these from a
source-to-target mapping, giving Data Engineers a consistent, repeatable starting point across
data products and target models.

## How it works

The pipeline is **config-driven** — a single `config.yaml` controls the input model, the
conversion (target model), the data platform, the LLM backend, and all I/O paths. A run flows:

1. **Parse** the Erwin XML into a normalized STTM JSON (source→target mapping).
2. **Filter/route** tables by the configured target model.
3. **Generate** DDL, staging SQL, config scripts and notebooks — table structure is derived
   deterministically from the mapping; SQL/transformations are produced by platform-aware LLM
   prompts using the mapping's Transformation Rules as the source of truth.

Switching data product, target model, platform, or LLM is a config change — no code edits.

## Project structure

```
data_eng_agent/
├── main.py                 CLI entry point — runs the full pipeline end-to-end
├── app.py                  Streamlit UI — stage-based, human-in-the-loop run
├── config.yaml             Single source of truth (paths, target model, platform, LLM, creds) — not committed
├── config.example.yaml     Template for config.yaml (no secrets)
├── config_loader.py        Loads/caches config.yaml; dotted-key access (e.g. io.input_xml_file)
├── requirements.txt        Python dependencies
├── notebook_creation.py    Assembles per-table configs into runnable Databricks notebooks
│
├── pipeline/               Orchestration layer
│   ├── config.py           PipelineConfig — resolves every path/flag from config.yaml
│   ├── base.py             PipelineStage base class + StageResult envelope
│   ├── orchestrator.py     Sequences the stages for CLI; picks the stage set by target model
│   ├── graph.py            Approval-gated stage entry points for the UI (run_stage1/2/3)
│   └── stages/             Thin wrapper per step:
│       ├── xml_to_json.py      Erwin XML → STTM JSON
│       ├── sttm_filter.py      Split STTM by target model (SCD1/SCD2/FACT, or hub/sat/link)
│       ├── ddl_generation.py   DDL per table
│       ├── dim_scd2.py         SCD2 (dimension / BV master) config + stage SQL
│       ├── dim_scd1.py         SCD1 (dimension / BV xref) notebook + stage SQL
│       ├── fact.py             Fact config + stage SQL
│       ├── raw_vault.py        Hub/Sat/Link config generation (Bronze → Raw Vault)
│       ├── notebook.py         Notebook assembly
│       └── json_to_csv.py      Flat lineage CSV
│
├── modules/                Core logic + LLM
│   ├── xmltojson.py            Parses Erwin XML into STTM JSON (unified UDP extraction incl. Filter Rule)
│   ├── generation_profiles.py  Target-model registry (Dimensional / Business Vault / Raw Data Vault): model detection, audit-column rules
│   ├── dim_scd2_generator.py   Builds SCD2 (dimension / BV master) config + stage SQL
│   ├── dim_scd1_generator.py   Builds SCD1 (dimension / BV xref) notebook + stage SQL
│   ├── fact_generator.py       Builds fact config + stage SQL
│   ├── raw_vault_generator.py  Builds hub/sat/link build-SQL config (one bundled file per type)
│   ├── ddl_generator.py        Multi-platform DDL generation
│   ├── ddl_constants.py        Platform/dialect catalog for DDL
│   ├── ddl_prompts.py          DDL prompt assembly helper
│   ├── json_to_csv.py          STTM → CSV lineage export
│   ├── openai_call.py          LLM backend router (Azure OpenAI / Vertex Claude)
│   ├── token_usage.py          Token-usage & cost meter + run report
│   └── prompts/                Platform-aware LLM prompt builders
│       ├── _profiles.py            Per-platform SQL rules + dialect translation
│       ├── dim_scd2_prompt.py      SCD2 staging-SQL prompt (used for dimension & BV master)
│       ├── dim_scd1_prompt.py      SCD1 staging-SQL prompt (used for dimension & BV xref)
│       ├── fact_prompt.py          Fact staging-SQL prompt
│       ├── hub_prompt.py           Raw Vault HUB build-SQL prompt
│       ├── sat_prompt.py           Raw Vault SATELLITE build-SQL prompt
│       ├── link_prompt.py          Raw Vault LINK build-SQL prompt
│       ├── ddl_prompt.py           DDL prompt builder
│       
│
├── ui/                     Streamlit UI pieces
│   ├── components.py           Reusable UI components (header, sidebar, approval gates)
│   ├── pipeline_tracker.py     Stage progress tracker
│   └── output_viewers.py       Renderers for STTM / DDL / config outputs + downloads
│
├── input/                  Erwin XML input file(s)
└── output/                 Generated artifacts — sttm/ (JSON), ddl/, configs/, lineage/
```

## Setup & installation

**Prerequisites**
- Python 3.10+
- VS Code IDE/ Pycharm IDE
- Access to at least one LLM backend: Azure OpenAI (GPT-4o / GPT-5) and/or Google Vertex (Claude)

**Install**
```bash
python -m venv venv && source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

**Configure** (config-driven — everything is set here; no code changes needed)
```bash
cp config.example.yaml config.yaml
```
Then edit `config.yaml`:
- `io.input_xml_file` / output paths — the Erwin XML to process and where artifacts are written.
- `generation.type_of_conversion` — the conversion / target model (see below).
- `generation.data_platform` + `sql_dialect` — the target data platform for DDL.
- `llm.default_model` — the LLM backend, plus that provider's credentials under `providers.*`.

`config.yaml` holds credentials and is git-ignored — never commit it. Use `config.example.yaml`
as the template. Point elsewhere with the `APP_CONFIG_FILE` env var if needed.

## Running the pipeline

**CLI / backend** (runs all stages end-to-end):
```bash
python main.py
```

**UI / Streamlit** (stage-based with approval gates between steps):
```bash
streamlit run app.py
```

Or use the included launchers. They create an isolated `.venv`, install/update all packages
from `requirements.txt`, start Streamlit in the background, and record its PID for shutdown:

```bat
run.bat
stop.bat
```

```bash
chmod +x run.sh stop.sh
./run.sh
./stop.sh
```

The UI is available at `http://localhost:8501`. Runtime output is written to
`streamlit.log` (and `streamlit.log.err` on Windows).

Both read the same `config.yaml`; the UI lets you review each stage's output before proceeding.

## Supported conversions & platforms

**Conversions** (`generation.type_of_conversion`):
- `Data Vault to Dimensional` or `Raw Vault to Dimensional`
- `3NF to Dimensional`
- `Data Vault to Business Vault` (Raw Vault/Data Vault → Business Vault)
- `Bronze to Raw Vault` (Bronze → Raw Vault/Data Vault; hub / sat / link)

**Data platforms**
- **DDL:** Databricks, Snowflake, Microsoft Fabric, Google BigQuery
- **Staging SQL / config scripts / notebooks:** Databricks

**LLM backends:** Azure OpenAI (GPT-4o / GPT-5), Google Vertex (Claude).
