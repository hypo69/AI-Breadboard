# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Scripts Dev - Convert To Md
# =============================================================================
# Description:
#   Media data to Markdown conversion utility.
#
# Usage Examples:
#   Python API:
#     import scripts.dev.convert_to_md as convert_to_md
#
# File: convert_to_md.py
# Project: ai-breadboard
# Package: scripts.dev
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:27:07
# =============================================================================

"""Media data to Markdown conversion utility.

Converts media metadata and descriptions from JSON format into formatted
Markdown reports with sections for plot, seasons, episodes, and verdicts."""

import json
from pathlib import Path
from header import __root__
REPORTS_DIR = __root__ / 'tmp' / 'reports'
json_data = '\n{\n  "title": "Example Title",\n  "plot": "Plot description here...",\n  "seasons": [\n    {\n      "season_number": 1,\n      "season_plot_summary": "Season summary...",\n      "episodes": [\n        {"episode_number": 1, "title": "Episode 1", "detailed_description": "Description...", "final_verdict": "Verdict text."}\n      ]\n    }\n  ]\n}\n'
data = json.loads(json_data)
md_content = f"# {data['title']}\n\n"
md_content += f"## Plot\n{data['plot']}\n\n"
for season in data.get('seasons', []):
    md_content += f"## Season {season['season_number']}\n"
    md_content += f"{season['season_plot_summary']}\n\n"
    md_content += '### Episodes\n'
    for ep in season.get('episodes', []):
        md_content += f"#### {ep['episode_number']}. {ep['title']}\n"
        md_content += f"{ep['detailed_description']}\n\n"
        md_content += f"**Verdict:** {ep['final_verdict']}\n\n"
output_path = REPORTS_DIR / 'media_report.md'
output_path.write_text(md_content, encoding='utf-8')
print(f'✅ Report saved: {output_path}')