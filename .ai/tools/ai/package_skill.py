# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Module
# =============================================================================
# Description:
#   Module for AI Breadboard project.
#
# File: package_skill.py
# Project: ai-breadboard
# Package: .ai.tools.ai
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import os
import zipfile
import argparse
from pathlib import Path

def package_skill(skill_dir, output_dir):
    skill_path = Path(skill_dir).resolve()
    output_path = Path(output_dir).resolve()
    
    if not output_path.exists():
        output_path.mkdir(parents=True)
        
    skill_name = skill_path.name
    skill_file = output_path / f"{skill_name}.skill"
    
    print(f"Упаковка навыка из {skill_path} в {skill_file}...")
    
    with zipfile.ZipFile(skill_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(skill_path):
            # Пропускаем директории dist и .git
            dirs[:] = [d for d in dirs if d not in ['dist', '.git', '__pycache__']]
            
            for file in files:
                file_path = Path(root) / file
                # Относительный путь внутри архива
                arcname = file_path.relative_to(skill_path)
                zipf.write(file_path, arcname)
                
    print(f"Навык successfully упакован: {skill_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Упаковщик навыков Gemini CLI")
    parser.add_argument("skill_dir", help="Путь к директории навыка")
    parser.add_argument("output_dir", help="Путь к директории dist")
    args = parser.parse_args()
    
    package_skill(args.skill_dir, args.output_dir)
