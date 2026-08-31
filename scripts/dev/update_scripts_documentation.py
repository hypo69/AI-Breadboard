# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Automatic scripts documentation generator
# =============================================================================
# Description:
#   Automatically updates project scripts documentation. Runs regularly
#   to maintain SCRIPTS_DOCUMENTATION.md currency.
#
# File: update_scripts_documentation.py
# Project: ai-breadboard
# Package: scripts.dev
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Automatic scripts documentation generation and update script.

Scans all project scripts, categorizes them, extracts metadata and
generates comprehensive markdown documentation."""

import os
import sys
import re
from pathlib import Path
from datetime import datetime
from collections import defaultdict

PROJECT_ROOT = Path(__file__).parent

# Script categories with descriptions
SCRIPT_CATEGORIES = {
    'launch_scripts': {
        'name': 'Main launch scripts',
        'description': 'Scripts for launching and configuring main system components',
        'patterns': ['*.ps1', 'main.py', 'bot_runner.py'],
        'priority': '✅ Critical'
    },
    'cli_utilities': {
        'name': 'CLI management and utilities',
        'description': 'Command-line interface for system management',
        'patterns': ['manage_*.py'],
        'priority': '✅ Important'
    },
    'media_processing': {
        'name': 'Media library processing',
        'description': 'Media library work, classification, database updates',
        'patterns': ['audit_*.py', 'generate_*.py', 'complete_*.py', 'fill_*.py', 'update_media_*.py'],
        'priority': '✅ Important'
    },
    'analysis': {
        'name': 'Analysis and reporting',
        'description': 'Data analysis and report generation',
        'patterns': ['analyze_*.py'],
        'priority': '🔶 Useful'
    },
    'diagnostics': {
        'name': 'Checks and diagnostics',
        'description': 'System state verification',
        'patterns': ['check_*.py', 'debug_*.py'],
        'priority': '🔶 Useful'
    },
    'database': {
        'name': 'Database operations',
        'description': 'Database maintenance',
        'patterns': ['update_db*.py', 'get_schema.py', 'remove_columns.py'],
        'priority': '🔶 Technical'
    },
    'migration': {
        'name': 'Migrations and backups',
        'description': 'Data migration and backup',
        'patterns': ['*migration*.py'],
        'priority': '🔶 Operational'
    },
    'counting': {
        'name': 'Statistics and metrics',
        'description': 'Various metrics counting',
        'patterns': ['count_*.py'],
        'priority': '🔶 Utilities'
    },
    'other': {
        'name': 'Other scripts',
        'description': 'Scripts not matching other categories',
        'patterns': ['*.py'],
        'priority': '🔶 Miscellaneous'
    }
}

def get_script_info(script_path):
    """Extract script information from file content.
    
    Args:
        script_path: Path to script file.
        
    Returns:
        Dictionary with script metadata: name, size, modified time, lines, purpose, dependencies.
    """
    info = {
        'name': script_path.name,
        'size': script_path.stat().st_size,
        'modified': datetime.fromtimestamp(script_path.stat().st_mtime),
        'lines': 0,
        'purpose': 'Not defined',
        'dependencies': [],
        'usage_examples': []
    }
    
    try:
        content = script_path.read_text(encoding='utf-8', errors='ignore')
        info['lines'] = len(content.split('\n'))
        
        # Extract purpose from docstring or comments
        lines = content.split('\n')
        purpose_found = False
        
        for i, line in enumerate(lines[:20]):  # Check first 20 lines
            line_lower = line.lower()
            
            # Look for docstring
            if '"""' in line and not purpose_found and i < 10:
                # Multi-line docstring
                docstring_lines = []
                for j in range(i + 1, min(i + 10, len(lines))):
                    if '"""' in lines[j]:
                        break
                    docstring_lines.append(lines[j].strip())
                if docstring_lines:
                    info['purpose'] = ' '.join(docstring_lines[:3])[:200]
                    purpose_found = True
            
            # Look for single-line comments with purpose
            elif not purpose_found and line.strip().startswith('#') and any(word in line_lower for word in ['purpose', 'description']):
                info['purpose'] = line.strip('# \t\n\r')[:200]
                purpose_found = True
        
        # If purpose not found, use first meaningful line
        if not purpose_found:
            for line in lines:
                if line.strip() and not line.strip().startswith(('#', '"', "'", 'import', 'from')):
                    info['purpose'] = line.strip()[:150]
                    break
        
        # Search for dependencies
        for line in lines:
            if 'import' in line:
                # Simple imports
                if 'import ' in line and ' as ' not in line:
                    parts = line.split('import')[1].strip().split(',')
                    for part in parts:
                        module = part.strip().split()[0]
                        if module and '.' not in module:  # Top-level modules only
                            info['dependencies'].append(module)
        
    except Exception as e:
        info['purpose'] = f"Error reading: {str(e)}"
    
    return info

