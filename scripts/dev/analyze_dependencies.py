# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Find all Python files in project root
# =============================================================================
# Description:
#   Analyzes dependencies between scripts in project. Helps determine which
#   scripts are used by others and which can be safely deleted.
#
# File: analyze_dependencies.py
# Project: ai-breadboard
# Package: scripts.dev
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Script dependency analysis utility.

Analyzes dependencies between project scripts to identify usage patterns
and help determine which scripts can be safely removed."""

import ast
import re
from pathlib import Path
from collections import defaultdict
from typing import Set, Dict, List

class ScriptAnalyzer:
    """Analyzes Python scripts for dependencies."""
    
    def __init__(self, root_dir: Path):
        """Initialize analyzer.
        
        Args:
            root_dir: Root directory to analyze.
        """
        self.root_dir = root_dir
        self.scripts = {}
        self.dependencies = defaultdict(set)
        self.imports = defaultdict(set)

    def find_all_scripts(self) -> List[Path]:
        """Find all Python files in root directory.
        
        Returns:
            List of Path objects for .py files.
        """
        scripts = []
        for py_file in self.root_dir.glob("*.py"):
            if py_file.name not in ['analyze_dependencies.py', 'update_scripts_documentation.py']:
                scripts.append(py_file)
        return scripts

    def analyze_imports(self, script_path: Path) -> Set[str]:
        """Extract imports from Python script.
        
        Args:
            script_path: Path to script file.
            
        Returns:
            Set of imported module names.
        """
        imports = set()
        try:
            with open(script_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse imports
            import_pattern = r'(?:from|import)\s+[\w.]+'
            for match in re.finditer(import_pattern, content):
                import_str = match.group()
                parts = import_str.split()
                if parts[0] == 'import':
                    module = parts[1].split('.')[0]
                elif parts[0] == 'from':
                    module = parts[1]
                else:
                    continue
                imports.add(module)
        except Exception:
            pass
        
        return imports

    def analyze_all(self) -> None:
        """Analyze all scripts in directory."""
        scripts = self.find_all_scripts()
        
        for script_path in scripts:
            imports = self.analyze_imports(script_path)
            self.scripts[script_path.name] = {
                'path': script_path,
                'imports': imports
            }
            self.imports[script_path.name] = imports

    def report(self) -> None:
        """Generate dependency report."""
        print("\n" + "="*70)
        print("SCRIPT DEPENDENCY ANALYSIS REPORT")
        print("="*70 + "\n")
        
        # Summary
        print(f"Total scripts analyzed: {len(self.scripts)}\n")
        
        # Scripts with most dependencies
        print("Scripts with most dependencies:")
        print("-" * 70)
        sorted_scripts = sorted(
            self.scripts.items(),
            key=lambda x: len(x[1]['imports']),
            reverse=True
        )
        for script_name, info in sorted_scripts[:5]:
            print(f"  {script_name}: {len(info['imports'])} imports")
        
        print("\n" + "="*70)
        print("Import inventory:")
        print("-" * 70)
        
        all_imports = set()
        for imports in self.imports.values():
            all_imports.update(imports)
        
        external_imports = []
        internal_imports = []
        standard_imports = []
        
        std_modules = {'sys', 'os', 'json', 'pathlib', 'argparse', 'subprocess', 
                       'asyncio', 're', 'typing', 'collections', 'datetime', 'urllib'}
        
        for imp in sorted(all_imports):
            if imp.startswith(('core', 'plugins', 'scripts')):
                internal_imports.append(imp)
            elif imp in std_modules or imp.startswith(('__', '_')):
                standard_imports.append(imp)
            else:
                external_imports.append(imp)
        
        print(f"\nStandard library: {len(standard_imports)} modules")
        print(f"Internal modules: {len(internal_imports)} modules")
        if internal_imports:
            for imp in internal_imports:
                print(f"  - {imp}")
        
        print(f"\nExternal packages: {len(external_imports)} packages")
        if external_imports:
            for imp in external_imports[:10]:
                print(f"  - {imp}")
            if len(external_imports) > 10:
                print(f"  ... and {len(external_imports) - 10} more")
        
        print("\n" + "="*70 + "\n")

def main():
    """Main entry point."""
    from header import __root__
    
    analyzer = ScriptAnalyzer(__root__)
    analyzer.analyze_all()
    analyzer.report()

if __name__ == "__main__":
    main()
