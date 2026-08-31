<#
.SYNOPSIS
    Check, install and run Google Gemini CLI (@google/gemini-cli).

.DESCRIPTION
    Script for checking Gemini CLI presence in system, automatic offer to install
    via npm if missing, configuring API keys from .env and running interactive
    session or single requests.

.PARAMETER Action
    Action to perform:
    - 'check': Check presence and status of Gemini CLI
    - 'install': Install/update Gemini CLI via npm
    - 'chat': Run interactive console session
    - 'version': Show utility version
    Default: 'check'.

.PARAMETER Prompt
    Optional one-off text request to execute through Gemini CLI.

.PARAMETER Model
    Gemini model for request (default from config.json or gemini-2.5-flash).

.PARAMETER Help
    Display usage help for script (-Help, -h, --help).

.EXAMPLE
    .\Run-GeminiCli.ps1
    .\Run-GeminiCli.ps1 -Action install
    .\Run-GeminiCli.ps1 -Action chat
    .\Run-GeminiCli.ps1 -Prompt "Hello, tell me about the project"
    .\Run-GeminiCli.ps1 --help
#>

[CmdletBinding()]
param (
    [ValidateSet('check', 'install', 'chat', 'version', 'status')]
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
    Write-Host "║           Run-GeminiCli.ps1 — HELP AND PARAMETERS             ║" -ForegroundColor Cyan
    Write-Host "╚═══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "PURPOSE:" -ForegroundColor Yellow
    Write-Host "  Check, install and run Google Gemini CLI console agent."
    Write-Host ""
    Write-Host "SYNTAX:" -ForegroundColor Yellow
    Write-Host "  .\Run-GeminiCli.ps1 [-Action <check|install|chat|version>]"
    Write-Host "  .\Run-GeminiCli.ps1 -Prompt `"your question`""
    Write-Host "  .\Run-GeminiCli.ps1 --help"
    Write-Host ""
    Write-Host "PARAMETERS:" -ForegroundColor Yellow
    Write-Host "  -Action <string>    Action: check (default), install, chat, version."
    Write-Host "  -Prompt <string>    Execute one-off request to model."
    Write-Host "  -Model <string>     Model (e.g.: gemini-2.5-flash, gemini-3.1-flash-lite)."
    Write-Host "  -Help, -h, --help   Show this help and exit."
    Write-Host ""
    Write-Host "EXAMPLES:" -ForegroundColor Yellow
    Write-Host "  .\Run-GeminiCli.ps1"
    Write-Host "  .\Run-GeminiCli.ps1 -Action install"
    Write-Host "  .\Run-GeminiCli.ps1 -Action chat"
    Write-Host "  .\Run-GeminiCli.ps1 -Prompt `"Explain FastAPI architecture`""
    Write-Host ""
    exit 0
}

Write-Host ""
Write-Host "╔═══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║              GOOGLE GEMINI CLI — DIAGNOSTICS AND LAUNCH       ║" -ForegroundColor Cyan
Write-Host "╚═══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# ============================================
# [1/4] LOADING .ENV AND CONFIGURATION
# ============================================
$envFile = Join-Path $projectRoot ".env"
$geminiApiKey = $null

if (Test-Path $envFile) {
    Get-Content $envFile | ForEach-Object {
        $line = $_.Trim()
        if ($line -and -not $line.StartsWith('#') -and $line -match "^([^=]+)=(.*)$") {
            $key = $Matches[1].Trim()
            $val = $Matches[2].Trim().Trim('"').Trim("'")
            if ($key -in @("GEMINI_API_KEY", "GOOGLE_API_KEY", "AGY_API_KEY")) {
                if (-not $geminiApiKey -and $val) {
                    $geminiApiKey = $val
                }
            }
        }
    }
}

# Export API key to session for gemini-cli
if ($geminiApiKey) {
    $env:GEMINI_API_KEY = $geminiApiKey
}

$configPath = Join-Path $projectRoot "config.json"
$defaultModel = "gemini-2.5-flash"
if (Test-Path $configPath) {
    try {
        $cfg = Get-Content $configPath -Raw | ConvertFrom-Json
        if ($cfg.ai.gemini_cli_model_id) {
            $defaultModel = [string]$cfg.ai.gemini_cli_model_id
        } elseif ($cfg.web_search.gemini_cli_model) {
            $defaultModel = [string]$cfg.web_search.gemini_cli_model
        }
    } catch {}
}

if (-not $Model) {
    $Model = $defaultModel
}

# ============================================
# [2/4] FINDING GEMINI CLI EXECUTABLE
# ============================================
function Find-GeminiCli {
    $candidates = @("gemini.cmd", "gemini.exe", "gemini.ps1", "gemini")
    foreach ($c in $candidates) {
        $cmd = Get-Command $c -ErrorAction SilentlyContinue
        if ($cmd -and $cmd.Source) {
            return $cmd.Source
        }
    }

    # Standard npm global paths on Windows
    $npmPath = Join-Path $env:APPDATA "npm\gemini.cmd"
    if (Test-Path $npmPath) {
        return $npmPath
    }

    $progFilesNpm = Join-Path $env:ProgramFiles "nodejs\gemini.cmd"
    if (Test-Path $progFilesNpm) {
        return $progFilesNpm
    }

    return $null
}

