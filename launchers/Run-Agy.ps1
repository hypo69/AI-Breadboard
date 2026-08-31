<#
.SYNOPSIS
    Check, install and run Google Antigravity CLI (agy).

.DESCRIPTION
    Script for checking Antigravity CLI (agy) presence in system, offering
    installation/update if missing, configuring API keys from .env and running
    interactive session or one-off requests to agent.

.PARAMETER Action
    Action to perform:
    - 'check': Check presence and status of agy CLI (default)
    - 'chat': Run interactive console session agy
    - 'models': Show list of available models (agy models)
    - 'update': Update agy utility to latest version (agy update)
    - 'version': Show utility version (agy --version)
    - 'status': Show current environment status

.PARAMETER Prompt
    Optional one-off text request to execute through agy --print.

.PARAMETER Model
    Model for request (default from config.json or agy-flash).

.PARAMETER Help
    Display usage help for script (-Help, -h, --help).

.EXAMPLE
    .\Run-Agy.ps1
    .\Run-Agy.ps1 -Action chat
    .\Run-Agy.ps1 -Action models
    .\Run-Agy.ps1 -Prompt "Explain Antigravity architecture"
    .\Run-Agy.ps1 --help
#>

[CmdletBinding()]
param (
    [ValidateSet('check', 'chat', 'models', 'update', 'version', 'status', 'install')]
    [string]$Action = 'check',

    [Parameter(Position = 0)]
    [string]$Prompt = '',

    [string]$Model = '',

    [Alias('h', '-help')]
    [switch]$Help
)

$ErrorActionPreference = 'Continue'
$env:PYTHONUTF8 = "1"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

$scriptDir = $PSScriptRoot
if ([string]::IsNullOrEmpty($scriptDir) -and $env:AIBREADBOARD_DIR -and (Test-Path $env:AIBREADBOARD_DIR)) {
    $scriptDir = $env:AIBREADBOARD_DIR
}
if ([string]::IsNullOrEmpty($scriptDir) -and $MyInvocation.MyCommand.Path) {
    $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
}
if ([string]::IsNullOrEmpty($scriptDir)) {
    $scriptDir = (Get-Location).Path
}

# Определение корня проекта (если скрипт находится в директории launchers/)
$projectRoot = $scriptDir
if ((Split-Path -Leaf $projectRoot) -eq "launchers" -or -not (Test-Path (Join-Path $projectRoot "main.py"))) {
    $parent = Split-Path -Parent $projectRoot
    if (Test-Path (Join-Path $parent "main.py")) {
        $projectRoot = $parent
    }
}
$env:AIBREADBOARD_DIR = $projectRoot
$env:ASSIST_DIR = $projectRoot

# ============================================
# HELP OUTPUT (--help / -h / -Help)
# ============================================
if ($Help) {
    Write-Host ""
    Write-Host "╔═══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "║              Run-Agy.ps1 — HELP AND PARAMETERS                ║" -ForegroundColor Cyan
    Write-Host "╚═══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "PURPOSE:" -ForegroundColor Yellow
    Write-Host "  Check, install and run Google Antigravity (agy) console agent."
    Write-Host ""
    Write-Host "SYNTAX:" -ForegroundColor Yellow
    Write-Host "  .\Run-Agy.ps1 [-Action <check|chat|models|update|version>]"
    Write-Host "  .\Run-Agy.ps1 -Prompt `"your question`""
    Write-Host "  .\Run-Agy.ps1 --help"
    Write-Host ""
    Write-Host "PARAMETERS:" -ForegroundColor Yellow
    Write-Host "  -Action <string>    Action: check (default), chat, models, update, version."
    Write-Host "  -Prompt <string>    Execute one-off request to model without interactive mode."
    Write-Host "  -Model <string>     Model (e.g.: agy-flash, agy-pro, gemma)."
    Write-Host "  -Help, -h, --help   Show this help and exit."
    Write-Host ""
    Write-Host "EXAMPLES:" -ForegroundColor Yellow
    Write-Host "  .\Run-Agy.ps1"
    Write-Host "  .\Run-Agy.ps1 -Action chat"
    Write-Host "  .\Run-Agy.ps1 -Action models"
    Write-Host "  .\Run-Agy.ps1 -Prompt `"Optimize search algorithm`""
    Write-Host ""
    exit 0
}

