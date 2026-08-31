# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Convert media data to Markdown format
# =============================================================================
# Description:
#   Converts media data from JSON format to formatted Markdown reports
#   for human-readable display and documentation purposes.
#
# File: convert_to_md.py
# Project: ai-breadboard
# Package: scripts.dev
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Media data to Markdown conversion utility.

Converts media metadata and descriptions from JSON format into formatted
Markdown reports with sections for plot, seasons, episodes, and verdicts."""

import json
from pathlib import Path
from header import __root__

REPORTS_DIR = __root__ / 'tmp' / 'reports'

# Load JSON data (replace with real data from previous step)
# Example structure from previous processing
json_data = """
{
  "title": "Example Title",
  "plot": "Plot description here...",
  "seasons": [
    {
      "season_number": 1,
      "season_plot_summary": "Season summary...",
      "episodes": [
        {"episode_number": 1, "title": "Episode 1", "detailed_description": "Description...", "final_verdict": "Verdict text."}
      ]
    }
  ]
}
"""
data = json.loads(json_data)

md_content = f"# {data['title']}\n\n"
md_content += f"## Plot\n{data['plot']}\n\n"

for season in data.get('seasons', []):
    md_content += f"## Season {season['season_number']}\n"
    md_content += f"{season['season_plot_summary']}\n\n"
    md_content += "### Episodes\n"
    for ep in season.get('episodes', []):
        md_content += f"#### {ep['episode_number']}. {ep['title']}\n"
        md_content += f"{ep['detailed_description']}\n\n"
        md_content += f"**Verdict:** {ep['final_verdict']}\n\n"

output_path = REPORTS_DIR / "media_report.md"
output_path.write_text(md_content, encoding='utf-8')
print(f"✅ Report saved: {output_path}")
