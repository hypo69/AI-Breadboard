<#
.SYNOPSIS
    System tray companion and window visibility manager for AI Breadboard.

.DESCRIPTION
    Provides Windows System Tray integration for console and application windows.
    Enables minimizing or hiding active console windows into the system tray,
    intercepting accidental window closure, and controlling application lifecycle
    via an interactive tray icon and context menu. Automatically loads brand
    icons from webinterface assets (favicon.ico / icon48.png / icon256.png).

.PARAMETER Action
    Operation to perform: 'start' (init tray icon and hooks), 'hide', 'show', 'toggle', 'stop', 'status'.
    Default: 'start'.

.PARAMETER WebUrl
    Target URL opened when selecting 'Open Web UI' from tray menu.
    Default: 'http://localhost:8000/admin'.

.PARAMETER Title
    Tooltip and notification title for system tray icon.
    Default: 'AI Breadboard'.

.PARAMETER IconPath
    Optional path to custom icon (.ico or .png). If not specified, automatically
    discovered from webinterface assets.

.PARAMETER HideNow
    Immediately hide the console window upon initialization.

.PARAMETER DisableCloseButton
    Disable the console system menu close button ([X]) to prevent accidental process termination.

.PARAMETER Help
    Display usage help for script (-Help, -h, --help).

.EXAMPLE
    .\launchers\ShowHide-InTray.ps1
    .\launchers\ShowHide-InTray.ps1 -Action hide
    .\launchers\ShowHide-InTray.ps1 -Action show
    .\launchers\ShowHide-InTray.ps1 -WebUrl "http://localhost:8000/admin" -DisableCloseButton
    .\ShowHide-InTray.ps1 --help
#>

[CmdletBinding()]
param (
    [ValidateSet('start', 'hide', 'show', 'toggle', 'stop', 'status')]
    [string]$Action = 'start',

    [Alias('Url')]
    [string]$WebUrl = 'http://localhost:8000/admin',

    [string]$Title = 'AI Breadboard',

    [Alias('Icon')]
    [string]$IconPath = '',

    [Alias('Hide')]
    [switch]$HideNow,

    [Alias('ProtectClose', 'NoClose')]
    [switch]$DisableCloseButton,

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
    Write-Host "║        ShowHide-InTray.ps1 — SYSTEM TRAY COMPANION            ║" -ForegroundColor Cyan
    Write-Host "╚═══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "PURPOSE:" -ForegroundColor Yellow
    Write-Host "  Hides and manages AI Breadboard console window in Windows System Tray."
    Write-Host ""
    Write-Host "SYNTAX:" -ForegroundColor Yellow
    Write-Host "  .\launchers\ShowHide-InTray.ps1 [-Action <start|hide|show|toggle|stop>] [-WebUrl <url>] [-IconPath <path>] [-HideNow] [-DisableCloseButton]"
    Write-Host "  .\launchers\ShowHide-InTray.ps1 --help"
    Write-Host ""
    Write-Host "ACTIONS:" -ForegroundColor Yellow
    Write-Host "  start   Initialize System Tray icon and message loop (default)"
    Write-Host "  hide    Hide the active console window into tray"
    Write-Host "  show    Restore the console window to desktop"
    Write-Host "  toggle  Toggle visibility between hidden and shown"
    Write-Host "  stop    Dispose tray icon and exit"
    Write-Host "  status  Check current window visibility state"
    Write-Host ""
    exit 0
}

# ============================================================================
# RESOLVE APPLICATION ASSETS ICON
# ============================================================================
if ([string]::IsNullOrWhiteSpace($IconPath) -or -not (Test-Path $IconPath)) {
    $candidatePaths = @(
        (Join-Path $projectRoot "src\fastapi\webinterface\assets\favicon.ico"),
        (Join-Path $projectRoot "src\fastapi\webinterface\favicon.ico"),
        (Join-Path $projectRoot "src\fastapi\webinterface\icons\icon48.png"),
        (Join-Path $projectRoot "src\fastapi\webinterface\icons\icon16.png"),
        (Join-Path $projectRoot "src\fastapi\webinterface\assets\icon256.png"),
        (Join-Path $projectRoot "src\fastapi\webinterface\icons\icon128.png")
    )
    foreach ($cand in $candidatePaths) {
        if (Test-Path $cand) {
            $IconPath = $cand
            break
        }
    }
}

# ============================================================================
# WIN32 API REGISTRATION
# ============================================================================
Add-Type -AssemblyName System.Windows.Forms -ErrorAction SilentlyContinue
Add-Type -AssemblyName System.Drawing -ErrorAction SilentlyContinue

