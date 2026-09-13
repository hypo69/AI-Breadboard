<#
.SYNOPSIS
    Wireshark and TShark installation and verification module for AI Breadboard.
.DESCRIPTION
    Checks whether tshark (part of Wireshark) is installed on the system.
    If absent, prompts user to install Wireshark via winget or provides download link.
    Also checks system PATH and verifies tshark version.
.EXAMPLE
    .\Install-Wireshark.ps1 -InstallDir $InstallDir -Config $Config
#>

param (
    [string]$InstallDir = '',
    [PSCustomObject]$Config = $null,
    [switch]$InstallLightVersion
)

$ErrorActionPreference = 'Continue'

if ($InstallLightVersion) {
    Write-Host ''
    Write-Host (Msg "step_wireshark_light_skip") -ForegroundColor Gray
    return
}

Write-Host ''
Write-Host '╔═══════════════════════════════════════════════════════════════╗' -ForegroundColor Cyan
Write-Host (Msg "step_wireshark_header") -ForegroundColor Cyan
Write-Host '╚═══════════════════════════════════════════════════════════════╝' -ForegroundColor Cyan
Write-Host ''

function Test-TSharkAvailable {
    # 1. Check system PATH
    $tsharkCmd = Get-Command 'tshark' -ErrorAction SilentlyContinue
    if ($tsharkCmd) {
        return $tsharkCmd.Source
    }

    # 2. Check standard Windows installation paths
    $commonPaths = @(
        "$env:ProgramFiles\Wireshark\tshark.exe",
        "${env:ProgramFiles(x86)}\Wireshark\tshark.exe"
    )

    foreach ($path in $commonPaths) {
        if ($path -and (Test-Path $path)) {
            return $path
        }
    }

    return $null
}

function Refresh-ProcessPath {
    $env:Path = [System.Environment]::GetEnvironmentVariable('Path', 'Machine') + ';' +
                [System.Environment]::GetEnvironmentVariable('Path', 'User')
    $wsPath = "$env:ProgramFiles\Wireshark"
    if ((Test-Path $wsPath) -and ($env:Path -notmatch [regex]::Escape($wsPath))) {
        $env:Path = "$wsPath;$env:Path"
    }
}

try {
    $existingTShark = Test-TSharkAvailable

    if ($existingTShark) {
        Write-Host (Msg "step_wireshark_already_installed" @($existingTShark)) -ForegroundColor Green
        try {
            $verOutput = & $existingTShark --version 2>&1 | Select-Object -First 1
            Write-Host "    $verOutput" -ForegroundColor Gray
        } catch {}
        return
    }

    Write-Host (Msg "step_wireshark_not_found") -ForegroundColor Yellow
    Write-Host (Msg "step_wireshark_prompt") -ForegroundColor White
    Write-Host (Msg "step_wireshark_opt_1") -ForegroundColor White
    Write-Host (Msg "step_wireshark_opt_2") -ForegroundColor Gray
    Write-Host ''

    $choice = Read-Host (Msg "step_wireshark_choice_prompt")
    $choice = $choice.Trim()
    if (-not $choice) { $choice = "1" }

    if ($choice -eq "2") {
        Write-Host (Msg "step_wireshark_skipped") -ForegroundColor Yellow
        return
    }

    $wingetCmd = Get-Command 'winget' -ErrorAction SilentlyContinue

    if ($wingetCmd) {
        Write-Host ''
        Write-Host (Msg "step_wireshark_installing_winget") -ForegroundColor Cyan
        
        & winget install --id WiresharkFoundation.Wireshark --exact --source winget --accept-source-agreements --accept-package-agreements
        
        Refresh-ProcessPath
        
        $installedTShark = Test-TSharkAvailable
        if ($installedTShark) {
            Write-Host (Msg "step_wireshark_success" @($installedTShark)) -ForegroundColor Green
            try {
                $verOutput = & $installedTShark --version 2>&1 | Select-Object -First 1
                Write-Host "    $verOutput" -ForegroundColor Gray
            } catch {}
        } else {
            Write-Host (Msg "step_wireshark_post_install_hint") -ForegroundColor Yellow
        }
    } else {
        Write-Host (Msg "step_wireshark_winget_missing") -ForegroundColor Yellow
        Write-Host "    https://www.wireshark.org/download.html" -ForegroundColor Cyan
    }
}
catch {
    Write-Host (Msg "step_wireshark_error" @($_.Exception.Message)) -ForegroundColor Red
}