def categorize_script(script_name):
    """Determine script category based on filename.
    
    Args:
        script_name: Name of the script file.
        
    Returns:
        Category ID string.
    """
    for category_id, category_info in SCRIPT_CATEGORIES.items():
        for pattern in category_info['patterns']:
            # Convert pattern to regex
            regex_pattern = pattern.replace('*', '.*').replace('?', '.')
            if re.match(f'^{regex_pattern}$', script_name):
                return category_id
    return 'other'

def generate_documentation():
    """Generate and save scripts documentation.
    
    Scans all project scripts, categorizes them, and creates comprehensive
    markdown documentation file.
    """
    print("Generating scripts documentation...")
    
    # Collect all scripts
    all_scripts = []
    
    # Python scripts
    for py_file in PROJECT_ROOT.glob("*.py"):
        if py_file.name not in ['analyze_dependencies.py', 'update_scripts_documentation.py']:
            all_scripts.append(py_file)
    
    # PowerShell scripts
    for ps1_file in PROJECT_ROOT.glob("*.ps1"):
        all_scripts.append(ps1_file)
    
    # Group by categories
    categorized_scripts = defaultdict(list)
    
    for script_path in all_scripts:
        category = categorize_script(script_path.name)
        script_info = get_script_info(script_path)
        categorized_scripts[category].append(script_info)
    
    # Sort within categories
    for category in categorized_scripts:
        categorized_scripts[category].sort(key=lambda x: x['name'].lower())
    
    # Generate Markdown documentation
    md_content = []
    
    # Header
    md_content.append(f"# Scripts Documentation for ai-breadboard project\n")
    md_content.append(f"**Version:** 1.0  \n")
    md_content.append(f"**Updated:** {datetime.now().strftime('%d %B %Y')}  \n")
    md_content.append(f"**Status:** Current (auto-updated)\n")
    
    # Statistics
    md_content.append("## General Statistics\n")
    md_content.append("| Category | Count | Status |")
    md_content.append("|----------|-------|--------|")
    
    total_scripts = 0
    for category_id, scripts in categorized_scripts.items():
        if scripts:  # Only non-empty categories
            category_info = SCRIPT_CATEGORIES[category_id]
            count = len(scripts)
            total_scripts += count
            md_content.append(f"| {category_info['name']} | {count} | {category_info['priority']} |")
    
    md_content.append(f"| **Total active scripts** | **{total_scripts}** | |\n")
    
    # Detailed descriptions by categories
    for category_id, scripts in categorized_scripts.items():
        if not scripts:
            continue
            
        category_info = SCRIPT_CATEGORIES[category_id]
        md_content.append(f"\n## {category_info['name']}\n")
        md_content.append(f"**Description:** {category_info['description']}  \n")
        md_content.append(f"**Status:** {category_info['priority']}\n")
        
        for script in scripts:
            md_content.append(f"\n### **{script['name']}**")
            
            if script['name'].endswith('.ps1'):
                md_content.append(f"**Type:** PowerShell script  \n")
            else:
                md_content.append(f"**Type:** Python script  \n")
            
            md_content.append(f"**Size:** {script['size']:,} bytes  \n")
            md_content.append(f"**Lines of code:** {script['lines']}  \n")
            md_content.append(f"**Modified:** {script['modified'].strftime('%Y-%m-%d %H:%M')}  \n")
            md_content.append(f"**Purpose:** {script['purpose']}\n")
            
            # Usage examples for main scripts
            if script['name'] in ['run.ps1', 'manage_tools.py']:
                md_content.append(f"**Usage Examples:**\n")
                
                if script['name'] == 'run.ps1':
                    md_content.append(f"```bash\n.\\run.ps1\n```\n")
                elif script['name'] == 'manage_tools.py':
                    md_content.append(f"```bash\npy manage_tools.py rag rebuild       # Rebuild RAG index\npy manage_tools.py knowledge extract # Extract knowledge\n```\n")
    
    # Maintenance principles
    md_content.append("\n## Maintenance Principles\n")
    md_content.append("### 1. Regular documentation updates\n")
    md_content.append("- This documentation updates automatically when running `update_scripts_documentation.py`\n")
    md_content.append("- Recommended to run after adding or removing scripts\n")
    
    md_content.append("\n### 2. Automatic updates\n")
    md_content.append("```bash\n# Update documentation\npython update_scripts_documentation.py\n```\n")
    
    md_content.append("\n### 3. Dependency analysis\n")
    md_content.append("```bash\n# Analyze dependencies between scripts\npython analyze_dependencies.py\n```\n")
    
    # Project info
    md_content.append("\n## Contacts and Support\n")
    md_content.append(f"**Project:** ai-breadboard  \n")
    md_content.append(f"**Last updated:** {datetime.now().strftime('%d %B %Y %H:%M')}  \n")
    md_content.append(f"**Update script:** `update_scripts_documentation.py`  \n")
    md_content.append("\n*Documentation automatically updates when repository changes.*\n")
    
    # Save documentation
    doc_file = PROJECT_ROOT / "SCRIPTS_DOCUMENTATION.md"
    doc_file.write_text('\n'.join(md_content), encoding='utf-8')
    
    print(f"✅ Documentation saved to {doc_file}")
    print(f"📊 Processed {len(all_scripts)} scripts")
    
    # Also create brief summary
    create_summary(categorized_scripts)

