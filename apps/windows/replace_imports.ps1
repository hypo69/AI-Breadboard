<#
=============================================================================
Process Name: AI-Breadboard Automation - Replace Imports
=============================================================================
Description:
  PowerShell-сценарий автоматизации и системного обслуживания (replace_imports).

Usage Examples:
  PowerShell Execution:
    .\replace_imports.ps1

File: replace_imports.ps1
Project: ai-breadboard
Package: apps/windows
Author: hypo69
Copyright: © 2026 hypo69
Updated: 2026-10-02 21:57:05
=============================================================================
#>

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
