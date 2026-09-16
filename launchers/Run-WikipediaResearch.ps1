<#
.SYNOPSIS
    Launcher script for Wikipedia Research and Model Benchmark Application.
.DESCRIPTION
    Runs the Wikipedia Research Laboratory standalone TUI, launches API server,
    or runs predefined Language (Exp A) and Model (Exp B) research experiments.
.EXAMPLE
    .\launchers\Run-WikipediaResearch.ps1
    .\launchers\Run-WikipediaResearch.ps1 -Server
    .\launchers\Run-WikipediaResearch.ps1 -Topic "Quantum computing" -ExpA
#>

[CmdletBinding()]
param (
    [switch]$Server,
    [switch]$ExpA,
    [switch]$ExpB,
    [string]$Topic = "Israel–Gaza war",
    [int]$Port = 8110
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RootDir = Split-Path -Parent $ScriptDir

Set-Location -Path $RootDir

Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host "  🌐 AI Breadboard - Wikipedia Research & Model Laboratory      " -ForegroundColor Yellow
Write-Host "=================================================================" -ForegroundColor Cyan

if ($Server) {
    Write-Host "Starting Wikipedia Research Standalone API Server on port $Port..." -ForegroundColor Green
    python -m apps.wikipedia_research --mode server --port $Port
}
elseif ($ExpA) {
    Write-Host "Running Experiment A (Language Comparison) for topic: '$Topic'..." -ForegroundColor Green
    python -m apps.wikipedia_research --mode experiment_a --topic "$Topic"
}
elseif ($ExpB) {
    Write-Host "Running Experiment B (Multi-Model Benchmark) for topic: '$Topic'..." -ForegroundColor Green
    python -m apps.wikipedia_research --mode experiment_b --topic "$Topic"
}
else {
    Write-Host "Launching Interactive Wikipedia Research TUI Dashboard..." -ForegroundColor Green
    python -m apps.wikipedia_research --topic "$Topic"
}