Write-Host ""
Write-Host "╔═══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║          GOOGLE ANTIGRAVITY (AGY) — DIAGNOSTICS AND LAUNCH    ║" -ForegroundColor Cyan
Write-Host "╚═══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# ============================================
# [1/4] LOADING .ENV AND CONFIGURATION
# ============================================
$envFile = Join-Path $projectRoot ".env"
$agyApiKey = $null

if (Test-Path $envFile) {
    Get-Content $envFile | ForEach-Object {
        $line = $_.Trim()
        if ($line -and -not $line.StartsWith('#') -and $line -match "^([^=]+)=(.*)$") {
            $key = $Matches[1].Trim()
            $val = $Matches[2].Trim().Trim('"').Trim("'")
            if ($key -in @("AGY_API_KEY", "GEMINI_API_KEY", "GOOGLE_API_KEY")) {
                if (-not $agyApiKey -and $val) {
                    $agyApiKey = $val
                }
            }
        }
    }
}

if ($agyApiKey) {
    $env:AGY_API_KEY = $agyApiKey
    $env:GEMINI_API_KEY = $agyApiKey
}

$configPath = Join-Path $projectRoot "config.json"
$defaultModel = "agy-flash"
if (Test-Path $configPath) {
    try {
        $cfg = Get-Content $configPath -Raw | ConvertFrom-Json
        if ($cfg.ai.agy_model_id) {
            $defaultModel = [string]$cfg.ai.agy_model_id
        } elseif ($cfg.web_search.agy_model) {
            $defaultModel = [string]$cfg.web_search.agy_model
        }
    } catch {}
}

if (-not $Model) {
    $Model = $defaultModel
}

# ============================================
# [2/4] FINDING AGY CLI EXECUTABLE
# ============================================
function Find-AgyCli {
    $candidates = @("agy.exe", "agy.cmd", "agy.ps1", "agy")
    foreach ($c in $candidates) {
        $cmd = Get-Command $c -ErrorAction SilentlyContinue
        if ($cmd -and $cmd.Source) {
            return $cmd.Source
        }
    }

    # Standard Antigravity installation paths on Windows
    $localAgy = Join-Path $env:LOCALAPPDATA "agy\bin\agy.exe"
    if (Test-Path $localAgy) {
        return $localAgy
    }

    $geminiAgy = Join-Path $env:USERPROFILE ".gemini\antigravity\bin\agy.exe"
    if (Test-Path $geminiAgy) {
        return $geminiAgy
    }

    $progAgy = Join-Path $env:ProgramFiles "Antigravity\bin\agy.exe"
    if (Test-Path $progAgy) {
        return $progAgy
    }

    return $null
}

function Install-AgyCli {
    Write-Host ""
    Write-Host "📦 Installing Google Antigravity CLI (agy)..." -ForegroundColor Cyan
    $wingetCmd = Get-Command winget -ErrorAction SilentlyContinue
    if ($wingetCmd) {
        Write-Host "   Attempting installation via Windows Package Manager (winget)..." -ForegroundColor DarkGray
        try {
            & winget install Google.Antigravity --silent --accept-package-agreements --accept-source-agreements
            if ($LASTEXITCODE -eq 0) {
                Write-Host "✅ Google Antigravity successfully installed via winget!" -ForegroundColor Green
                return $true
            }
        } catch {}
    }

    $npmCmd = Get-Command npm -ErrorAction SilentlyContinue
    if ($npmCmd) {
        Write-Host "   Attempting installation via npm (antigravity-cli / @google/antigravity)..." -ForegroundColor DarkGray
        try {
            & npm install -g antigravity-cli 2>$null
            if ($LASTEXITCODE -eq 0) {
                Write-Host "✅ Antigravity CLI successfully installed via npm!" -ForegroundColor Green
                return $true
            }
        } catch {}
    }

    Write-Host "ℹ️ Automatic installation via winget/npm failed." -ForegroundColor Yellow
    Write-Host "   Please install Google Antigravity from official website or installer." -ForegroundColor Yellow
    return $false
}