if (-not ([System.Management.Automation.PSTypeName]'AIBreadboard.TrayWin32').Type) {
    try {
        Add-Type -MemberDefinition @"
            [DllImport("kernel32.dll")]
            public static extern IntPtr GetConsoleWindow();

            [DllImport("user32.dll")]
            public static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);

            [DllImport("user32.dll")]
            public static extern bool IsWindowVisible(IntPtr hWnd);

            [DllImport("user32.dll")]
            public static extern bool SetForegroundWindow(IntPtr hWnd);

            [DllImport("user32.dll")]
            public static extern IntPtr GetSystemMenu(IntPtr hWnd, bool bRevert);

            [DllImport("user32.dll")]
            public static extern bool DeleteMenu(IntPtr hMenu, uint uPosition, uint uFlags);

            [DllImport("user32.dll")]
            public static extern bool EnableMenuItem(IntPtr hMenu, uint uIDEnableItem, uint uEnable);

            [DllImport("user32.dll")]
            public static extern IntPtr SendMessage(IntPtr hWnd, uint Msg, IntPtr wParam, IntPtr lParam);
"@ -Name "TrayWin32" -Namespace "AIBreadboard" -ErrorAction SilentlyContinue
    } catch {
        # Type already loaded in current session
    }
}

$SW_HIDE = 0
$SW_SHOW = 5
$SW_RESTORE = 9
$SC_CLOSE = 0xF060
$MF_BYCOMMAND = 0x00000000
$MF_GRAYED = 0x00000001
$MF_DISABLED = 0x00000002
$WM_SETICON = 0x0080
$ICON_SMALL = 0
$ICON_BIG = 1

$hwnd = [AIBreadboard.TrayWin32]::GetConsoleWindow()

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================
function Hide-ConsoleWindow {
    param([IntPtr]$TargetHwnd = $hwnd)
    if ($TargetHwnd -ne [IntPtr]::Zero) {
        [AIBreadboard.TrayWin32]::ShowWindow($TargetHwnd, $SW_HIDE) | Out-Null
        $global:AIBreadboard_WindowHidden = $true
    }
}

function Show-ConsoleWindow {
    param([IntPtr]$TargetHwnd = $hwnd)
    if ($TargetHwnd -ne [IntPtr]::Zero) {
        [AIBreadboard.TrayWin32]::ShowWindow($TargetHwnd, $SW_RESTORE) | Out-Null
        [AIBreadboard.TrayWin32]::SetForegroundWindow($TargetHwnd) | Out-Null
        $global:AIBreadboard_WindowHidden = $false
    }
}

function Toggle-ConsoleWindow {
    param([IntPtr]$TargetHwnd = $hwnd)
    if ($TargetHwnd -ne [IntPtr]::Zero) {
        $isVisible = [AIBreadboard.TrayWin32]::IsWindowVisible($TargetHwnd)
        if ($isVisible) {
            Hide-ConsoleWindow -TargetHwnd $TargetHwnd
        } else {
            Show-ConsoleWindow -TargetHwnd $TargetHwnd
        }
    }
}

function Disable-ConsoleCloseButton {
    param([IntPtr]$TargetHwnd = $hwnd)
    if ($TargetHwnd -ne [IntPtr]::Zero) {
        $hMenu = [AIBreadboard.TrayWin32]::GetSystemMenu($TargetHwnd, $false)
        if ($hMenu -ne [IntPtr]::Zero) {
            [AIBreadboard.TrayWin32]::EnableMenuItem($hMenu, $SC_CLOSE, ($MF_BYCOMMAND -bor $MF_GRAYED -bor $MF_DISABLED)) | Out-Null
        }
    }
}

# Handle direct commands
if ($Action -eq 'hide') {
    Hide-ConsoleWindow
    exit 0
}

if ($Action -eq 'show') {
    Show-ConsoleWindow
    exit 0
}

if ($Action -eq 'toggle') {
    Toggle-ConsoleWindow
    exit 0
}

if ($Action -eq 'status') {
    $isVisible = if ($hwnd -ne [IntPtr]::Zero) { [AIBreadboard.TrayWin32]::IsWindowVisible($hwnd) } else { $false }
    Write-Host "Console Window HWND: $hwnd | Visible: $isVisible" -ForegroundColor Cyan
    exit 0
}

if ($Action -eq 'stop') {
    if ($global:AIBreadboard_TrayRunspace) {
        try {
            $global:AIBreadboard_TrayRunspace.Close()
            $global:AIBreadboard_TrayRunspace.Dispose()
        } catch {}
    }
    Show-ConsoleWindow
    exit 0
}

