<#
.SYNOPSIS
    Universal multi-app orchestrator launcher for all /apps microservices.

.DESCRIPTION
    Starts, stops, restarts, or queries the status of all standalone microservices in /apps
    according to configuration in config_tc.json or config.json:
    - Windows System Administrator (Port 8100)
    - Network Analyzer Terminal (Port 8101)
    - System Inspector (Port 8102)
    - Exchange Trading Desk (Port 8103)
    - Cloudflare Tunnel Monitor (Port 8104)
    - Google Cloud Monitor (Port 8106)
    - Website Intelligence Monitor (Port 8107)

.PARAMETER Action
    Action to perform across all apps: 'start' (default), 'stop', 'restart', 'status'.

.PARAMETER NewWindow
    Launch all apps in visible standalone console windows.

.PARAMETER ConfigFile
    Configuration file to load app enablement from (default: config_tc.json or config.json).

.PARAMETER Help
    Display usage help for script (-Help, -h, --help).

.EXAMPLE
    .\launchers\Run-Apps.ps1
    .\launchers\Run-Apps.ps1 -NewWindow
    .\launchers\Run-Apps.ps1 -ConfigFile config_tc.json
    .\launchers\Run-Apps.ps1 -Action status
    .\launchers\Run-Apps.ps1 -Action stop
#>