def create_summary(categorized_scripts):
    """Create brief summary of scripts.
    
    Args:
        categorized_scripts: Dictionary of scripts organized by category.
    """
    summary = ["# Scripts Summary\n"]
    summary.append(f"*Updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n")
    
    for category_id, scripts in categorized_scripts.items():
        if not scripts:
            continue
            
        category_info = SCRIPT_CATEGORIES[category_id]
        summary.append(f"\n## {category_info['name']} ({len(scripts)})\n")
        
        for script in scripts:
            if script['name'].endswith('.ps1'):
                summary.append(f"- `{script['name']}` - PowerShell ({script['size']:,} bytes)")
            else:
                summary.append(f"- `{script['name']}` - Python ({script['lines']} lines)")
    
    summary_file = PROJECT_ROOT / "SCRIPTS_SUMMARY.md"
    summary_file.write_text('\n'.join(summary), encoding='utf-8')
    
    print(f"📋 Brief summary saved to {summary_file}")

def main():
    """Main function."""
    print("=" * 60)
    print("SCRIPTS DOCUMENTATION UPDATE")
    print("=" * 60)
    
    try:
        generate_documentation()
        
        # Also run dependency analysis for completeness
        print("\n" + "=" * 60)
        print("ADDITIONAL DEPENDENCY ANALYSIS")
        print("=" * 60)
        
        if (PROJECT_ROOT / "analyze_dependencies.py").exists():
            import subprocess
            result = subprocess.run([sys.executable, "analyze_dependencies.py"], 
                                  capture_output=True, text=True)
            print(result.stdout)
            if result.stderr:
                print(f"Warnings: {result.stderr}")
        else:
            print("Script analyze_dependencies.py not found, skipping dependency analysis.")
        
        print("\n" + "=" * 60)
        print("✅ UPDATE COMPLETED SUCCESSFULLY")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error during documentation update: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
