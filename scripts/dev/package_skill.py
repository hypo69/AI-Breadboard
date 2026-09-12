# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Package Gemini skills into distributable archives
# =============================================================================
# Description:
#   Utility for packaging Gemini CLI skills into ZIP archives for distribution.
#   Automatically excludes build artifacts and version control directories.
#
# File: package_skill.py
# Project: ai-breadboard
# Package: scripts.dev
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Gemini skills packaging utility.

Packages skill directories into ZIP archive format for distribution,
automatically excluding build artifacts and version control files."""

import os
import zipfile
import argparse
from pathlib import Path

def package_skill(skill_dir, output_dir):
    """Package a skill directory into a distributable archive.
    
    Args:
        skill_dir: Path to skill directory to package.
        output_dir: Path to output directory for packaged skill file.
    """
    skill_path = Path(skill_dir).resolve()
    output_path = Path(output_dir).resolve()
    
    if not output_path.exists():
        output_path.mkdir(parents=True)
        
    skill_name = skill_path.name
    skill_file = output_path / f"{skill_name}.skill"
    
    print(f"Packaging skill from {skill_path} to {skill_file}...")
    
    with zipfile.ZipFile(skill_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(skill_path):
            # Skip dist and git directories
            dirs[:] = [d for d in dirs if d not in ['dist', '.git', '__pycache__']]
            
            for file in files:
                file_path = Path(root) / file
                # Relative path within archive
                arcname = file_path.relative_to(skill_path)
                zipf.write(file_path, arcname)
                
    print(f"Skill packaged successfully: {skill_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Gemini CLI skills packager")
    parser.add_argument("skill_dir", help="Path to skill directory")
    parser.add_argument("output_dir", help="Path to dist directory")
    args = parser.parse_args()
    
    package_skill(args.skill_dir, args.output_dir)
