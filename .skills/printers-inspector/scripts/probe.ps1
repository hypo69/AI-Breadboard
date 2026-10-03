<#
=============================================================================
Process Name: AI-Breadboard Automation - Probe
=============================================================================
Description:
  PowerShell-сценарий автоматизации и системного обслуживания (probe).

Usage Examples:
  PowerShell Execution:
    .\probe.ps1

File: probe.ps1
Project: ai-breadboard
Package: .skills/printers-inspector/scripts
Author: hypo69
Copyright: © 2026 hypo69
Updated: 2026-10-02 21:57:05
=============================================================================
#>

Get-Printer -ErrorAction SilentlyContinue | Select-Object Name, Type, DriverName, PortName, Shared, Default | ConvertTo-Json