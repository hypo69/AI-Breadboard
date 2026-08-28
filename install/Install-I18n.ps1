<#
.SYNOPSIS
    Модуль интернационализации (I18N) мастера установки AI Breadboard.
.DESCRIPTION
    Содержит словари локализации (RU, EN, ES, HE) и функции форматирования сообщений и выбора языка.
#>

$Global:I18N = @{
    ru = @{
        lang_name             = "Русский (Russian)"
        select_lang_header    = "AI Breadboard — МАСТЕР УСТАНОВКИ"
        select_lang_prompt    = "Выберите язык установки / Select installation language:"
        lang_default_suffix   = "[По умолчанию]"
        lang_choice_prompt    = "Язык / Language [{0}]"
        lang_selected         = "-> Выбран язык: {0}"
        
        banner_title          = "              AI Breadboard — МАСТЕР УСТАНОВКИ                      "
        
        dir_step_title        = "[1/7] Выбор директории установки..."
        dir_notice_header     = "  ВАЖНОЕ ПРИМЕЧАНИЕ О ДИРЕКТОРИИ УСТАНОВКИ:"
        dir_stability_warn    = "  Поскольку проект AI Breadboard находится в активной разработке, для стабильной`n  работы, автоматических обновлений и корректной привязки внутренних и внешних`n  инструментов настоятельно рекомендуется использовать стандартную директорию."
        dir_opt_default       = "  [1] Стандартная директория (Рекомендуется): {0}"
        dir_opt_custom        = "  [2] Указать другой каталог вручную"
        dir_choice_prompt     = "  Ваш выбор [Enter = 1]"
        dir_enter_custom      = "  Введите полный путь к папке для установки"
        dir_selected          = "  -> Директория установки: {0}"
        
        repo_downloading      = "  Загрузка файлов репозитория в {0}..."
        repo_git_clone        = "  Клонирование репозитория через Git..."
        repo_zip_download     = "  Git не найден. Загрузка ZIP-архива репозитория с GitHub..."
        repo_unzipping        = "  Распаковка файлов проекта..."
        repo_ready            = "  [OK] Файлы проекта успешно подготовлены в {0}"
        
        step_1                = "[2/7] Снятие блокировки файлов Windows (Unblock-File)..."
        step_1_ok             = "    [OK] Файлы проекта разблокированы"
        
        step_2                = "[3/7] Проверка виртуального окружения (venv)..."
        step_2_existing       = "    [OK] venv уже существует: {0} ({1})"
        step_2_damaged        = "    [WARN] Существующий venv поврежден. Требуется пересоздание."
        step_2_err_launch     = "    [WARN] Ошибка запуска venv python: {0}"
        step_2_searching      = "    Поиск системного интерпретатора Python..."
        step_2_py_found       = "    [OK] Найден интерпретатор через Python Launcher: {0}"
        step_2_sys_found      = "    [OK] Найден системный интерпретатор: {0} ({1})"
        step_2_py_not_found   = "    [ERROR] Python не найден на вашей системе!"
        step_2_py_install_tip = "    Пожалуйста, установите Python 3.12 или 3.13 с https://www.python.org/downloads/`n    При установке обязательно отметьте галочку `"Add python.exe to PATH`"."
        step_2_header         = "[3/7] Настройка виртуального окружения Python..."
        step_2_module_missing = "    [ERROR] Модуль Install-Venv.ps1 не найден!"
        step_2_error          = "    [ERROR] Ошибка при создании виртуального окружения!"
        step_2_failed         = "    [ERROR] Виртуальное окружение не было создано корректно!"
        step_2_remove_old     = "    Удаление старого каталога venv..."
        step_2_creating       = "    Создание виртуального окружения в {0}..."
        step_2_create_fail    = "    [ERROR] Не удалось создать виртуальное окружение."
        step_2_created_ok     = "    [OK] Виртуальное окружение успешно создано"
        
        step_3                = "[4/7] Обновление pip и базовых утилит сборки..."
        step_3_ok             = "    [OK] pip, setuptools, wheel обновлены"
        step_3_warn           = "    [WARN] Не удалось обновить pip (продолжаем установку)"
        
        step_4                = "[5/7] Установка зависимостей проекта..."
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
        
        step_5                = "[6/7] Проверка SSL-сертификатов..."
        step_5_found          = "    [OK] SSL-сертификаты найдены ({0})"
        step_5_not_found      = "    [INFO] SSL-сертификаты не найдены. Вызов мастера создания сертификатов..."
        step_5_missing_script = "    [WARN] Скрипт {0} не найден. Сервер будет запускаться без SSL."
        
        step_6                = "[7/7] Регистрация системных путей и команд assist..."
        step_6_env_ok         = "    [OK] Системная переменная AIBREADBOARD_DIR установлена: {0}"
        step_6_path_ok        = "    [OK] Пути добавлены в переменную среды PATH пользователя"
        step_6_prof_ok        = "    [OK] Функция assist зарегистрирована в профилях PowerShell"
        
        step_7                = "Финальная проверка установленного окружения..."
        step_7_ok             = "    [OK] Основные библиотеки успешно инициализированы"
        step_7_py_path        = "    [OK] Python интерпретатор: {0}"
        step_7_warn           = "    [WARN] Результат проверки: {0}"
        
        finish_banner_1       = "║         УСТАНОВКА AI Breadboard УСПЕШНО ЗАВЕРШЕНА!                ║"
        finish_banner_2       = "║  Запуск сервера:  assist start  или  ./run.ps1                ║"
        finish_hint           = "  Глобальные команды: assist start | assist status | assist providers | assist stop"
    }
    en = @{
        lang_name             = "English"
        select_lang_header    = "AI Breadboard — INSTALLATION WIZARD"
        select_lang_prompt    = "Select installation language / Выберите язык установки:"
        lang_default_suffix   = "[Default]"
        lang_choice_prompt    = "Language / Язык [{0}]"
        lang_selected         = "-> Selected language: {0}"
        
        banner_title          = "              AI Breadboard — INSTALLATION WIZARD                   "
        
        dir_step_title        = "[1/7] Selecting installation directory..."
        dir_notice_header     = "  IMPORTANT NOTE ABOUT INSTALLATION DIRECTORY:"
        dir_stability_warn    = "  Since AI Breadboard is under active development, to ensure stability,`n  smooth automatic updates, and proper tool binding, it is strongly`n  recommended to use the default installation directory."
        dir_opt_default       = "  [1] Default directory (Recommended): {0}"
        dir_opt_custom        = "  [2] Specify custom directory manually"
        dir_choice_prompt     = "  Your choice [Enter = 1]"
        dir_enter_custom      = "  Enter full destination folder path"
        dir_selected          = "  -> Installation directory: {0}"
        
        repo_downloading      = "  Downloading repository files to {0}..."
        repo_git_clone        = "  Cloning repository with Git..."
        repo_zip_download     = "  Git not found. Downloading ZIP archive from GitHub..."
        repo_unzipping        = "  Extracting project files..."
        repo_ready            = "  [OK] Project files ready in {0}"
        
        step_1                = "[2/7] Unblocking Windows files (Unblock-File)..."
        step_1_ok             = "    [OK] Project files unblocked"
        
        step_2                = "[3/7] Checking virtual environment (venv)..."
        step_2_existing       = "    [OK] venv already exists: {0} ({1})"
        step_2_damaged        = "    [WARN] Existing venv is corrupted. Re-creation required."
        step_2_err_launch     = "    [WARN] Error launching venv python: {0}"
        step_2_searching      = "    Searching for system Python interpreter..."
        step_2_py_found       = "    [OK] Found Python interpreter via Python Launcher: {0}"
        step_2_sys_found      = "    [OK] Found system Python interpreter: {0} ({1})"
        step_2_py_not_found   = "    [ERROR] Python was not found on your system!"
        step_2_py_install_tip = "    Please install Python 3.12 or 3.13 from: https://www.python.org/downloads/`n    Make sure to check `"Add python.exe to PATH`" during installation."
        step_2_header         = "[3/7] Setting up Python virtual environment..."
        step_2_module_missing = "    [ERROR] Install-Venv.ps1 module not found!"
        step_2_error          = "    [ERROR] Error creating virtual environment!"
        step_2_failed         = "    [ERROR] Virtual environment was not created properly!"
        step_2_remove_old     = "    Removing old venv directory..."
        step_2_creating       = "    Creating virtual environment in {0}..."
        step_2_create_fail    = "    [ERROR] Failed to create virtual environment."
        step_2_created_ok     = "    [OK] Virtual environment created successfully"
        
        step_3                = "[4/7] Upgrading pip and build tools..."
        step_3_ok             = "    [OK] pip, setuptools, wheel upgraded"
        step_3_warn           = "    [WARN] Failed to upgrade pip (continuing installation)"
        
        step_4                = "[5/7] Installing project dependencies..."
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
        
        step_5                = "[6/7] Checking SSL certificates..."
        step_5_found          = "    [OK] SSL certificates found ({0})"
        step_5_not_found      = "    [INFO] SSL certificates not found. Invoking certificate wizard..."
        step_5_missing_script = "    [WARN] Script {0} not found. Server will run without SSL."
        
        step_6                = "[7/7] Registering system paths and assist commands..."
        step_6_env_ok         = "    [OK] Environment variable AIBREADBOARD_DIR set: {0}"
        step_6_path_ok        = "    [OK] Paths added to User PATH environment variable"
        step_6_prof_ok        = "    [OK] assist function registered in PowerShell profiles"
        
        step_7                = "Verifying installed environment..."
        step_7_ok             = "    [OK] Core libraries initialized successfully"
        step_7_py_path        = "    [OK] Python interpreter: {0}"
        step_7_warn           = "    [WARN] Verification result: {0}"
        
        finish_banner_1       = "║         AI Breadboard INSTALLATION COMPLETED SUCCESSFULLY!        ║"
        finish_banner_2       = "║  Start server:   assist start  or  ./run.ps1                  ║"
        finish_hint           = "  Global commands: assist start | assist status | assist providers | assist stop"
    }
    es = @{
        lang_name             = "Español (Spanish)"
        select_lang_header    = "AI Breadboard — ASISTENTE DE INSTALACIÓN"
        select_lang_prompt    = "Seleccione el idioma de instalación / Select language:"
        lang_default_suffix   = "[Predeterminado]"
        lang_choice_prompt    = "Idioma / Language [{0}]"
        lang_selected         = "-> Idioma seleccionado: {0}"
        
        banner_title          = "              AI Breadboard — ASISTENTE DE INSTALACIÓN              "
        
        dir_step_title        = "[1/7] Selección del directorio de instalación..."
        dir_notice_header     = "  NOTA IMPORTANTE SOBRE EL DIRECTORIO DE INSTALACIÓN:"
        dir_stability_warn    = "  Dado que AI Breadboard se encuentra en desarrollo activo, para garantizar`n  la estabilidad, actualizaciones automáticas y el correcto funcionamiento`n  de las herramientas, se recomienda encarecidamente usar la ruta predeterminada."
        dir_opt_default       = "  [1] Directorio predeterminado (Recomendado): {0}"
        dir_opt_custom        = "  [2] Especificar otro directorio manualmente"
        dir_choice_prompt     = "  Su elección [Enter = 1]"
        dir_enter_custom      = "  Introduzca la ruta completa de destino"
        dir_selected          = "  -> Directorio de instalación: {0}"
        
        repo_downloading      = "  Descargando archivos del repositorio en {0}..."
        repo_git_clone        = "  Clonando repositorio con Git..."
        repo_zip_download     = "  Git no encontrado. Descargando archivo ZIP de GitHub..."
        repo_unzipping        = "  Extrayendo archivos del proyecto..."
        repo_ready            = "  [OK] Archivos del proyecto listos en {0}"
        
        step_1                = "[2/7] Desbloqueo de archivos de Windows (Unblock-File)..."
        step_1_ok             = "    [OK] Archivos del proyecto desbloqueados"
        
        step_2                = "[3/7] Comprobando entorno virtual (venv)..."
        step_2_existing       = "    [OK] venv ya existe: {0} ({1})"
        step_2_damaged        = "    [WARN] El venv existente está dañado. Se requiere recreación."
        step_2_err_launch     = "    [WARN] Error al iniciar venv python: {0}"
        step_2_searching      = "    Buscando intérprete Python en el sistema..."
        step_2_py_found       = "    [OK] Intérprete Python encontrado vía Python Launcher: {0}"
        step_2_sys_found      = "    [OK] Intérprete Python del sistema encontrado: {0} ({1})"
        step_2_py_not_found   = "    [ERROR] ¡Python no fue encontrado en su sistema!"
        step_2_py_install_tip = "    Por favor instale Python 3.12 o 3.13 desde: https://www.python.org/downloads/`n    Asegúrese de marcar la casilla `"Add python.exe to PATH`" durante la instalación."
        step_2_remove_old     = "    Eliminando directorio venv antiguo..."
        step_2_creating       = "    Creando entorno virtual en {0}..."
        step_2_create_fail    = "    [ERROR] Error al crear el entorno virtual."
        step_2_created_ok     = "    [OK] Entorno virtual creado exitosamente"
        
        step_3                = "[4/7] Actualizando pip y herramientas de compilación..."
        step_3_ok             = "    [OK] pip, setuptools, wheel actualizados"
        step_3_warn           = "    [WARN] Error al actualizar pip (continuando instalación)"
        
        step_4                = "[5/7] Instalando dependencias del proyecto..."
        step_4_menu_title     = "    Seleccione la opción de instalación de dependencias:"
        step_4_opt_1          = "      [1] Instalación completa (Core + AI + Utils) — RECOMENDADO"
        step_4_opt_2          = "      [2] Solo servidor básico (Core)"
        step_4_opt_3          = "      [3] Servidor + Módulos AI (Core + AI)"
        step_4_opt_4          = "      [4] Instalación completa + Tests y Docs (Dev)"
        step_4_opt_5          = "      [5] Omitir instalación de dependencias"
        step_4_choice_prompt  = "    Su elección [predeterminado 1]"
        step_4_installing_all = "    Instalando dependencias principales desde requirements.txt..."
        step_4_installing_core= "    Instalando dependencias Core..."
        step_4_installing_ai  = "    Instalando dependencias Core + AI..."
        step_4_installing_dev = "    Instalando conjunto completo + Dev..."
        step_4_skipped        = "    Instalación de dependencias omitida por el usuario."
        step_4_default_msg    = "    Opción predeterminada seleccionada: instalación completa..."
        step_4_pip_error      = "    [ERROR] Ocurrieron errores durante la instalación con pip."
        
        step_5                = "[6/7] Comprobando certificados SSL..."
        step_5_found          = "    [OK] Certificados SSL encontrados ({0})"
        step_5_not_found      = "    [INFO] Certificados SSL no encontrados. Iniciando asistente..."
        step_5_missing_script = "    [WARN] Script {0} no encontrado. El servidor se ejecutará sin SSL."
        
        step_6                = "[7/7] Registrando rutas del sistema и comandos assist..."
        step_6_env_ok         = "    [OK] Variable de entorno AIBREADBOARD_DIR establecida: {0}"
        step_6_path_ok        = "    [OK] Rutas añadidas a la variable de entorno PATH"
        step_6_prof_ok        = "    [OK] Función assist registrada en perfiles PowerShell"
        
        step_7                = "Verificando el entorno instalado..."
        step_7_ok             = "    [OK] Librerías principales inicializadas correctamente"
        step_7_py_path        = "    [OK] Intérprete Python: {0}"
        step_7_warn           = "    [WARN] Resultado de la verificación: {0}"
        
        finish_banner_1       = "║        ¡INSTALACIÓN DE AI Breadboard COMPLETADA CON ÉXITO!        ║"
        finish_banner_2       = "║  Iniciar servidor: assist start  o  ./run.ps1                 ║"
        finish_hint           = "  Comandos globales: assist start | assist status | assist providers | assist stop"
    }
    he = @{
        lang_name             = "עברית (Hebrew)"
        select_lang_header    = "AI Breadboard — אשף ההתקנה"
        select_lang_prompt    = "בחר שפת התקנה / Select installation language:"
        lang_default_suffix   = "[ברירת מחדל]"
        lang_choice_prompt    = "שפה / Language [{0}]"
        lang_selected         = "-> שפה שנבחרה: {0}"
        
        banner_title          = "              AI Breadboard — אשף ההתקנה                             "
        
        dir_step_title        = "[1/7] בחירת תיקיית התקנה..."
        dir_notice_header     = "  הערה חשובה לגבי תיקיית ההתקנה:"
        dir_stability_warn    = "  מכיוון ש-AI Breadboard נמצא בפיתוח פעיל, למען יציבות מרבית,`n  עדכונים אוטומטיים חלקים וקישור מדויק של כלי המערכת,`n  מומלץ מאוד להשתמש בתיקיית ברירת המחדל."
        dir_opt_default       = "  [1] ספריית ברירת מחדל (מומלץ): {0}"
        dir_opt_custom        = "  [2] ציין תיקייה אחרת באופן ידני"
        dir_choice_prompt     = "  הבחירה שלך [Enter = 1]"
        dir_enter_custom      = "  הזן נתיב מלא לתיקיית ההתקנה"
        dir_selected          = "  -> ספריית התקנה: {0}"
        
        repo_downloading      = "  מוריד קבצי פרויקט אל {0}..."
        repo_git_clone        = "  משכפל מאגר באמצעות Git..."
        repo_zip_download     = "  Git לא נמצא. מוריד ארכיון ZIP מ-GitHub..."
        repo_unzipping        = "  מחלץ קבצי פרויקט..."
        repo_ready            = "  [OK] קבצי הפרויקט מוכנים ב-{0}"
        
        step_1                = "[2/7] שחרור חסימת קבצים של Windows (Unblock-File)..."
        step_1_ok             = "    [OK] חסימת קבצי הפרויקט הוסרה בהצלחה"
        
        step_2                = "[3/7] בדיקת סביבה וירטואלית (venv)..."
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
        
        step_3                = "[4/7] מעדכן את pip וכלי בנייה..."
        step_3_ok             = "    [OK] pip, setuptools, wheel עודכנו בהצלחה"
        step_3_warn           = "    [WARN] עדכון pip נכשל (ממשיך בהתקנה)"
        
        step_4                = "[5/7] התקנת תלויות הפרויקט..."
        step_4_menu_title     = "    בחר אפשרות התקנת תלויות:"
        step_4_opt_1          = "      [1] התקנה מלאה (Core + AI + Utils) — מומלץ"
        step_4_opt_2          = "      [2] שרת בסיסי בלבד (Core)"
        step_4_opt_3          = "      [3] שרת ומודולי AI (Core + AI)"
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
        
        step_5                = "[6/7] בדיקת תעודות SSL..."
        step_5_found          = "    [OK] תעודות SSL נמצאו ({0})"
        step_5_not_found      = "    [INFO] תעודות SSL לא נמצאו. מפעיל אשף יצירת תעודות..."
        step_5_missing_script = "    [WARN] הסקריפט {0} לא נמצא. השרת יפעל ללא SSL."
        
        step_6                = "[7/7] רישום נתיבי מערכת ופקודות assist..."
        step_6_env_ok         = "    [OK] משתנה סביבה AIBREADBOARD_DIR הוגדר: {0}"
        step_6_path_ok        = "    [OK] הנתיבים נוספו למשתנה הסביבה PATH של המשתמש"
        step_6_prof_ok        = "    [OK] הפונקציה assist נרשמה בפרופילי PowerShell"
        
        step_7                = "אימות סביבת העבודה המותקנת..."
        step_7_ok             = "    [OK] ספריות הליבה אותחלו בהצלחה"
        step_7_py_path        = "    [OK] מפרש Python: {0}"
        step_7_warn           = "    [WARN] תוצאת הבדיקה: {0}"
        
        finish_banner_1       = "║         התקנת AI Breadboard הושלמה בהצלחה!                        ║"
        finish_banner_2       = "║  הפעלת השרת:     assist start  או  ./run.ps1                  ║"
        finish_hint           = "  פקודות גלובליות: assist start | assist status | assist providers | assist stop"
    }
}

$Global:CurrentLang = "ru"

function global:Msg {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Key,
        [object[]]$Args_ = @()
    )
    $dict = $Global:I18N[$Global:CurrentLang]
    if (-not $dict) { $dict = $Global:I18N["en"] }
    $template = $dict[$Key]
    if (-not $template) {
        $template = $Global:I18N["en"][$Key]
        if (-not $template) { return $Key }
    }
    if ($Args_ -and $Args_.Count -gt 0) {
        return [string]::Format($template, $Args_)
    }
    return $template
}

function global:Select-InstallerLanguage {
    param([string]$DefaultLang = "en")
    
    $systemLangs = @()
    try {
        $cultureName = (Get-Culture).TwoLetterISOLanguageName.ToLower()
        if ($cultureName) { $systemLangs += $cultureName }
        $uiCultureName = [System.Globalization.CultureInfo]::CurrentUICulture.TwoLetterISOLanguageName.ToLower()
        if ($uiCultureName -and ($systemLangs -notcontains $uiCultureName)) { $systemLangs += $uiCultureName }
    } catch {}
    try {
        if (Get-Command Get-WinUserLanguageList -ErrorAction SilentlyContinue) {
            $userLangs = Get-WinUserLanguageList -ErrorAction SilentlyContinue
            if ($userLangs) {
                foreach ($ul in $userLangs) {
                    $c = $ul.LanguageTag.Split('-')[0].ToLower()
                    if ($c -and ($systemLangs -notcontains $c)) { $systemLangs += $c }
                }
            }
        }
    } catch {}

    $languages = @("en", "ru", "es", "he")
    $defaultIndex = [array]::IndexOf($languages, $DefaultLang) + 1
    if ($defaultIndex -le 0) { $defaultIndex = 1 }

    Write-Host ""
    Write-Host "Select installation wizard language:" -ForegroundColor Cyan
    Write-Host ""

    for ($i = 0; $i -lt $languages.Length; $i++) {
        $code = $languages[$i]
        $name = $Global:I18N[$code]["lang_name"]
        $num = $i + 1
        $isDefault = ($num -eq $defaultIndex)
        $isSystem = ($systemLangs -contains $code)

        if ($isDefault) {
            Write-Host "    [$num] $name ($code) [Default]" -ForegroundColor Green
        } elseif ($isSystem) {
            Write-Host "    [$num] $name ($code) [System]" -ForegroundColor Cyan
        } else {
            Write-Host "    [$num] $name ($code)" -ForegroundColor Gray
        }
    }
    Write-Host ""

    $userChoice = Read-Host "  Language [$defaultIndex]"
    $userChoice = $userChoice.Trim()
    if (-not $userChoice) { $userChoice = [string]$defaultIndex }

    $chosenIndex = 0
    if ([int]::TryParse($userChoice, [ref]$chosenIndex) -and $chosenIndex -ge 1 -and $chosenIndex -le $languages.Length) {
        $Global:CurrentLang = $languages[$chosenIndex - 1]
    } else {
        $found = $false
        for ($i = 0; $i -lt $languages.Length; $i++) {
            if ($languages[$i] -ieq $userChoice) {
                $Global:CurrentLang = $languages[$i]
                $found = $true
                break
            }
        }
        if (-not $found) {
            $Global:CurrentLang = $languages[$defaultIndex - 1]
        }
    }

    Write-Host ""
    Write-Host (Msg "lang_selected" @($Global:I18N[$Global:CurrentLang]["lang_name"])) -ForegroundColor Green
    Write-Host ""
}
