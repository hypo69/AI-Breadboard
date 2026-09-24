<#
.SYNOPSIS
    AI Breadboard — графический лончер сценариев.
.DESCRIPTION
    WinForms-окно с кнопками запуска основных сценариев:
    run.ps1, tc.ps1, helpdesk.ps1, admin (открывает /admin в браузере).
#>

Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

$scriptDir = $PSScriptRoot
if ([string]::IsNullOrEmpty($scriptDir)) {
    $scriptDir = (Get-Location).Path
}

# --- Helpers ---

function Invoke-Script {
    param([string]$ScriptPath, [string[]]$Args = @())
    $hasPwsh = Get-Command pwsh.exe -ErrorAction SilentlyContinue
    $shell   = if ($hasPwsh) { 'pwsh.exe' } else { 'powershell.exe' }
    $argStr  = ($Args | ForEach-Object { "`"$_`"" }) -join ' '
    Start-Process $shell -ArgumentList "-NoExit -ExecutionPolicy Bypass -File `"$ScriptPath`" $argStr" -WorkingDirectory $scriptDir
}

function Get-ServerUrl {
    $cfgPath = Join-Path $scriptDir 'config\dashboard.json'
    $proto = 'http'; $host_ = 'localhost'; $port = '8000'
    if (Test-Path $cfgPath) {
        try {
            $cfg = Get-Content $cfgPath -Raw | ConvertFrom-Json
            if ($cfg.server.protocol) { $proto = $cfg.server.protocol }
            if ($cfg.server.host -and $cfg.server.host -ne '0.0.0.0') { $host_ = $cfg.server.host }
            if ($cfg.server.port) { $port = $cfg.server.port }
        } catch {}
    }
    return "${proto}://${host_}:${port}"
}

# --- Form ---

$form = New-Object System.Windows.Forms.Form
$form.Text            = 'AI Breadboard'
$form.Size            = New-Object System.Drawing.Size(320, 280)
$form.StartPosition   = 'CenterScreen'
$form.FormBorderStyle = 'FixedSingle'
$form.MaximizeBox     = $false
$form.BackColor       = [System.Drawing.Color]::FromArgb(30, 30, 30)
$form.Font            = New-Object System.Drawing.Font('Segoe UI', 10)

# --- Title label ---

$label = New-Object System.Windows.Forms.Label
$label.Text      = 'AI Breadboard Launcher'
$label.ForeColor = [System.Drawing.Color]::FromArgb(0, 200, 255)
$label.Font      = New-Object System.Drawing.Font('Segoe UI', 11, [System.Drawing.FontStyle]::Bold)
$label.AutoSize  = $true
$label.Location  = New-Object System.Drawing.Point(70, 18)
$form.Controls.Add($label)

# --- Button factory ---

function New-LaunchButton {
    param([string]$Text, [int]$Y, [scriptblock]$OnClick)
    $btn = New-Object System.Windows.Forms.Button
    $btn.Text      = $Text
    $btn.Size      = New-Object System.Drawing.Size(260, 42)
    $btn.Location  = New-Object System.Drawing.Point(28, $Y)
    $btn.FlatStyle = 'Flat'
    $btn.FlatAppearance.BorderColor = [System.Drawing.Color]::FromArgb(0, 200, 255)
    $btn.FlatAppearance.BorderSize  = 1
    $btn.BackColor  = [System.Drawing.Color]::FromArgb(45, 45, 48)
    $btn.ForeColor  = [System.Drawing.Color]::White
    $btn.Cursor     = [System.Windows.Forms.Cursors]::Hand
    $btn.Add_Click($OnClick)
    $btn.Add_MouseEnter({ $this.BackColor = [System.Drawing.Color]::FromArgb(0, 122, 204) })
    $btn.Add_MouseLeave({ $this.BackColor = [System.Drawing.Color]::FromArgb(45, 45, 48) })
    return $btn
}

# --- Buttons ---

$btnRun = New-LaunchButton -Text '▶  Run  —  запустить FastAPI сервер' -Y 60 -OnClick {
    Invoke-Script (Join-Path $scriptDir 'Run-Dashboard.ps1')
}

$btnTc = New-LaunchButton -Text '🖥  TC  —  блок приложений (Test Computer)' -Y 112 -OnClick {
    Invoke-Script (Join-Path $scriptDir 'Run-TC.ps1')
}

$btnHelpdesk = New-LaunchButton -Text '🎫  Helpdesk  —  служба поддержки' -Y 164 -OnClick {
    Invoke-Script (Join-Path $scriptDir 'launchers\helpdesk.ps1')
}

$btnAdmin = New-LaunchButton -Text '⚙  Admin  —  открыть панель в браузере' -Y 216 -OnClick {
    $url = (Get-ServerUrl) + '/admin'
    Start-Process $url
}

$form.Controls.AddRange(@($btnRun, $btnTc, $btnHelpdesk, $btnAdmin))

[void]$form.ShowDialog()
