<#
=============================================================================
Process Name: AI-Breadboard Automation - Launcher
=============================================================================
Description:
  AI Breadboard — графический лончер сценариев и сервисов

Usage Examples:
  PowerShell Execution:
    .\launcher.ps1

File: launcher.ps1
Project: ai-breadboard
Package: root
Author: hypo69
Copyright: © 2026 hypo69
Updated: 2026-10-02 21:57:05
=============================================================================
.SYNOPSIS
    AI Breadboard — графический лончер сценариев и сервисов
.DESCRIPTION
    WinForms-окно с панелью быстрого запуска основных сценариев
    и динамическим каталогом всех лончеров из директории launchers/
    с поддержкой выбора ключей и параметров
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
    $ext = [System.IO.Path]::GetExtension($ScriptPath).ToLower()
    if ($ext -eq '.py') {
        $hasPy = Get-Command py.exe -ErrorAction SilentlyContinue
        $pythonExe = if ($hasPy) { 'py.exe' } else { 'python.exe' }
        $argStr = ($Args | ForEach-Object { "`"$_`"" }) -join ' '
        Start-Process $pythonExe -ArgumentList "`"$ScriptPath`" $argStr" -WorkingDirectory $scriptDir
    } else {
        $hasPwsh = Get-Command pwsh.exe -ErrorAction SilentlyContinue
        $shell   = if ($hasPwsh) { 'pwsh.exe' } else { 'powershell.exe' }
        $argStr  = ($Args | ForEach-Object { "$_" }) -join ' '
        Start-Process $shell -ArgumentList "-NoExit -ExecutionPolicy Bypass -File `"$ScriptPath`" $argStr" -WorkingDirectory $scriptDir
    }
}

function Get-ServerUrl {
    $cfgPath = Join-Path $scriptDir 'config\dashboard.json'
    $proto = 'http'; $host_ = 'localhost'; $port = '8000'
    if (Test-Path $cfgPath) {
        try {
            $cfg = Get-Content $cfgPath -Raw -Encoding UTF8 | ConvertFrom-Json
            if ($cfg.server.protocol) { $proto = $cfg.server.protocol }
            if ($cfg.server.host -and $cfg.server.host -ne '0.0.0.0') { $host_ = $cfg.server.host }
            if ($cfg.server.port) { $port = $cfg.server.port }
        } catch {}
    }
    return "${proto}://${host_}:${port}"
}

function Get-ScriptSynopsis {
    param([string]$FilePath)
    if (-not (Test-Path $FilePath)) { return '' }
    $lines = Get-Content $FilePath -Encoding UTF8 -ErrorAction SilentlyContinue -Head 30
    if (-not $lines) { return '' }
    
    $inSynopsis = $false
    $synLines = @()
    foreach ($line in $lines) {
        if ($line -match '^\s*\.\s*SYNOPSIS\b') {
            $inSynopsis = $true
            continue
        }
        if ($inSynopsis) {
            if ($line -match '^\s*\.\s*[A-Z]+' -or $line -match '^\s*#>') {
                break
            }
            $clean = $line -replace '^\s*#\s*', '' -replace '^\s*<\#\s*', ''
            if ($clean.Trim()) {
                $synLines += $clean.Trim()
            }
        }
    }
    if ($synLines.Count -gt 0) {
        return ($synLines -join ' ')
    }
    
    foreach ($line in $lines) {
        $clean = $line.Trim()
        if ($clean.StartsWith('#') -and -not $clean.StartsWith('#!')) {
            $text = $clean.TrimStart('#').Trim()
            if ($text -and -not $text.StartsWith('encoding')) {
                return $text
            }
        }
    }
    return ''
}

function Get-ScriptParameters {
    param([string]$FilePath)
    $params = @()
    if (-not (Test-Path $FilePath)) { return $params }
    
    $ext = [System.IO.Path]::GetExtension($FilePath).ToLower()
    if ($ext -eq '.ps1') {
        try {
            $tokens = $null
            $errors = $null
            $ast = [System.Management.Automation.Language.Parser]::ParseFile($FilePath, [ref]$tokens, [ref]$errors)
            if ($ast.ParamBlock -and $ast.ParamBlock.Parameters) {
                foreach ($p in $ast.ParamBlock.Parameters) {
                    $paramName = $p.Name.VariablePath.UserPath
                    if ($paramName -in @('Help', 'h')) { continue }
                    
                    $paramType = 'string'
                    if ($p.StaticType) { $paramType = $p.StaticType.Name }
                    
                    $isSwitch = ($paramType -eq 'SwitchParameter' -or ($p.Attributes | Where-Object { $_.TypeName.Name -eq 'switch' }))
                    
                    $validateSet = @()
                    foreach ($attr in $p.Attributes) {
                        if ($attr.TypeName.Name -eq 'ValidateSet' -or $attr.TypeName.FullName -eq 'ValidateSet') {
                            foreach ($pa in $attr.PositionalArguments) {
                                if ($pa.Extent) {
                                    $val = $pa.Extent.Text.Trim("'", '"')
                                    if ($val) { $validateSet += $val }
                                }
                            }
                        }
                    }
                    $validateSet = $validateSet | Select-Object -Unique
                    
                    $defaultValue = ''
                    if ($p.DefaultValue) {
                        $defaultValue = $p.DefaultValue.Extent.Text.Trim("'", '"')
                    }
                    
                    $isPositional = $false
                    foreach ($attr in $p.Attributes) {
                        if ($attr.TypeName.Name -eq 'Parameter') {
                            foreach ($named in $attr.NamedArguments) {
                                if ($named.ArgumentName -eq 'Position') {
                                    $isPositional = $true
                                }
                            }
                        }
                    }
                    
                    $params += [PSCustomObject]@{
                        Name         = $paramName
                        Type         = $paramType
                        IsSwitch     = $isSwitch
                        ValidateSet  = $validateSet
                        DefaultValue = $defaultValue
                        IsPositional = $isPositional
                    }
                }
            }
        } catch {}
    } elseif ($ext -eq '.py') {
        try {
            $content = Get-Content $FilePath -Raw -Encoding UTF8 -ErrorAction SilentlyContinue
            if ($content) {
                $argRegex = 'add_argument\s*\(\s*(?<args>[\x27"][^\x27"]+[\x27"](?:\s*,\s*[\x27"][^\x27"]+[\x27"])?)(?<rest>[^)]*)\)'
                $argMatches = [regex]::Matches($content, $argRegex)
                foreach ($m in $argMatches) {
                    $argsPart = $m.Groups['args'].Value
                    $rest = $m.Groups['rest'].Value
                    
                    $nameMatches = [regex]::Matches($argsPart, '[\x27"]([^\x27"]+)[\x27"]')
                    $names = @()
                    foreach ($nm in $nameMatches) { $names += $nm.Groups[1].Value }
                    if (-not $names) { continue }
                    $lastName = $names[-1]
                    $cleanName = $lastName.TrimStart('-')
                    if ($cleanName -in @('help', 'h')) { continue }
                    
                    $isPositional = -not ($names[0].StartsWith('-'))
                    
                    $validateSet = @()
                    if ($rest -match 'choices\s*=\s*\[([^\]]+)\]') {
                        $cMatches = [regex]::Matches($Matches[1], '[\x27"]([^\x27"]+)[\x27"]')
                        foreach ($cm in $cMatches) {
                            $validateSet += $cm.Groups[1].Value
                        }
                    }
                    
                    $defaultValue = ''
                    if ($rest -match 'default\s*=\s*[\x27"]?([^\x27",\s)]+)[\x27"]?') {
                        $defaultValue = $Matches[1]
                    }
                    
                    $isSwitch = ($rest -match 'action\s*=\s*[\x27"]store_true[\x27"]')
                    
                    $params += [PSCustomObject]@{
                        Name         = $cleanName
                        Type         = if ($isSwitch) { 'SwitchParameter' } else { 'string' }
                        IsSwitch     = $isSwitch
                        ValidateSet  = $validateSet
                        DefaultValue = $defaultValue
                        IsPositional = $isPositional
                    }
                }
            }
        } catch {}
    }
    return $params
}

# --- Form Setup ---

$form = New-Object System.Windows.Forms.Form
$form.Text            = 'AI Breadboard Launcher'
$form.Size            = New-Object System.Drawing.Size(680, 800)
$form.MinimumSize     = New-Object System.Drawing.Size(550, 500)
$form.StartPosition   = 'CenterScreen'
$form.FormBorderStyle = 'Sizable'
$form.BackColor       = [System.Drawing.Color]::FromArgb(30, 30, 30)
$form.Font            = New-Object System.Drawing.Font('Segoe UI', 9)

# --- Header Panel ---

$headerPanel = New-Object System.Windows.Forms.Panel
$headerPanel.Dock     = [System.Windows.Forms.DockStyle]::Top
$headerPanel.Height   = 60
$headerPanel.BackColor = [System.Drawing.Color]::FromArgb(37, 37, 38)
$form.Controls.Add($headerPanel)

$titleLabel = New-Object System.Windows.Forms.Label
$titleLabel.Text      = 'AI Breadboard Scenario Launcher'
$titleLabel.ForeColor = [System.Drawing.Color]::FromArgb(0, 200, 255)
$titleLabel.Font      = New-Object System.Drawing.Font('Segoe UI', 12, [System.Drawing.FontStyle]::Bold)
$titleLabel.AutoSize  = $true
$titleLabel.Location  = New-Object System.Drawing.Point(16, 10)
$headerPanel.Controls.Add($titleLabel)

$subTitleLabel = New-Object System.Windows.Forms.Label
$subTitleLabel.Text      = 'Выберите сервис или сценарий из категории launchers для запуска'
$subTitleLabel.ForeColor = [System.Drawing.Color]::FromArgb(180, 180, 180)
$subTitleLabel.Font      = New-Object System.Drawing.Font('Segoe UI', 9)
$subTitleLabel.AutoSize  = $true
$subTitleLabel.Location  = New-Object System.Drawing.Point(16, 34)
$headerPanel.Controls.Add($subTitleLabel)

# --- Quick Actions Panel ---

$quickGroup = New-Object System.Windows.Forms.GroupBox
$quickGroup.Text      = 'Быстрый запуск'
$quickGroup.ForeColor = [System.Drawing.Color]::FromArgb(0, 200, 255)
$quickGroup.Dock      = [System.Windows.Forms.DockStyle]::Top
$quickGroup.Height    = 80
$quickGroup.Padding   = New-Object System.Windows.Forms.Padding(10)
$quickGroup.BackColor = [System.Drawing.Color]::FromArgb(30, 30, 30)
$form.Controls.Add($quickGroup)

function New-QuickButton {
    param([string]$Text, [int]$X, [scriptblock]$OnClick)
    $btn = New-Object System.Windows.Forms.Button
    $btn.Text      = $Text
    $btn.Size      = New-Object System.Drawing.Size(145, 38)
    $btn.Location  = New-Object System.Drawing.Point($X, 26)
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

$btnRun = New-QuickButton -Text '▶ Run (FastAPI)' -X 16 -OnClick {
    Invoke-Script (Join-Path $scriptDir 'Run-Dashboard.ps1')
}
$btnTc = New-QuickButton -Text '🖥 TC (Рабочая среда)' -X 173 -OnClick {
    Invoke-Script (Join-Path $scriptDir 'Run-TC.ps1')
}
$btnHelpdesk = New-QuickButton -Text '🎫 Helpdesk' -X 330 -OnClick {
    Invoke-Script (Join-Path $scriptDir 'launchers\helpdesk.ps1')
}
$btnAdmin = New-QuickButton -Text '⚙ Admin Panel' -X 487 -OnClick {
    $url = (Get-ServerUrl) + '/admin'
    Start-Process $url
}

$quickGroup.Controls.AddRange(@($btnRun, $btnTc, $btnHelpdesk, $btnAdmin))

# --- Filter Search Panel ---

$searchPanel = New-Object System.Windows.Forms.Panel
$searchPanel.Dock     = [System.Windows.Forms.DockStyle]::Top
$searchPanel.Height   = 45
$searchPanel.Padding  = New-Object System.Windows.Forms.Padding(16, 8, 16, 8)
$form.Controls.Add($searchPanel)

$searchLabel = New-Object System.Windows.Forms.Label
$searchLabel.Text      = '🔍 Поиск:'
$searchLabel.ForeColor = [System.Drawing.Color]::White
$searchLabel.AutoSize  = $true
$searchLabel.Location  = New-Object System.Drawing.Point(16, 12)
$searchPanel.Controls.Add($searchLabel)

$txtSearch = New-Object System.Windows.Forms.TextBox
$txtSearch.Location  = New-Object System.Drawing.Point(80, 9)
$txtSearch.Size      = New-Object System.Drawing.Size(550, 25)
$txtSearch.BackColor = [System.Drawing.Color]::FromArgb(45, 45, 48)
$txtSearch.ForeColor = [System.Drawing.Color]::White
$txtSearch.BorderStyle = [System.Windows.Forms.BorderStyle]::FixedSingle
$txtSearch.Anchor    = [System.Windows.Forms.AnchorStyles]::Left -bor [System.Windows.Forms.AnchorStyles]::Right -bor [System.Windows.Forms.AnchorStyles]::Top
$searchPanel.Controls.Add($txtSearch)

# --- Scrollable Launchers Panel ---

$scrollPanel = New-Object System.Windows.Forms.Panel
$scrollPanel.Dock       = [System.Windows.Forms.DockStyle]::Fill
$scrollPanel.AutoScroll = $true
$scrollPanel.Padding    = New-Object System.Windows.Forms.Padding(16)
$form.Controls.Add($scrollPanel)

$flowLayout = New-Object System.Windows.Forms.FlowLayoutPanel
$flowLayout.Dock        = [System.Windows.Forms.DockStyle]::Top
$flowLayout.AutoSize    = $true
$flowLayout.AutoSizeMode = [System.Windows.Forms.AutoSizeMode]::GrowAndShrink
$flowLayout.FlowDirection = [System.Windows.Forms.FlowDirection]::TopDown
$flowLayout.WrapContents  = $false
$flowLayout.Width       = 620
$scrollPanel.Controls.Add($flowLayout)

# --- Dynamic Load of Launchers ---

$launchersDir = Join-Path $scriptDir 'launchers'
$launcherCards = @()

if (Test-Path $launchersDir) {
    $files = Get-ChildItem $launchersDir -File | Where-Object {
        $_.Extension -in ('.ps1', '.py') -and $_.Name -ne 'ShowHide-InTray.ps1'
    } | Sort-Object Name

    foreach ($file in $files) {
        $synopsis = Get-ScriptSynopsis -FilePath $file.FullName
        $scriptParams = Get-ScriptParameters -FilePath $file.FullName
        
        $paramKeysStr = ($scriptParams | ForEach-Object { $_.Name }) -join ' '
        
        $card = New-Object System.Windows.Forms.Panel
        $card.Width     = 610
        $card.Margin    = New-Object System.Windows.Forms.Padding(0, 0, 0, 8)
        $card.BackColor = [System.Drawing.Color]::FromArgb(40, 40, 42)
        $card.BorderStyle = [System.Windows.Forms.BorderStyle]::FixedSingle
        $card.Tag       = "$($file.Name) $synopsis $paramKeysStr".ToLower()

        $btnLaunch = New-Object System.Windows.Forms.Button
        $btnLaunch.Text      = 'Запустить'
        $btnLaunch.Size      = New-Object System.Drawing.Size(95, 34)
        $btnLaunch.Location  = New-Object System.Drawing.Point(500, 8)
        $btnLaunch.Anchor    = [System.Windows.Forms.AnchorStyles]::Right -bor [System.Windows.Forms.AnchorStyles]::Top
        $btnLaunch.FlatStyle = 'Flat'
        $btnLaunch.FlatAppearance.BorderColor = [System.Drawing.Color]::FromArgb(0, 200, 255)
        $btnLaunch.BackColor  = [System.Drawing.Color]::FromArgb(0, 122, 204)
        $btnLaunch.ForeColor  = [System.Drawing.Color]::White
        $btnLaunch.Cursor     = [System.Windows.Forms.Cursors]::Hand
        
        $lblTitle = New-Object System.Windows.Forms.Label
        $lblTitle.Text      = $file.Name
        $lblTitle.Font      = New-Object System.Drawing.Font('Segoe UI', 9.5, [System.Drawing.FontStyle]::Bold)
        $lblTitle.ForeColor = [System.Drawing.Color]::FromArgb(0, 200, 255)
        $lblTitle.Location  = New-Object System.Drawing.Point(10, 6)
        $lblTitle.AutoSize  = $true
        $card.Controls.Add($lblTitle)

        $lblDesc = New-Object System.Windows.Forms.Label
        $lblDesc.Text      = if ($synopsis) { $synopsis } else { 'Сценарий запуска платформы AI Breadboard' }
        $lblDesc.Font      = New-Object System.Drawing.Font('Segoe UI', 8.5)
        $lblDesc.ForeColor = [System.Drawing.Color]::FromArgb(190, 190, 190)
        $lblDesc.Location  = New-Object System.Drawing.Point(10, 27)
        $lblDesc.Size      = New-Object System.Drawing.Size(480, 18)
        $lblDesc.AutoEllipsis = $true
        $card.Controls.Add($lblDesc)

        $card.Controls.Add($btnLaunch)

        $paramPanel = $null
        if ($scriptParams.Count -gt 0) {
            $paramPanel = New-Object System.Windows.Forms.FlowLayoutPanel
            $paramPanel.Location = New-Object System.Drawing.Point(10, 48)
            $paramPanel.Width = 485
            $paramPanel.AutoSize = $true
            $paramPanel.AutoSizeMode = [System.Windows.Forms.AutoSizeMode]::GrowAndShrink
            $paramPanel.FlowDirection = [System.Windows.Forms.FlowDirection]::LeftToRight
            $paramPanel.WrapContents = $true
            $paramPanel.Margin = New-Object System.Windows.Forms.Padding(0)

            foreach ($p in $scriptParams) {
                if ($p.ValidateSet -and $p.ValidateSet.Count -gt 0) {
                    # Выпадающий список для выбора из нескольких вариантов
                    $lblParam = New-Object System.Windows.Forms.Label
                    $lblParam.Text = "-$($p.Name):"
                    $lblParam.ForeColor = [System.Drawing.Color]::FromArgb(200, 200, 200)
                    $lblParam.AutoSize = $true
                    $lblParam.Margin = New-Object System.Windows.Forms.Padding(0, 4, 2, 0)
                    $paramPanel.Controls.Add($lblParam)

                    $combo = New-Object System.Windows.Forms.ComboBox
                    $combo.DropDownStyle = [System.Windows.Forms.ComboBoxStyle]::DropDownList
                    $combo.Size = New-Object System.Drawing.Size(100, 23)
                    $combo.BackColor = [System.Drawing.Color]::FromArgb(50, 50, 55)
                    $combo.ForeColor = [System.Drawing.Color]::White
                    $combo.FlatStyle = [System.Windows.Forms.FlatStyle]::Flat
                    foreach ($val in $p.ValidateSet) {
                        [void]$combo.Items.Add($val)
                    }
                    if ($p.DefaultValue -and $combo.Items.Contains($p.DefaultValue)) {
                        $combo.SelectedItem = $p.DefaultValue
                    } else {
                        $combo.SelectedIndex = 0
                    }
                    $combo.Margin = New-Object System.Windows.Forms.Padding(0, 0, 10, 4)
                    $combo.Tag = @{ Name = $p.Name; Kind = 'Choice'; IsPositional = $p.IsPositional; FileExt = $file.Extension }
                    $paramPanel.Controls.Add($combo)
                } elseif ($p.IsSwitch) {
                    # Флажок (Switch)
                    $chk = New-Object System.Windows.Forms.CheckBox
                    $chk.Text = "-$($p.Name)"
                    $chk.ForeColor = [System.Drawing.Color]::FromArgb(200, 200, 200)
                    $chk.AutoSize = $true
                    $chk.Checked = ($p.DefaultValue -eq 'true' -or $p.DefaultValue -eq '$true')
                    $chk.Margin = New-Object System.Windows.Forms.Padding(0, 2, 10, 4)
                    $chk.Tag = @{ Name = $p.Name; Kind = 'Switch'; IsPositional = $p.IsPositional; FileExt = $file.Extension }
                    $paramPanel.Controls.Add($chk)
                } else {
                    # Текстовое поле для ввода аргумента
                    $lblParam = New-Object System.Windows.Forms.Label
                    $lblParam.Text = "-$($p.Name):"
                    $lblParam.ForeColor = [System.Drawing.Color]::FromArgb(200, 200, 200)
                    $lblParam.AutoSize = $true
                    $lblParam.Margin = New-Object System.Windows.Forms.Padding(0, 4, 2, 0)
                    $paramPanel.Controls.Add($lblParam)

                    $txt = New-Object System.Windows.Forms.TextBox
                    $txt.Text = if ($p.DefaultValue) { $p.DefaultValue } else { '' }
                    $txt.Size = New-Object System.Drawing.Size(80, 23)
                    $txt.BackColor = [System.Drawing.Color]::FromArgb(50, 50, 55)
                    $txt.ForeColor = [System.Drawing.Color]::White
                    $txt.BorderStyle = [System.Windows.Forms.BorderStyle]::FixedSingle
                    $txt.Margin = New-Object System.Windows.Forms.Padding(0, 0, 10, 4)
                    $txt.Tag = @{ Name = $p.Name; Kind = 'Text'; IsPositional = $p.IsPositional; FileExt = $file.Extension }
                    $paramPanel.Controls.Add($txt)
                }
            }

            $card.Controls.Add($paramPanel)
            $card.Height = 52 + $paramPanel.Height + 6
        } else {
            $card.Height = 52
        }

        $filePath = $file.FullName
        $fileExt = $file.Extension
        $localParamPanel = $paramPanel

        $btnLaunch.Add_Click({
            $callArgs = @()
            if ($localParamPanel) {
                foreach ($ctrl in $localParamPanel.Controls) {
                    if (-not $ctrl.Tag) { continue }
                    $meta = $ctrl.Tag
                    $pName = $meta.Name
                    $kind = $meta.Kind

                    if ($kind -eq 'Choice') {
                        $selectedVal = [string]$ctrl.SelectedItem
                        if ($selectedVal) {
                            if ($meta.IsPositional -and $fileExt -eq '.py') {
                                $callArgs += $selectedVal
                            } else {
                                $flagPrefix = if ($fileExt -eq '.py' -and -not $pName.StartsWith('-')) { "--" } else { "-" }
                                $callArgs += "$flagPrefix$pName"
                                $callArgs += $selectedVal
                            }
                        }
                    } elseif ($kind -eq 'Switch') {
                        if ($ctrl.Checked) {
                            $flagPrefix = if ($fileExt -eq '.py' -and -not $pName.StartsWith('-')) { "--" } else { "-" }
                            $callArgs += "$flagPrefix$pName"
                        }
                    } elseif ($kind -eq 'Text') {
                        $txtVal = $ctrl.Text.Trim()
                        if ($txtVal) {
                            if ($meta.IsPositional -and $fileExt -eq '.py') {
                                $callArgs += $txtVal
                            } else {
                                $flagPrefix = if ($fileExt -eq '.py' -and -not $pName.StartsWith('-')) { "--" } else { "-" }
                                $callArgs += "$flagPrefix$pName"
                                $callArgs += $txtVal
                            }
                        }
                    }
                }
            }
            Invoke-Script -ScriptPath $filePath -Args $callArgs
        })

        $flowLayout.Controls.Add($card)
        $launcherCards += $card
    }
}

# --- Search Event Handler ---

$txtSearch.Add_TextChanged({
    $query = $txtSearch.Text.Trim().ToLower()
    $flowLayout.SuspendLayout()
    foreach ($card in $launcherCards) {
        if ([string]::IsNullOrEmpty($query) -or $card.Tag.Contains($query)) {
            $card.Visible = $true
        } else {
            $card.Visible = $false
        }
    }
    $flowLayout.ResumeLayout()
})

# Bring quickGroup and headers to top in correct z-order
$headerPanel.BringToFront()
$quickGroup.BringToFront()
$searchPanel.BringToFront()
$scrollPanel.BringToFront()

[void]$form.ShowDialog()