function Install-GeminiCli {
    Write-Host ""
    Write-Host "📦 Installing Google Gemini CLI (@google/gemini-cli)..." -ForegroundColor Cyan
    $npmCmd = Get-Command npm -ErrorAction SilentlyContinue
    if (-not $npmCmd) {
        Write-Host "❌ Error: Package manager npm / Node.js not found in system!" -ForegroundColor Red
        Write-Host "   Gemini CLI requires installed Node.js (https://nodejs.org/)." -ForegroundColor Yellow
        $wingetCmd = Get-Command winget -ErrorAction SilentlyContinue
        if ($wingetCmd) {
            $installNode = Read-Host "   Install Node.js via winget right now? (Y/n)"
            if ($installNode.Trim().ToLower() -in @("", "y", "yes", "d", "da", "1")) {
                Write-Host "   Running winget install OpenJS.NodeJS.LTS..." -ForegroundColor Cyan
                & winget install OpenJS.NodeJS.LTS --silent --accept-package-agreements --accept-source-agreements
                Write-Host "   After Node.js installation restart terminal and run again." -ForegroundColor Yellow
            }
        }
        return $false
    }

    Write-Host "   Running: npm install -g @google/gemini-cli" -ForegroundColor DarkGray
    try {
        & npm install -g @google/gemini-cli
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Google Gemini CLI successfully installed!" -ForegroundColor Green
            return $true
        } else {
            Write-Host "❌ Error installing Gemini CLI via npm (exit code $LASTEXITCODE)." -ForegroundColor Red
            return $false
        }
    } catch {
        Write-Host "❌ Error calling npm: $_" -ForegroundColor Red
        return $false
    }
}

$cliPath = Find-GeminiCli

# ============================================
# [3/4] HANDLING SITUATION IF CLI NOT FOUND
# ============================================
if (-not $cliPath -or $Action -eq 'install') {
    if (-not $cliPath) {
        Write-Host "[WARN] Google Gemini CLI (@google/gemini-cli) not found in system!" -ForegroundColor Yellow
        Write-Host ""
        $answer = Read-Host "Want to install Google Gemini CLI now via npm? (Y/n) [Enter = Yes]"
        $answer = $answer.Trim().ToLower()
        if ($answer -in @("", "y", "yes", "d", "da", "1")) {
            $installed = Install-GeminiCli
            if ($installed) {
                $cliPath = Find-GeminiCli
            }
        } else {
            Write-Host ""
            Write-Host "Installation skipped. You can install utility manually via:" -ForegroundColor Yellow
            Write-Host "  npm install -g @google/gemini-cli" -ForegroundColor Cyan
            Write-Host ""
            exit 1
        }
    } else {
        # When explicitly called with -Action install
        $installed = Install-GeminiCli
        if ($installed) {
            $cliPath = Find-GeminiCli
        }
    }
}

if (-not $cliPath) {
    Write-Host "❌ gemini executable not found. Restart console after installation." -ForegroundColor Red
    exit 1
}

# Determine version
$versionStr = "Unknown"
try {
    $verOut = & $cliPath --version 2>$null
    if ($verOut) { $versionStr = $verOut.Trim() }
} catch {}

Write-Host "    [OK] Gemini CLI found: $cliPath" -ForegroundColor Green
Write-Host "    Version:      $versionStr" -ForegroundColor Gray
Write-Host "    Model:        $Model" -ForegroundColor Gray
if ($env:GEMINI_API_KEY) {
    Write-Host "    API Key:      Loaded from .env" -ForegroundColor Green
} else {
    Write-Host "    [WARN] API Key (GEMINI_API_KEY) not found in .env!" -ForegroundColor Yellow
}
Write-Host ""

# ============================================
# [4/4] PERFORMING ACTIONS (PROMPT / CHAT / CHECK)
# ============================================
if ($Action -eq 'version') {
    Write-Host "Gemini CLI Version: $versionStr" -ForegroundColor Green
    exit 0
}

# If direct text request passed (-Prompt)
if ($Prompt) {
    Write-Host "💬 Request: $Prompt" -ForegroundColor Cyan
    Write-Host "───────────────────────────────────────────────────────────────" -ForegroundColor DarkGray
    & $cliPath -m $Model $Prompt
    exit $LASTEXITCODE
}

# If interactive chat requested (-Action chat)
if ($Action -eq 'chat') {
    Write-Host "🚀 Launching interactive Gemini CLI dialog (Ctrl+C to exit)..." -ForegroundColor Green
    Write-Host "───────────────────────────────────────────────────────────────" -ForegroundColor DarkGray
    & $cliPath -m $Model
    exit $LASTEXITCODE
}

# Check mode (default)
Write-Host "╔═══════════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║  GEMINI CLI READY TO WORK                                     ║" -ForegroundColor Green
Write-Host "╚═══════════════════════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""
Write-Host "Commands for working:" -ForegroundColor Yellow
Write-Host "  .\Run-GeminiCli.ps1 -Action chat              # Interactive dialog"
Write-Host "  .\Run-GeminiCli.ps1 -Prompt `"Your question`"  # One-off request"
Write-Host "  .\Run-GeminiCli.ps1 -Action install           # Update package"
Write-Host ""