[CmdletBinding()]
param (
    [ValidateSet('start', 'stop', 'restart', 'status')]
    [string]$Action = 'start',

    [Alias('Window', 'SeparateWindow')]
    [switch]$NewWindow,

    [Alias('Config', 'Cfg')]
    [string]$ConfigFile = '',

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

$projectRoot = $scriptDir
if ((Split-Path -Leaf $projectRoot) -eq "launchers" -or -not (Test-Path (Join-Path $projectRoot "main.py"))) {
    $parent = Split-Path -Parent $projectRoot
    if (Test-Path (Join-Path $parent "main.py")) {
        $projectRoot = $parent
    }
}
$env:AIBREADBOARD_DIR = $projectRoot
$env:ASSIST_DIR = $projectRoot

if ($Help) {
    Write-Host ""
    Write-Host "╔═══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "║           Run-Apps.ps1 — ALL APPS ORCHESTRATOR                ║" -ForegroundColor Cyan
    Write-Host "╚═══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "PURPOSE:" -ForegroundColor Yellow
    Write-Host "  Manage and launch all standalone microservices in /apps."
    Write-Host ""
    Write-Host "SYNTAX:" -ForegroundColor Yellow
    Write-Host "  .\launchers\Run-Apps.ps1 [-Action start|stop|restart|status] [-NewWindow] [-ConfigFile <file.json>]"
    Write-Host "  .\launchers\Run-Apps.ps1 --help"
    Write-Host ""
    exit 0
}

Write-Host ""
Write-Host "╔═══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║              AI BREADBOARD — /apps MICROSERVICES              ║" -ForegroundColor Cyan
Write-Host "╚═══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# Resolve configuration file
$activeCfgFile = "config.json"
if ($ConfigFile -and (Test-Path (Join-Path $projectRoot $ConfigFile))) {
    $activeCfgFile = $ConfigFile
} elseif (Test-Path (Join-Path $projectRoot "config.json")) {
    $activeCfgFile = "config.json"
} elseif (Test-Path (Join-Path $projectRoot "config_ts.json")) {
    $activeCfgFile = "config_ts.json"
} elseif (Test-Path (Join-Path $projectRoot "config_tc.json")) {
    $activeCfgFile = "config_tc.json"
}

$activeCfgPath = Join-Path $projectRoot $activeCfgFile
$cfgObj = $null
if (Test-Path $activeCfgPath) {
    try {
        $cfgObj = Get-Content $activeCfgPath -Raw -Encoding UTF8 | ConvertFrom-Json
        Write-Host "  [CONFIG] Using configuration: $activeCfgFile" -ForegroundColor DarkGray
    } catch {
        Write-Host "  [WARN] Failed to parse $activeCfgFile : $_" -ForegroundColor Yellow
    }
}

function Get-AppServerMode {
    param (
        [string]$AppName,
        [string]$BaseDir = $projectRoot
    )
    $candidatePaths = @(
        (Join-Path $BaseDir "src\apps\$AppName\config.json"),
        (Join-Path $BaseDir "apps\$AppName\config.json")
    )
    foreach ($path in $candidatePaths) {
        if (Test-Path $path) {
            try {
                $raw = Get-Content $path -Raw -Encoding UTF8 | ConvertFrom-Json
                if ($raw.server) {
                    if ($raw.server.PSObject.Properties['dedicated'] -ne $null) {
                        if ($raw.server.dedicated -eq $true -or $raw.server.dedicated -eq 'true') {
                            return "dedicated"
                        } else {
                            return "shared"
                        }
                    }
                    if ($raw.server -is [string]) {
                        return $raw.server.Trim().ToLower()
                    }
                    if ($raw.server.mode) {
                        return $raw.server.mode.ToString().Trim().ToLower()
                    }
                    if ($raw.server.type) {
                        return $raw.server.type.ToString().Trim().ToLower()
                    }
                }
            } catch {
                # Fallback to dedicated
            }
        }
    }
    return "dedicated"
}

$appScripts = @(
    @{ Name = "Windows System Administrator"; Folder = "windows_sysadmin";    File = "Run-WindowsAdmin.ps1";        Port = 8100; Key = "windows_sysadmin" },
    @{ Name = "Network Analyzer Terminal";    Folder = "network_terminal";    File = "Run-NetworkTerminal.ps1";     Port = 8101; Key = "network_terminal" },
    @{ Name = "System Inspector";             Folder = "system_inspector";    File = "Run-SystemInspector.ps1";     Port = 8102; Key = "system_inspector" },
    @{ Name = "Exchange Trading Terminal";    Folder = "trading_terminal";    File = "Run-TradingTerminal.ps1";     Port = 8103; Key = "trading_terminal" },
    @{ Name = "Cloudflared Monitor";          Folder = "cloudflared_monitor"; File = "Run-CloudflaredMonitor.ps1"; Port = 8104; Key = "cloudflared_monitor" },
    @{ Name = "User Assistant";               Folder = "user_assistant";      File = "Run-UserAssistant.ps1";       Port = 8105; Key = "user_assistant" },
    @{ Name = "Google Cloud Monitor";         Folder = "gcloud_monitor";      File = "Run-GCloudMonitor.ps1";       Port = 8106; Key = "gcloud_monitor" },
    @{ Name = "Website Intelligence Monitor"; Folder = "website_monitor";     File = "Run-WebsiteMonitor.ps1";      Port = 8107; Key = "website_monitor" },
    @{ Name = "System Control Center";        Folder = "system_control_center"; File = "Run-SystemControlCenter.ps1"; Port = 8109; Key = "system_control_center" },
    @{ Name = "Wikipedia Research Lab";       Folder = "wikipedia_research";   File = "Run-WikipediaResearch.ps1";  Port = 8110; Key = "wikipedia_research" },
    @{ Name = "AI Breadboard Admin";          Folder = "ai_breadboard_admin";  File = "Run-Admin.ps1";              Port = 8110; Key = "ai_breadboard_admin" },
    @{ Name = "Research & Statistics";        Folder = "research_and_statistic"; File = "Run-ResearchStatistic.ps1"; Port = 8111; Key = "research_and_statistic" },
    @{ Name = "Software Audit";               Folder = "software_audit";      File = "Run-SoftwareAudit.ps1";      Port = 8113; Key = "software_audit" },
    @{ Name = "Registry Viewer";              Folder = "registry_viewer";     File = "Run-RegistryViewer.ps1";     Port = 8114; Key = "registry_viewer" },
    @{ Name = "Windows Startup Auditor";      Folder = "windows_startup_auditor"; File = "Run-StartupAuditor.ps1"; Port = 8112; Key = "windows_startup_auditor" },
    @{ Name = "Windows Defender Center";      Folder = "windows_defender";    File = "Run-Defender.ps1";           Port = 8113; Key = "windows_defender" },
    @{ Name = "Windows Backup Manager";       Folder = "windows_backup_manager"; File = "Run-BackupManager.ps1";   Port = 8115; Key = "windows_backup_manager" },
    @{ Name = "Hardware & Sensors Monitor";   Folder = "windows";             File = "Run-HardwareMonitor.ps1";    Port = 8116; Key = "hardware_monitor" },
    @{ Name = "AIDA64 Diagnostic App";        Folder = "aida64";              File = "Run-Aida64.ps1";             Port = 8120; Key = "aida64" },
    @{ Name = "HWiNFO Diagnostic App";        Folder = "hwinfo";              File = "Run-Hwinfo.ps1";             Port = 8121; Key = "hwinfo" },
    @{ Name = "CPU-Z Processor App";          Folder = "cpuz";                File = "Run-Cpuz.ps1";               Port = 8122; Key = "cpuz" },
    @{ Name = "GPU-Z Graphics App";           Folder = "gpuz";                File = "Run-Gpuz.ps1";               Port = 8123; Key = "gpuz" },
    @{ Name = "smartmontools Storage App";    Folder = "smartmontools";       File = "Run-Smartmontools.ps1";      Port = 8124; Key = "smartmontools" },
    @{ Name = "LibreHardwareMonitor App";     Folder = "librehardwaremonitor"; File = "Run-LHM.ps1";               Port = 8126; Key = "librehardwaremonitor" }
)

$isAppsArray = ($cfgObj -and $cfgObj.apps -and ($cfgObj.apps -is [System.Collections.IEnumerable]) -and ($cfgObj.apps -isnot [string]) -and ($cfgObj.apps.PSObject.Properties['enable_all'] -eq $null) -and ($cfgObj.apps.PSObject.Properties['enabled'] -eq $null))

$hasEnabledList = ($cfgObj -and $cfgObj.apps -and $cfgObj.apps.PSObject.Properties['enabled'] -ne $null -and ($cfgObj.apps.enabled -is [System.Collections.IEnumerable]))
$hasDisabledList = ($cfgObj -and $cfgObj.apps -and $cfgObj.apps.PSObject.Properties['disabled'] -ne $null -and ($cfgObj.apps.disabled -is [System.Collections.IEnumerable]))

$enabledAppsList = @()
$disabledAppsList = @()

if ($isAppsArray) {
    foreach ($item in $cfgObj.apps) {
        if ($item) { $enabledAppsList += $item.ToString().Trim().ToLower() }
    }
} elseif ($hasEnabledList) {
    foreach ($item in $cfgObj.apps.enabled) {
        if ($item) { $enabledAppsList += $item.ToString().Trim().ToLower() }
    }
}

if ($hasDisabledList) {
    foreach ($item in $cfgObj.apps.disabled) {
        if ($item) { $disabledAppsList += $item.ToString().Trim().ToLower() }
    }
}

$enableAll = $true
if ($isAppsArray -or $hasEnabledList) {
    $enableAll = $false
} elseif ($cfgObj -and $cfgObj.apps -and $cfgObj.apps.PSObject.Properties['enable_all'] -ne $null) {
    $enableAll = [bool]$cfgObj.apps.enable_all
}

foreach ($app in $appScripts) {
    $aliases = @(
        $app.Folder.ToLower(),
        $app.Key.ToLower(),
        $app.Folder.Replace('_', '').ToLower(),
        $app.Folder.Replace('_sysadmin', '_admin').ToLower(),
        $app.Folder.Replace('_center', '').ToLower(),
        $app.Folder.Replace('_viewer', '').ToLower(),
        $app.Folder.Replace('_viewer', 's').ToLower()
    )
    if ($app.Folder -eq "windows_sysadmin") { $aliases += @("windows_admin", "windowsadmin", "sysadmin", "tab-windows-admin") }
    if ($app.Folder -eq "system_control_center") { $aliases += @("system_control", "control_center", "tab-system-control") }
    if ($app.Folder -eq "trading_terminal") { $aliases += @("trading", "tab-trading") }
    if ($app.Folder -eq "network_terminal") { $aliases += @("network", "tab-network-terminal") }
    if ($app.Folder -eq "system_inspector") { $aliases += @("inspector", "tab-system-inspector") }
    if ($app.Folder -eq "cloudflared_monitor") { $aliases += @("cloudflared", "tab-cloudflared") }
    if ($app.Folder -eq "gcloud_monitor") { $aliases += @("gcloud", "google_cloud", "tab-gcloud") }
    if ($app.Folder -eq "website_monitor") { $aliases += @("website", "website_intelligence", "tab-website-monitor") }
    if ($app.Folder -eq "user_assistant") { $aliases += @("assistant", "userassistant", "tab-user-assistant") }
    if ($app.Folder -eq "wikipedia_research") { $aliases += @("wikipedia", "wiki_lab", "tab-wikipedia-research") }
    if ($app.Folder -eq "software_audit") { $aliases += @("software", "audit_software", "installed_software", "tab-software-audit") }
    if ($app.Folder -eq "registry_viewer") { $aliases += @("registry", "regedit", "reg_viewer", "tab-registry-viewer") }
    if ($app.Folder -eq "windows_startup_auditor") { $aliases += @("startup_auditor", "startup", "autoruns", "tab-startup-auditor") }
    if ($app.Folder -eq "windows_backup_manager") { $aliases += @("backup_manager", "windows_backup", "backup", "tab-windows-backup") }
    if ($app.Key -eq "hardware_monitor") { $aliases += @("hardware", "sensors", "hw_monitor", "tab-hardware-monitor") }

    $isExplicitlyDisabled = $false
    foreach ($al in $aliases) {
        if ($disabledAppsList -contains $al) {
            $isExplicitlyDisabled = $true
            break
        }
    }

    if ($isExplicitlyDisabled) {
        $isAppEnabled = $false
    } elseif ($isAppsArray -or $hasEnabledList) {
        $matched = $false
        foreach ($al in $aliases) {
            if ($enabledAppsList -contains $al) {
                $matched = $true
                break
            }
        }
        $isAppEnabled = $matched
    } elseif ($cfgObj -and $cfgObj.apps -and $cfgObj.apps.PSObject.Properties[$app.Key] -ne $null) {
        $isAppEnabled = [bool]$cfgObj.apps.($app.Key)
    } elseif ($cfgObj -and $cfgObj.apps -and $cfgObj.apps.PSObject.Properties[$app.Folder] -ne $null) {
        $isAppEnabled = [bool]$cfgObj.apps.($app.Folder)
    } else {
        $isAppEnabled = $enableAll
    }

    if (-not $isAppEnabled) {
        Write-Host "⏸ $($app.Name) (Port: $($app.Port))... [DISABLED in $activeCfgFile]" -ForegroundColor DarkGray
        continue
    }

    $serverMode = Get-AppServerMode $app.Folder
    if ($serverMode -ne "dedicated") {
        Write-Host "▶ $($app.Name) (Port: $($app.Port))... [SHARED MODE — routed via main server]" -ForegroundColor DarkCyan
        continue
    }

    $launcherPath = Join-Path $projectRoot "launchers\$($app.File)"
    if (-not (Test-Path $launcherPath)) {
        $launcherPath = Join-Path $projectRoot $app.File
    }

    if (Test-Path $launcherPath) {
        Write-Host "▶ $($app.Name) (Port: $($app.Port))..." -ForegroundColor Cyan
        $callArgs = @{ Action = $Action }
        if ($NewWindow -and $Action -in @('start', 'restart')) {
            $callArgs['NewWindow'] = $true
        }
        & $launcherPath @callArgs
    } else {
        Write-Host "  [WARN] Launcher script not found: $launcherPath" -ForegroundColor Yellow
    }
}
Write-Host ""
