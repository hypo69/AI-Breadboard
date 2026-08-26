<#
.SYNOPSIS
    Установщик проекта ai-assistant с поддержкой мультиязычности (i18n).
.DESCRIPTION
    Инициализирует кодировку UTF-8, запрашивает язык установки (RU/EN/HE),
    разблокирует файлы, создает виртуальное окружение, обновляет pip,
    устанавливает зависимости, настраивает SSL и проверяет готовность окружения.
.EXAMPLE
    .\install.ps1
#>

$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$VenvDir    = Join-Path $ScriptRoot 'venv'
$PythonPath = Join-Path $VenvDir 'Scripts\python.exe'

# ============================================================
# СЛОВАРЬ ПЕРЕВОДОВ (I18N)
# ============================================================
$I18N = @{
    ru = @{
        lang_name             = "Русский"
        select_lang_header    = "ai-assistant — МАСТЕР УСТАНОВКИ / INSTALLATION WIZARD"
        select_lang_prompt    = "Выберите язык установки / Select language:"
        lang_default_suffix   = "[По умолчанию]"
        lang_choice_prompt    = "Язык / Language [{0}]"
        lang_selected         = "-> Выбран язык: {0}"
        
        banner_title          = "              ai-assistant — МАСТЕР УСТАНОВКИ                      "
        
        step_1                = "[1/6] Снятие блокировки Windows (Unblock-File)..."
        step_1_ok             = "    [OK] Файлы разблокированы"
        
        step_2                = "[2/6] Проверка виртуального окружения (venv)..."
        step_2_existing       = "    [OK] venv уже существует: {0} ({1})"
        step_2_damaged        = "    [WARN] Существующий venv поврежден. Требуется пересоздание."
        step_2_err_launch     = "    [WARN] Ошибка запуска venv python: {0}"
        step_2_searching      = "    Поиск системного интерпретатора Python..."
        step_2_py_found       = "    [OK] Найден интерпретатор через Python Launcher: {0}"
        step_2_sys_found      = "    [OK] Найден системный интерпретатор: {0} ({1})"
        step_2_py_not_found   = "    [ERROR] Python не найден на вашей системе!"
        step_2_py_install_tip = "    Пожалуйста, установите Python 3.12 или 3.13 с официального сайта: https://www.python.org/downloads/`n    При установке обязательно отметьте галочку `"Add python.exe to PATH`"."
        step_2_remove_old     = "    Удаление старого каталога venv..."
        step_2_creating       = "    Создание виртуального окружения в {0}..."
        step_2_create_fail    = "    [ERROR] Не удалось создать виртуальное окружение."
        step_2_created_ok     = "    [OK] Виртуальное окружение успешно создано"
        
        step_3                = "[3/6] Обновление pip и базовых утилит..."
        step_3_ok             = "    [OK] pip, setuptools, wheel обновлены"
        step_3_warn           = "    [WARN] Не удалось обновить pip (продолжаем установку)"
        
        step_4                = "[4/6] Установка зависимостей проекта..."
        step_4_menu_title     = "    Выберите вариант установки зависимостей:"
        step_4_opt_1          = "      [1] Полная установка (Core + AI + Utils) — РЕКОМЕНДУЕТСЯ"
        step_4_opt_2          = "      [2] Только базовый сервер (Core)"
        step_4_opt_3          = "      [3] Сервер + AI модули (Core + AI)"
        step_4_opt_4          = "      [4] Полная установка + Тесты и Документация (Dev)"
        step_4_opt_5          = "      [5] Пропустить установку зависимостей"
        step_4_choice_prompt  = "    Ваш выбор [по умолчанию 1]"
        step_4_installing_all = "    Установка всех основных зависимостей из requirements.txt..."
        step_4_installing_core= "    Установка Core зависимостей..."
        step_4_installing_ai  = "    Установка Core + AI зависимостей..."
        step_4_installing_dev = "    Установка полного набора + Dev..."
        step_4_skipped        = "    Установка зависимостей пропущена пользователем."
        step_4_default_msg    = "    Выбрано по умолчанию: полная установка из requirements.txt..."
        step_4_pip_error      = "    [ERROR] Возникли ошибки при установке пакетов pip."
        
        step_5                = "[5/6] Проверка SSL-сертификатов..."
        step_5_found          = "    [OK] SSL-сертификаты найдены ({0})"
        step_5_not_found      = "    [INFO] SSL-сертификаты не найдены. Вызов мастера создания сертификатов..."
        step_5_missing_script = "    [WARN] Скрипт {0} не найден. Сервер будет запускаться без SSL."
        
        step_6                = "[6/6] Проверка установленного окружения..."
        step_6_ok             = "    [OK] Основные библиотеки успешно инициализированы"
        step_6_py_path        = "    [OK] Python интерпретатор: {0}"
        step_6_warn           = "    [WARN] Результат проверки: {0}"
        
        finish_banner_1       = "║         УСТАНОВКА ai-assistant УСПЕШНО ЗАВЕРШЕНА!                 ║"
        finish_banner_2       = "║  Запуск сервера:  ./run.ps1                                   ║"
    }
    en = @{
        lang_name             = "English"
        select_lang_header    = "ai-assistant — INSTALLATION WIZARD / МАСТЕР УСТАНОВКИ"
        select_lang_prompt    = "Select installation language / Выберите язык установки:"
        lang_default_suffix   = "[Default]"
        lang_choice_prompt    = "Language / Язык [{0}]"
        lang_selected         = "-> Selected language: {0}"
        
        banner_title          = "              ai-assistant — INSTALLATION WIZARD                    "
        
        step_1                = "[1/6] Unblocking Windows files (Unblock-File)..."
        step_1_ok             = "    [OK] Files unblocked"
        
        step_2                = "[2/6] Checking virtual environment (venv)..."
        step_2_existing       = "    [OK] venv already exists: {0} ({1})"
        step_2_damaged        = "    [WARN] Existing venv is corrupted. Re-creation required."
        step_2_err_launch     = "    [WARN] Error launching venv python: {0}"
        step_2_searching      = "    Searching for system Python interpreter..."
        step_2_py_found       = "    [OK] Found Python interpreter via Python Launcher: {0}"
        step_2_sys_found      = "    [OK] Found system Python interpreter: {0} ({1})"
        step_2_py_not_found   = "    [ERROR] Python was not found on your system!"
        step_2_py_install_tip = "    Please install Python 3.12 or 3.13 from: https://www.python.org/downloads/`n    Make sure to check `"Add python.exe to PATH`" during installation."
        step_2_remove_old     = "    Removing old venv directory..."
        step_2_creating       = "    Creating virtual environment in {0}..."
        step_2_create_fail    = "    [ERROR] Failed to create virtual environment."
        step_2_created_ok     = "    [OK] Virtual environment created successfully"
        
        step_3                = "[3/6] Upgrading pip and build tools..."
        step_3_ok             = "    [OK] pip, setuptools, wheel upgraded"
        step_3_warn           = "    [WARN] Failed to upgrade pip (continuing installation)"
        
        step_4                = "[4/6] Installing project dependencies..."
        step_4_menu_title     = "    Select dependency installation option:"
        step_4_opt_1          = "      [1] Full installation (Core + AI + Utils) — RECOMMENDED"
        step_4_opt_2          = "      [2] Core server only"
        step_4_opt_3          = "      [3] Core + AI modules"
        step_4_opt_4          = "      [4] Full installation + Tests & Docs (Dev)"
        step_4_opt_5          = "      [5] Skip dependency installation"
        step_4_choice_prompt  = "    Your choice [default 1]"
        step_4_installing_all = "    Installing all main dependencies from requirements.txt..."
        step_4_installing_core= "    Installing Core dependencies..."
        step_4_installing_ai  = "    Installing Core + AI dependencies..."
        step_4_installing_dev = "    Installing full dependency set + Dev..."
        step_4_skipped        = "    Dependency installation skipped by user."
        step_4_default_msg    = "    Default selected: full installation from requirements.txt..."
        step_4_pip_error      = "    [ERROR] Errors occurred during pip package installation."
        
        step_5                = "[5/6] Checking SSL certificates..."
        step_5_found          = "    [OK] SSL certificates found ({0})"
        step_5_not_found      = "    [INFO] SSL certificates not found. Invoking certificate wizard..."
        step_5_missing_script = "    [WARN] Script {0} not found. Server will run without SSL."
        
        step_6                = "[6/6] Verifying installed environment..."
        step_6_ok             = "    [OK] Core libraries successfully initialized"
        step_6_py_path        = "    [OK] Python interpreter: {0}"
        step_6_warn           = "    [WARN] Verification output: {0}"
        
        finish_banner_1       = "║         ai-assistant INSTALLATION COMPLETED SUCCESSFULLY!         ║"
        finish_banner_2       = "║  Start server:   ./run.ps1                                    ║"
    }
    he = @{
        lang_name             = "עברית (Hebrew)"
        select_lang_header    = "ai-assistant — אשף ההתקנה / INSTALLATION WIZARD"
        select_lang_prompt    = "בחר שפת התקנה / Select installation language:"
        lang_default_suffix   = "[ברירת מחדל]"
        lang_choice_prompt    = "שפה / Language [{0}]"
        lang_selected         = "-> שפה שנבחרה: {0}"
        
        banner_title          = "              ai-assistant — אשף ההתקנה                              "
        
        step_1                = "[1/6] שחרור חסימת קבצים של Windows (Unblock-File)..."
        step_1_ok             = "    [OK] חסימת הקבצים הוסרה בהצלחה"
        
        step_2                = "[2/6] בדיקת סביבה וירטואלית (venv)..."
        step_2_existing       = "    [OK] סביבת venv כבר קיימת: {0} ({1})"
        step_2_damaged        = "    [WARN] סביבת venv פגומה. נדרשת יצירה מחדש."
        step_2_err_launch     = "    [WARN] שגיאה בהפעלת venv python: {0}"
        step_2_searching      = "    מחפש מפרש Python במערכת..."
        step_2_py_found       = "    [OK] נמצא מפרש Python דרך Python Launcher: {0}"
        step_2_sys_found      = "    [OK] נמצא מפרש Python במערכת: {0} ({1})"
        step_2_py_not_found   = "    [ERROR] Python לא נמצא במערכת שלך!"
        step_2_py_install_tip = "    אנא התקן Python 3.12 או 3.13 מאתר: https://www.python.org/downloads/`n    הקפד לסמן את האפשרות `"Add python.exe to PATH`" במהלך ההתקנה."
        step_2_remove_old     = "    מוחק תיקיית venv ישנה..."
        step_2_creating       = "    יוצר סביבה וירטואלית ב-{0}..."
        step_2_create_fail    = "    [ERROR] יצירת סביבת venv נכשלה."
        step_2_created_ok     = "    [OK] סביבת venv נוצרה בהצלחה"
        
        step_3                = "[3/6] מעדכן את pip וכלי בנייה..."
        step_3_ok             = "    [OK] pip, setuptools, wheel עודכנו בהצלחה"
        step_3_warn           = "    [WARN] עדכון pip נכשל (ממשיך בהתקנה)"
        
        step_4                = "[4/6] התקנת תלויות הפרויקט..."
        step_4_menu_title     = "    בחר אפשרות התקנת תלויות:"
        step_4_opt_1          = "      [1] התקנה מלאה (Core + AI + Utils) — מומלץ"
        step_4_opt_2          = "      [2] שרת בסיסי בלבד (Core)"
        step_4_opt_3          = "      [3] שרת + מודולי AI (Core + AI)"
        step_4_opt_4          = "      [4] התקנה מלאה + בדיקות ותיעוד (Dev)"
        step_4_opt_5          = "      [5] דלג על התקנת תלויות"
        step_4_choice_prompt  = "    הבחירה שלך [ברירת מחדל 1]"
        step_4_installing_all = "    מתקין את כל התלויות הראשיות מ-requirements.txt..."
        step_4_installing_core= "    מתקין תלויות Core..."
        step_4_installing_ai  = "    מתקין תלויות Core + AI..."
        step_4_installing_dev = "    מתקין את כל החבילות כולל Dev..."
        step_4_skipped        = "    התקנת התלויות דולגה על ידי המשתמש."
        step_4_default_msg    = "    נבחרה ברירת מחדל: התקנה מלאה מ-requirements.txt..."
        step_4_pip_error      = "    [ERROR] אירעו שגיאות בעת התקנת חבילות pip."
        
        step_5                = "[5/6] בדיקת תעודות SSL..."
        step_5_found          = "    [OK] תעודות SSL נמצאו ({0})"
        step_5_not_found      = "    [INFO] תעודות SSL לא נמצאו. מפעיל אשף יצירת תעודות..."
        step_5_missing_script = "    [WARN] הסקריפט {0} לא נמצא. השרת יפעל ללא SSL."
        
        step_6                = "[6/6] אימות תקינות הסביבה..."
        step_6_ok             = "    [OK] כל הספריות הראשיות אותחלו בהצלחה"
        step_6_py_path        = "    [OK] מפרש Python: {0}"
        step_6_warn           = "    [WARN] תוצאת הבדיקה: {0}"
        
        finish_banner_1       = "║         התקנת ai-assistant הושלמה בהצלחה!                          ║"
        finish_banner_2       = "║  הפעלת השרת:     ./run.ps1                                    ║"
    }
}

$Global:CurrentLang = "ru"
$Global:FallbackLang = "en"

function Msg {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Key,
        [object[]]$Args_ = @()
    )

    $dict = $I18N[$Global:CurrentLang]
    $str = $null

    if ($dict -and $dict.ContainsKey($Key)) {
        $str = $dict[$Key]
    } elseif ($I18N[$Global:FallbackLang].ContainsKey($Key)) {
        $str = $I18N[$Global:FallbackLang][$Key]
    } elseif ($I18N['ru'].ContainsKey($Key)) {
        $str = $I18N['ru'][$Key]
    } else {
        return "[$Key]"
    }

    if ($Args_ -and $Args_.Count -gt 0) {
        return [string]::Format($str, $Args_)
    }
    return $str
}

function Select-InstallerLanguage {
    $culture = (Get-Culture).TwoLetterISOLanguageName.ToLower()
    $defaultLang = "ru"
    if ($I18N.ContainsKey($culture)) {
        $defaultLang = $culture
    }

    $languages = @("ru", "en", "he")
    $defaultIndex = [array]::IndexOf($languages, $defaultLang) + 1
    if ($defaultIndex -le 0) { $defaultIndex = 1 }

    Write-Host ""
    Write-Host "╔═══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "║              ai-assistant — LANGUAGE / ЯЗЫК                   ║" -ForegroundColor Cyan
    Write-Host "╚═══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  Select language / Выберите язык установки:" -ForegroundColor White
    
    for ($i = 0; $i -lt $languages.Count; $i++) {
        $code = $languages[$i]
        $name = $I18N[$code]["lang_name"]
        $num = $i + 1
        if ($num -eq $defaultIndex) {
            Write-Host "    [$num] $name ($code) [Default / По умолчанию]" -ForegroundColor Green
        } else {
            Write-Host "    [$num] $name ($code)" -ForegroundColor Gray
        }
    }
    Write-Host ""

    $userChoice = Read-Host "  Language / Язык [$defaultIndex]"
    if (-not $userChoice) { $userChoice = [string]$defaultIndex }

    $chosenIndex = 0
    if ([int]::TryParse($userChoice, [ref]$chosenIndex) -and $chosenIndex -ge 1 -and $chosenIndex -le $languages.Count) {
        $Global:CurrentLang = $languages[$chosenIndex - 1]
    } else {
        $Global:CurrentLang = $languages[$defaultIndex - 1]
    }

    Write-Host (Msg "lang_selected" @($I18N[$Global:CurrentLang]["lang_name"])) -ForegroundColor Green
    Write-Host ""
}

# ============================================================
# [0] ВЫБОР ЯЗЫКА УСТАНОВКИ
# ============================================================
Select-InstallerLanguage

# ============================================================
# [1/6] Снятие Mark of the Web со всего проекта
# ============================================================
Write-Host (Msg "step_1") -ForegroundColor Cyan

Get-ChildItem -Path $ScriptRoot -Recurse -File -ErrorAction SilentlyContinue |
    Where-Object { $_.FullName -notmatch '\\\.git\\' } |
    Unblock-File -ErrorAction SilentlyContinue

Write-Host (Msg "step_1_ok") -ForegroundColor Green

# ============================================================
# [2/6] Проверка / Создание виртуального окружения
# ============================================================
Write-Host ''
Write-Host (Msg "step_2") -ForegroundColor Cyan

$needCreateVenv = $false

if (Test-Path $PythonPath) {
    try {
        $testVer = & $PythonPath --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host (Msg "step_2_existing" @($testVer, $PythonPath)) -ForegroundColor Green
        } else {
            Write-Host (Msg "step_2_damaged") -ForegroundColor Yellow
            $needCreateVenv = $true
        }
    } catch {
        Write-Host (Msg "step_2_err_launch" @($_)) -ForegroundColor Yellow
        $needCreateVenv = $true
    }
} else {
    $needCreateVenv = $true
}

if ($needCreateVenv) {
    Write-Host (Msg "step_2_searching") -ForegroundColor DarkGray
    
    $sysPythonCmd = $null
    
    # 1. Проверяем py launcher
    $pyCheck = Get-Command py -ErrorAction SilentlyContinue
    if ($pyCheck) {
        foreach ($ver in @('-3.13', '-3.12', '-3.11', '-3')) {
            $check = & py $ver --version 2>&1
            if ($LASTEXITCODE -eq 0) {
                $sysPythonCmd = @('py', $ver)
                Write-Host (Msg "step_2_py_found" @($check)) -ForegroundColor Green
                break
            }
        }
    }
    
    # 2. Если py launcher не найден, ищем python / python3
    if (-not $sysPythonCmd) {
        foreach ($cmd in @('python', 'python3')) {
            $cmdCheck = Get-Command $cmd -ErrorAction SilentlyContinue
            if ($cmdCheck) {
                $check = & $cmd --version 2>&1
                if ($LASTEXITCODE -eq 0 -and $check -notmatch 'WindowsApps') {
                    $sysPythonCmd = @($cmd)
                    Write-Host (Msg "step_2_sys_found" @($check, $cmdCheck.Source)) -ForegroundColor Green
                    break
                }
            }
        }
    }

    if (-not $sysPythonCmd) {
        Write-Host ''
        Write-Host (Msg "step_2_py_not_found") -ForegroundColor Red
        Write-Host (Msg "step_2_py_install_tip") -ForegroundColor Yellow
        exit 1
    }

    if (Test-Path $VenvDir) {
        Write-Host (Msg "step_2_remove_old") -ForegroundColor DarkGray
        Remove-Item $VenvDir -Recurse -Force -ErrorAction SilentlyContinue
    }

    Write-Host (Msg "step_2_creating" @($VenvDir)) -ForegroundColor Cyan
    & $sysPythonCmd[0] $sysPythonCmd[1..($sysPythonCmd.Length-1)] -m venv $VenvDir
    
    if ($LASTEXITCODE -ne 0 -or -not (Test-Path $PythonPath)) {
        Write-Host (Msg "step_2_create_fail") -ForegroundColor Red
        exit 1
    }
    
    # Снимаем блокировку со свежесозданного venv
    Get-ChildItem -Path $VenvDir -Recurse -File -ErrorAction SilentlyContinue |
        Unblock-File -ErrorAction SilentlyContinue

    Write-Host (Msg "step_2_created_ok") -ForegroundColor Green
}

# ============================================================
# [3/6] Обновление pip
# ============================================================
Write-Host ''
Write-Host (Msg "step_3") -ForegroundColor Cyan
& $PythonPath -m pip install --upgrade pip setuptools wheel --quiet
if ($LASTEXITCODE -eq 0) {
    Write-Host (Msg "step_3_ok") -ForegroundColor Green
} else {
    Write-Host (Msg "step_3_warn") -ForegroundColor Yellow
}

# ============================================================
# [4/6] Установка зависимостей проекта
# ============================================================
Write-Host ''
Write-Host (Msg "step_4") -ForegroundColor Cyan

$reqMain = Join-Path $ScriptRoot 'requirements.txt'
$reqCore = Join-Path $ScriptRoot 'req\requirements-core.txt'
$reqAi   = Join-Path $ScriptRoot 'req\requirements-ai.txt'
$reqTest = Join-Path $ScriptRoot 'req\requirements-test.txt'
$reqDocs = Join-Path $ScriptRoot 'req\requirements-docs.txt'

Write-Host (Msg "step_4_menu_title") -ForegroundColor Gray
Write-Host (Msg "step_4_opt_1") -ForegroundColor White
Write-Host (Msg "step_4_opt_2") -ForegroundColor Gray
Write-Host (Msg "step_4_opt_3") -ForegroundColor Gray
Write-Host (Msg "step_4_opt_4") -ForegroundColor Gray
Write-Host (Msg "step_4_opt_5") -ForegroundColor DarkGray
Write-Host ''

$choice = Read-Host (Msg "step_4_choice_prompt")
if (-not $choice) { $choice = '1' }

switch ($choice) {
    '1' {
        Write-Host ''
        Write-Host (Msg "step_4_installing_all") -ForegroundColor Cyan
        & $PythonPath -m pip install -r $reqMain
    }
    '2' {
        Write-Host ''
        Write-Host (Msg "step_4_installing_core") -ForegroundColor Cyan
        & $PythonPath -m pip install -r $reqCore
    }
    '3' {
        Write-Host ''
        Write-Host (Msg "step_4_installing_ai") -ForegroundColor Cyan
        & $PythonPath -m pip install -r $reqCore -r $reqAi
    }
    '4' {
        Write-Host ''
        Write-Host (Msg "step_4_installing_dev") -ForegroundColor Cyan
        & $PythonPath -m pip install -r $reqMain -r $reqTest -r $reqDocs
    }
    '5' {
        Write-Host (Msg "step_4_skipped") -ForegroundColor Yellow
    }
    default {
        Write-Host ''
        Write-Host (Msg "step_4_default_msg") -ForegroundColor Cyan
        & $PythonPath -m pip install -r $reqMain
    }
}

if ($choice -ne '5' -and $LASTEXITCODE -ne 0) {
    Write-Host (Msg "step_4_pip_error") -ForegroundColor Red
    exit 1
}

# ============================================================
# [5/6] Проверка и настройка SSL-сертификатов (.certs)
# ============================================================
Write-Host ''
Write-Host (Msg "step_5") -ForegroundColor Cyan

$certsDir = Join-Path $env:USERPROFILE ".certs"
$certFile = Join-Path $certsDir "localhost+2.pem"
$keyFile  = Join-Path $certsDir "localhost+2-key.pem"

if ((Test-Path $certFile) -and (Test-Path $keyFile)) {
    Write-Host (Msg "step_5_found" @($certFile)) -ForegroundColor Green
} else {
    Write-Host (Msg "step_5_not_found") -ForegroundColor Yellow
    $sslScript = Join-Path $ScriptRoot "install_ssl_cert.ps1"
    if (Test-Path $sslScript) {
        & $sslScript
    } else {
        Write-Host (Msg "step_5_missing_script" @($sslScript)) -ForegroundColor Yellow
    }
}

# ============================================================
# [6/6] Финальная проверка работоспособности
# ============================================================
Write-Host ''
Write-Host (Msg "step_6") -ForegroundColor Cyan

$testScript = "
import sys
modules = ['fastapi', 'uvicorn', 'dotenv', 'pydantic', 'aiohttp', 'cryptography']
loaded = []
failed = []
for m in modules:
    try:
        __import__(m)
        loaded.append(m)
    except ImportError:
        failed.append(m)
print('loaded=' + ','.join(loaded))
if failed:
    print('missing=' + ','.join(failed))
"

$checkOutput = & $PythonPath -c $testScript 2>&1

if ($LASTEXITCODE -eq 0 -and $checkOutput -match 'loaded=') {
    Write-Host (Msg "step_6_ok") -ForegroundColor Green
    Write-Host (Msg "step_6_py_path" @($PythonPath)) -ForegroundColor Green
} else {
    Write-Host (Msg "step_6_warn" @($checkOutput)) -ForegroundColor Yellow
}

# Сохраняем выбранный язык в config.json
$configPath = Join-Path $ScriptRoot "config.json"
if (Test-Path $configPath) {
    try {
        $jsonContent = Get-Content $configPath -Raw | ConvertFrom-Json
        if (-not $jsonContent.user_settings) {
            $jsonContent | Add-Member -NotePropertyName "user_settings" -NotePropertyValue (New-Object PSObject) -Force
        }
        $jsonContent.user_settings | Add-Member -NotePropertyName "language" -NotePropertyValue $Global:CurrentLang -Force
        $jsonContent | ConvertTo-Json -Depth 10 | Set-Content $configPath -Encoding UTF8
    } catch {}
}

Write-Host ''
Write-Host '╔═══════════════════════════════════════════════════════════════╗' -ForegroundColor Green
Write-Host (Msg "finish_banner_1") -ForegroundColor Green
Write-Host '║                                                               ║' -ForegroundColor Green
Write-Host (Msg "finish_banner_2") -ForegroundColor Green
Write-Host '╚═══════════════════════════════════════════════════════════════╝' -ForegroundColor Green
Write-Host ''