$cliPath = Find-AgyCli

# ============================================
# [3/4] HANDLING SITUATION IF AGY NOT FOUND
# ============================================
if (-not $cliPath -or $Action -in @('install', 'update')) {
    if (-not $cliPath) {
        Write-Host "[WARN] Google Antigravity CLI (agy) not found in system!" -ForegroundColor Yellow
        Write-Host ""
        $answer = Read-Host "Do you want to try installing Google Antigravity CLI now? (Y/n) [Enter = Yes]"
        $answer = $answer.Trim().ToLower()
        if ($answer -in @("", "y", "yes", "d", "da", "1")) {
            $installed = Install-AgyCli
            if ($installed) {
                $cliPath = Find-AgyCli
            }
        } else {
            Write-Host ""
            Write-Host "Installation skipped. Download Antigravity distribution for agy to work." -ForegroundColor Yellow
            Write-Host ""
            exit 1
        }
    } elseif ($Action -eq 'update') {
        Write-Host "🔄 Updating Antigravity CLI..." -ForegroundColor Cyan
        & $cliPath update
        exit $LASTEXITCODE
    }
}

if (-not $cliPath) {
    Write-Host "❌ agy executable not found. Restart console after installation." -ForegroundColor Red
    exit 1
}

# Determine version
$versionStr = "Unknown"
try {
    $verOut = & $cliPath --version 2>$null
    if ($verOut) { $versionStr = $verOut.Trim() }
} catch {}

Write-Host "    [OK] Antigravity CLI found: $cliPath" -ForegroundColor Green
Write-Host "    Version:      $versionStr" -ForegroundColor Gray
Write-Host "    Model:        $Model" -ForegroundColor Gray
if ($env:AGY_API_KEY -or $env:GEMINI_API_KEY) {
    Write-Host "    API Key:      Loaded from .env" -ForegroundColor Green
} else {
    Write-Host "    [WARN] API Key (AGY_API_KEY / GEMINI_API_KEY) not found in .env!" -ForegroundColor Yellow
}
Write-Host ""

# ============================================
# [4/4] PERFORMING ACTIONS (PROMPT / CHAT / MODELS)
# ============================================
if ($Action -eq 'version') {
    Write-Host "Antigravity CLI Version: $versionStr" -ForegroundColor Green
    exit 0
}

if ($Action -eq 'models') {
    Write-Host "📋 List of available Antigravity models:" -ForegroundColor Cyan
    Write-Host "───────────────────────────────────────────────────────────────" -ForegroundColor DarkGray
    & $cliPath models
    exit $LASTEXITCODE
}

# If direct text request passed (-Prompt)
if ($Prompt) {
    Write-Host "💬 Request to agy: $Prompt" -ForegroundColor Cyan
    Write-Host "───────────────────────────────────────────────────────────────" -ForegroundColor DarkGray
    & $cliPath --print $Prompt
    exit $LASTEXITCODE
}

# If interactive chat requested (-Action chat)
if ($Action -eq 'chat') {
    Write-Host "🚀 Launching interactive Google Antigravity (agy) console..." -ForegroundColor Green
    Write-Host "───────────────────────────────────────────────────────────────" -ForegroundColor DarkGray
    & $cliPath
    exit $LASTEXITCODE
}

# Check mode (default)
Write-Host "╔═══════════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║  ANTIGRAVITY CLI (AGY) READY TO WORK                          ║" -ForegroundColor Green
Write-Host "╚═══════════════════════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""
Write-Host "Commands for working:" -ForegroundColor Yellow
Write-Host "  .\Run-Agy.ps1 -Action chat              # Interactive console"
Write-Host "  .\Run-Agy.ps1 -Action models            # List of models"
Write-Host "  .\Run-Agy.ps1 -Prompt `"Your question`"  # One-off request"
Write-Host "  .\Run-Agy.ps1 -Action update            # Update CLI"
Write-Host ""