# ============================================================================
# START TRAY INTEGRATION (STA BACKGROUND RUNSPACE)
# ============================================================================
if ($DisableCloseButton) {
    Disable-ConsoleCloseButton -TargetHwnd $hwnd
}

if ($HideNow) {
    Hide-ConsoleWindow -TargetHwnd $hwnd
}

# Initialize STA Runspace for Windows Forms Application.Run loop
$runspace = [runspacefactory]::CreateRunspace()
$runspace.ApartmentState = [System.Threading.ApartmentState]::STA
$runspace.Open()

# Share variables with runspace
$runspace.SessionStateProxy.SetVariable("SharedHwnd", $hwnd)
$runspace.SessionStateProxy.SetVariable("SharedTitle", $Title)
$runspace.SessionStateProxy.SetVariable("SharedUrl", $WebUrl)
$runspace.SessionStateProxy.SetVariable("SharedIconPath", $IconPath)
$runspace.SessionStateProxy.SetVariable("SharedProjectRoot", $projectRoot)
$runspace.SessionStateProxy.SetVariable("SharedPid", $PID)

$ps = [powershell]::Create()
$ps.Runspace = $runspace

$trayScriptBlock = {
    Add-Type -AssemblyName System.Windows.Forms
    Add-Type -AssemblyName System.Drawing

    if (-not ([System.Management.Automation.PSTypeName]'AIBreadboard.TrayWin32').Type) {
        try {
            Add-Type -MemberDefinition @"
                [DllImport("user32.dll")]
                public static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);
                [DllImport("user32.dll")]
                public static extern bool IsWindowVisible(IntPtr hWnd);
                [DllImport("user32.dll")]
                public static extern bool SetForegroundWindow(IntPtr hWnd);
                [DllImport("user32.dll")]
                public static extern IntPtr SendMessage(IntPtr hWnd, uint Msg, IntPtr wParam, IntPtr lParam);
"@ -Name "TrayWin32" -Namespace "AIBreadboard" -ErrorAction SilentlyContinue
        } catch {}
    }

    $notifyIcon = New-Object System.Windows.Forms.NotifyIcon
    $loadedIcon = $null

    # Load custom icon from web assets or fallback to default application icon
    if ($SharedIconPath -and (Test-Path $SharedIconPath)) {
        try {
            if ($SharedIconPath.EndsWith(".ico", [System.StringComparison]::OrdinalIgnoreCase)) {
                $loadedIcon = [System.Drawing.Icon]::new($SharedIconPath, 32, 32)
            } else {
                # Load PNG and create HIcon
                $bmp = [System.Drawing.Bitmap]::FromFile($SharedIconPath)
                $hIcon = $bmp.GetHicon()
                $loadedIcon = [System.Drawing.Icon]::FromHandle($hIcon)
            }
        } catch {
            $loadedIcon = $null
        }
    }

    if ($null -eq $loadedIcon) {
        $loadedIcon = [System.Drawing.SystemIcons]::Application
    }

    $notifyIcon.Icon = $loadedIcon
    $notifyIcon.Text = if ($SharedTitle.Length -gt 63) { $SharedTitle.Substring(0, 60) + "..." } else { $SharedTitle }
    $notifyIcon.Visible = $true

    # Optionally set console window titlebar icon
    if ($SharedHwnd -ne [IntPtr]::Zero -and $loadedIcon -ne $null) {
        try {
            [AIBreadboard.TrayWin32]::SendMessage($SharedHwnd, 0x0080, [IntPtr]0, $loadedIcon.Handle) | Out-Null # ICON_SMALL
            [AIBreadboard.TrayWin32]::SendMessage($SharedHwnd, 0x0080, [IntPtr]1, $loadedIcon.Handle) | Out-Null # ICON_BIG
        } catch {}
    }

    $openOrRestoreAppWindow = {
        $appDataDir = $env:APPDATA
        if (-not $appDataDir) {
            $appDataDir = Join-Path $env:USERPROFILE "AppData\Roaming"
        }
        $profileDir = Join-Path $appDataDir "AI-Breadboard\browser_profile"

        $restored = $false
        try {
            $edgeProcs = Get-CimInstance Win32_Process -Filter "Name = 'msedge.exe'" -ErrorAction SilentlyContinue |
                Where-Object { $_.CommandLine -and ($_.CommandLine -like "*$profileDir*" -or $_.CommandLine -like "*browser_profile*") }

            if ($edgeProcs) {
                foreach ($proc in $edgeProcs) {
                    $p = Get-Process -Id $proc.ProcessId -ErrorAction SilentlyContinue
                    if ($p -and $p.MainWindowHandle -ne [IntPtr]::Zero) {
                        [AIBreadboard.TrayWin32]::ShowWindow($p.MainWindowHandle, 9) | Out-Null # SW_RESTORE
                        [AIBreadboard.TrayWin32]::SetForegroundWindow($p.MainWindowHandle) | Out-Null
                        $restored = $true
                        break
                    }
                }
            }
        } catch {}

        if (-not $restored) {
            $edgePaths = @(
                "${env:ProgramFiles(x86)}\Microsoft\Edge\Application\msedge.exe",
                "${env:ProgramFiles}\Microsoft\Edge\Application\msedge.exe",
                "${env:LocalAppData}\Microsoft\Edge\Application\msedge.exe",
                "${env:ProgramFiles}\Google\Chrome\Application\chrome.exe",
                "${env:ProgramFiles(x86)}\Google\Chrome\Application\chrome.exe",
                "${env:LocalAppData}\Google\Chrome\Application\chrome.exe"
            )
            $edgeExe = $edgePaths | Where-Object { Test-Path $_ } | Select-Object -First 1
            if ($edgeExe) {
                $edgeArgs = @(
                    "--app=$SharedUrl",
                    "--user-data-dir=`"$profileDir`"",
                    "--start-maximized"
                )
                Start-Process -FilePath $edgeExe -ArgumentList ($edgeArgs -join " ") -WindowStyle Maximized
            } else {
                try {
                    [System.Diagnostics.Process]::Start((New-Object System.Diagnostics.ProcessStartInfo($SharedUrl) -Property @{ UseShellExecute = $true })) | Out-Null
                } catch {}
            }
        }
    }

    $contextMenu = New-Object System.Windows.Forms.ContextMenuStrip

    # Menu items
    $itemWeb = $contextMenu.Items.Add("🌐 Open App Window")
    $itemWeb.Font = New-Object System.Drawing.Font($itemWeb.Font, [System.Drawing.FontStyle]::Bold)
    $itemToggle = $contextMenu.Items.Add("💻 Show / Hide Console")
    $contextMenu.Items.Add("-") | Out-Null
    $itemAssist = $contextMenu.Items.Add("🤖 Launch Assist CLI")
    $contextMenu.Items.Add("-") | Out-Null
    $itemExit = $contextMenu.Items.Add("❌ Stop Server and Exit")

    # Handlers
    $itemWeb.Add_Click({
        & $openOrRestoreAppWindow
    })

    $itemToggle.Add_Click({
        if ($SharedHwnd -ne [IntPtr]::Zero) {
            $visible = [AIBreadboard.TrayWin32]::IsWindowVisible($SharedHwnd)
            if ($visible) {
                [AIBreadboard.TrayWin32]::ShowWindow($SharedHwnd, 0) | Out-Null # SW_HIDE
                $notifyIcon.ShowBalloonTip(2000, $SharedTitle, "Server is running in system tray.", [System.Windows.Forms.ToolTipIcon]::Info)
            } else {
                [AIBreadboard.TrayWin32]::ShowWindow($SharedHwnd, 9) | Out-Null # SW_RESTORE
                [AIBreadboard.TrayWin32]::SetForegroundWindow($SharedHwnd) | Out-Null
            }
        }
    })

    $notifyIcon.Add_DoubleClick({
        & $openOrRestoreAppWindow
    })

    $itemAssist.Add_Click({
        $assistFile = Join-Path $SharedProjectRoot "assist.ps1"
        if (Test-Path $assistFile) {
            Start-Process powershell.exe -ArgumentList "-NoExit -ExecutionPolicy Bypass -File `"$assistFile`"" -WorkingDirectory $SharedProjectRoot
        }
    })

    $itemExit.Add_Click({
        $notifyIcon.Visible = $false
        $notifyIcon.Dispose()
        if ($SharedPid -gt 0) {
            Stop-Process -Id $SharedPid -Force -ErrorAction SilentlyContinue
        }
        [System.Windows.Forms.Application]::Exit()
    })

    $notifyIcon.ContextMenuStrip = $contextMenu

    [System.Windows.Forms.Application]::Run()
}

$ps.AddScript($trayScriptBlock) | Out-Null
$asyncResult = $ps.BeginInvoke()

# Store handles globally in PowerShell session
$global:AIBreadboard_TrayRunspace = $runspace
$global:AIBreadboard_TrayAsync = $asyncResult

$iconHint = if ($IconPath) { (Split-Path -Leaf $IconPath) } else { "Default" }
Write-Host "    [OK] System tray icon initialized ($Title | Icon: $iconHint)" -ForegroundColor Green
