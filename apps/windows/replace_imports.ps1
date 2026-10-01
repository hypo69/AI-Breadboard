# =============================================================================
# Process Name: AI-Breadboard Automation - Replace Imports Script
# =============================================================================
# Description:
#   PowerShell-сценарий системного обслуживания и запуска (replace_imports).
#
# Usage Examples:
#   PowerShell Execution:
#     .\replace_imports.ps1
#
# File: replace_imports.ps1
# Project: ai-breadboard
# Package: apps.windows
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:28:28
# =============================================================================

# Description:
#   PowerShell-сценарий администрирования и автоматизации (replace_imports).
#
# Usage Examples:
#   PowerShell Execution:
#     .\replace_imports.ps1
#
# File: replace_imports.ps1
# Project: ai-breadboard
# Package: windows
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:04:40
# =============================================================================

# Description:
#   PowerShell-сценарий системных операций и автоматизации (replace_imports).
#
# Usage Examples:
#   PowerShell:
#     .\replace_imports.ps1
#
# File: replace_imports.ps1
# Project: ai-breadboard
# Package: windows
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 12:54:56
# =============================================================================

Get-ChildItem -Path 'C:/Users/onela/AppData/Local/AI-Breadboard/apps/windows' -Recurse -Filter *.py |
    ForEach-Object {
        $path = $_.FullName
        $content = Get-Content $path -Raw
        $new = $content -replace 'apps\.windows\.api\.', 'apps.windows.telemetry.win32_ffi.'
        if ($new -ne $content) {
            Set-Content -Path $path -Value $new -Encoding utf8
            Write-Host "Updated imports in $path"
        }
    }
