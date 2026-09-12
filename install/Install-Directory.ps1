<#
.SYNOPSIS
    Модуль выбора и подготовки целевой директории установки AI Breadboard.
.DESCRIPTION
    Определяет стандартное предпочтительное расположение (%LOCALAPPDATA%\AI Breadboard),
    выводит мультиязычное разъяснение о стабильности стандартного пути при активной разработке,
    запрашивает подтверждение/путь у пользователя, создает директорию и при необходимости
    развертывает файлы репозитория через Git или скачивание архива ZIP.
#>

param (
    [PSCustomObject]$Config,
    [string]$SourceDir = ""
)

Write-Host (Msg "dir_step_title") -ForegroundColor Cyan
Write-Host ''

$defaultInstallDir = if ($SourceDir -and (Test-Path (Join-Path $SourceDir "header.py"))) {
    $SourceDir
} elseif ($Config -and $Config.defaults -and $Config.defaults.install_dir) {
    [System.Environment]::ExpandEnvironmentVariables($Config.defaults.install_dir)
} elseif ($env:LOCALAPPDATA) {
    Join-Path $env:LOCALAPPDATA 'AI Breadboard'
} else {
    Join-Path $env:USERPROFILE 'AppData\Local\AI Breadboard'
}

Write-Host "┌─────────────────────────────────────────────────────────────┐" -ForegroundColor Yellow
Write-Host (Msg "dir_notice_header") -ForegroundColor Yellow
Write-Host (Msg "dir_stability_warn") -ForegroundColor White
Write-Host "└─────────────────────────────────────────────────────────────┘" -ForegroundColor Yellow
Write-Host ""
Write-Host (Msg "dir_opt_default" @($defaultInstallDir)) -ForegroundColor Green
Write-Host (Msg "dir_opt_custom") -ForegroundColor White
Write-Host ""

$dirChoice = Read-Host (Msg "dir_choice_prompt")
$dirChoice = $dirChoice.Trim()

$targetDir = $defaultInstallDir
if ($dirChoice -eq '2') {
    Write-Host ""
    $customInput = Read-Host (Msg "dir_enter_custom")
    $customInput = $customInput.Trim().Trim('"').Trim("'")
    if ($customInput) {
        $expanded = [System.Environment]::ExpandEnvironmentVariables($customInput)
        $targetDir = [System.IO.Path]::GetFullPath($expanded)
    }
}

Write-Host ""
Write-Host (Msg "dir_selected" @($targetDir)) -ForegroundColor Green
Write-Host ""

if (-not (Test-Path $targetDir)) {
    New-Item -ItemType Directory -Force -Path $targetDir | Out-Null
}

$needsFetch = (-not (Test-Path (Join-Path $targetDir "header.py"))) -or (-not (Test-Path (Join-Path $targetDir "config.json")))

if ($needsFetch) {
    if ($SourceDir -and (Test-Path (Join-Path $SourceDir "header.py")) -and ($SourceDir -ne $targetDir)) {
        Write-Host (Msg "repo_downloading" @($targetDir)) -ForegroundColor Cyan
        Copy-Item -Path "$SourceDir\*" -Destination $targetDir -Recurse -Force
    } else {
        Write-Host (Msg "repo_downloading" @($targetDir)) -ForegroundColor Cyan
        $gitCmd = Get-Command git -ErrorAction SilentlyContinue
        $cloneSuccess = $false
        $repoUrl = "https://github.com/hypo69/AI-Breadboard.git"
        if ($Config -and $Config.defaults -and $Config.defaults.repo_url) {
            $repoUrl = $Config.defaults.repo_url
        }

        if ($gitCmd) {
            Write-Host (Msg "repo_git_clone") -ForegroundColor Gray
            try {
                & git clone $repoUrl $targetDir
                if ($LASTEXITCODE -eq 0) { $cloneSuccess = $true }
            } catch {}
        }
        
        if (-not $cloneSuccess) {
            Write-Host (Msg "repo_zip_download") -ForegroundColor Yellow
            $zipUrl = "https://github.com/hypo69/AI-Breadboard/archive/refs/heads/master.zip"
            if ($Config -and $Config.defaults -and $Config.defaults.repo_zip_url) {
                $zipUrl = $Config.defaults.repo_zip_url
            }
            $tempZip = Join-Path $env:TEMP "aibreadboard_master.zip"
            $tempExtract = Join-Path $env:TEMP "aibreadboard_extract_$([System.Guid]::NewGuid().ToString('N'))"
            
            [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12 -bor [Net.SecurityProtocolType]::Tls13
            Invoke-WebRequest -Uri $zipUrl -OutFile $tempZip -UseBasicParsing
            
            Write-Host (Msg "repo_unzipping") -ForegroundColor Gray
            Expand-Archive -Path $tempZip -DestinationPath $tempExtract -Force
            
            $extractedRoot = Get-ChildItem -Path $tempExtract -Directory | Select-Object -First 1
            if ($extractedRoot) {
                Copy-Item -Path "$($extractedRoot.FullName)\*" -Destination $targetDir -Recurse -Force
            }
            
            Remove-Item -Path $tempZip -Force -ErrorAction SilentlyContinue
            Remove-Item -Path $tempExtract -Recurse -Force -ErrorAction SilentlyContinue
        }
    }
    Write-Host (Msg "repo_ready" @($targetDir)) -ForegroundColor Green
    Write-Host ""
}

return $targetDir
