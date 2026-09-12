# Скрипт для управления синхронизацией на Google Drive

param(
    [string]$Command = "help",
    [string]$Path = "",
    [int]$IntervalHours = 6
)

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$SetupScript = Join-Path $ScriptDir "scripts\setup_google_drive_sync.py"

function Show-Help {
    Write-Host @"
╔════════════════════════════════════════════════════════════════╗
║       Google Drive Synchronization Management Tool            ║
╚════════════════════════════════════════════════════════════════╝

Usage:
  .\sync.ps1 [COMMAND] [OPTIONS]

Commands:
  init              - Initialize synchronization (first time setup)
  sync              - Synchronize data now
  start             - Start automatic scheduler
  status            - Show synchronization status
  help              - Show this help message

Examples:
  # First time setup
  .\sync.ps1 init

  # Synchronize now
  .\sync.ps1 sync

  # Start automatic synchronization (background)
  .\sync.ps1 start

  # Check status
  .\sync.ps1 status

"@
}

function Initialize {
    Write-Host "🔧 Initializing Google Drive synchronization..." -ForegroundColor Cyan
    
    if (-not (Test-Path $SetupScript)) {
        Write-Host "❌ Error: Setup script not found at $SetupScript" -ForegroundColor Red
        exit 1
    }

    python "$SetupScript" --init
}

function SyncNow {
    Write-Host "⏳ Starting synchronization..." -ForegroundColor Cyan
    
    if (-not (Test-Path $SetupScript)) {
        Write-Host "❌ Error: Setup script not found at $SetupScript" -ForegroundColor Red
        exit 1
    }

    python "$SetupScript" --sync-now
}

function StartScheduler {
    Write-Host "🚀 Starting automatic synchronization scheduler..." -ForegroundColor Cyan
    Write-Host "💡 Tip: You can close this window. The scheduler will continue running." -ForegroundColor Yellow
    Write-Host ""
    
    if (-not (Test-Path $SetupScript)) {
        Write-Host "❌ Error: Setup script not found at $SetupScript" -ForegroundColor Red
        exit 1
    }

    python "$SetupScript" --start-scheduler
}

function ShowStatus {
    Write-Host "📊 Synchronization Status:" -ForegroundColor Cyan
    
    if (-not (Test-Path $SetupScript)) {
        Write-Host "❌ Error: Setup script not found at $SetupScript" -ForegroundColor Red
        exit 1
    }

    python "$SetupScript" --status
}

# Main logic
switch ($Command.ToLower()) {
    "init" { Initialize }
    "sync" { SyncNow }
    "start" { StartScheduler }
    "status" { ShowStatus }
    "help" { Show-Help }
    default { Show-Help }
}
