"""
Stage 1 — Erwin XML → normalised STTM JSON.

Thin OOP wrapper around `xmltojson.parse_erwin_full_mapping`. The actual
XML walking, UDP extraction, PK/FK detection, and watermark handling
remain inside the original function — this class only owns the lifecycle
(existence check, banner, sys.exit-on-missing) the way the original
`main.py` did.
"""

from __future__ import annotations

import os
import sys
from typing import Any, Dict

from pipeline.base import PipelineStage
from modules.xmltojson import parse_erwin_full_mapping


class XmlToJsonStage(PipelineStage):
    """Parses the Erwin XML repository into the canonical STTM JSON."""

    def __init__(self, config):
        super().__init__(config, name="STEP 1 — Erwin XML → JSON")

    def _run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        xml_path = self.config.input_xml_file

        if not os.path.exists(xml_path):
            print(f"File {xml_path} not found.")
            sys.exit(1)

        parse_erwin_full_mapping(xml_path, self.config.output_json_file)
        return {
            "input_xml_file": xml_path,
            "output_json_file": self.config.output_json_file,
        }
