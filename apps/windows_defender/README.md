# 🛡️ Microsoft Defender & AI Security Diagnostic Center (`apps/windows_defender`)

**Статус:** ✅ Активен  
**Версия:** 1.0.0  
**Автор:** hypo69  
**Порт:** `8113`  
**Префикс API:** `/api/v1/defender`

---

## 📋 Обзор

**Microsoft Defender & AI Security Diagnostic Center** — это специализированное автономное приложение и модуль платформы AI-Breadboard, предназначенный для углубленного мониторинга, аудита и управления штатным антивирусным движком Microsoft Defender Antivirus в среде Windows.

Вместо попыток дублировать функционал антивируса, приложение использует Microsoft Defender как высокоточный низкоуровневый сенсор, надстраивая над ним интеллектуальный уровень анализа, аудита политик Attack Surface Reduction (ASR), защиты от вымогателей (Controlled Folder Access), эвристической оценки опасных исключений, инспекции дерева процессов и корреляции событий безопасности.

---

## 🏛️ Ключевые возможности

1. **Проверка файлов и сканирование:**
   - Быстрое (`Quick`), Полное (`Full`), Выборочное (`Custom`) и Офлайн-сканирование (`Offline`).
   - Прямая интеграция с `MpCmdRun.exe` и PowerShell-командлетами Defender.
   - Обновление баз сигнатур и антивирусного движка.
2. **Мониторинг защиты в реальном времени:**
   - Состояние Real-Time Protection, Behavior Monitoring, IOAV (защита загрузок), On-Access scanning, AMSI Script scanning.
   - Мониторинг системных служб и процессов: `MsMpEng.exe`, `MpDefenderCoreService.exe`, `NisSrv.exe`, `MpCmdRun.exe`.
3. **Attack Surface Reduction (ASR):**
   - Полный каталог из 14+ ключевых правил ASR (GUID, описание, статус, рекомендации).
   - Защита от кражи учетных данных LSASS, блокировка дочерних процессов Office/Adobe Reader, блокировка обфусцированных скриптов и уязвимых драйверов (BYOVD).
4. **Controlled Folder Access (Ransomware Protection):**
   - Мониторинг защиты критических пользовательских директорий от несанкционированного изменения неизвестными процессами.
   - Управление списками защищенных папок и доверенных приложений.
5. **Аудит исключений (Exclusions Security Audit):**
   - Эвристический анализ путей, расширений и процессов, добавленных в исключения.
   - Автоматическое выявление критических рисков (исключение `C:\`, `C:\Windows`, `%TEMP%`, опасных расширений `.exe`/`.dll` и системных интерпретаторов `powershell.exe`/`cmd.exe`).
6. **Детекция Fileless и аномальных процессов:**
   - Инспекция дерева процессов на предмет подозрительных цепочек (Office $\to$ PowerShell/CMD/MSHTA).
   - Выявление признаков скрытого выполнения (`Invoke-Expression`, Base64-encoded payload, BITS/Certutil abuse, удаление теневых копий VSS).
7. **Журнал угроз и событий:**
   - Парсинг инцидентов и статуса нейтрализации (Cleaned/Quarantined/Blocked).
   - Сбор и корреляция событий канала `Microsoft-Windows-Windows Defender/Operational`.
8. **AI Correlation & Security Posture Score:**
   - Расчет единого индекса защищенности системы (0-100).
   - Формирование структурированных отчетов с приоритизацией критических уязвимостей и практических шагов по их устранению.

---

## 🚀 Запуск и использование

### Запуск CLI/TUI дашборда
```powershell
python -m apps.windows_defender
```

### Запуск сканирования
```powershell
# Быстрое сканирование
python -m apps.windows_defender --scan quick

# Полное сканирование
python -m apps.windows_defender --scan full

# Выборочное сканирование папки
python -m apps.windows_defender --scan custom --path "C:\Users\username\Downloads"

# Обновление баз сигнатур
python -m apps.windows_defender --update
```

### Запуск выделенного микросервиса API
```powershell
python -m apps.windows_defender --server --port 8113
```

---

## 📡 REST API Эндпоинты

| Метод | Путь | Описание |
|---|---|---|
| `GET` | `/api/v1/defender/status` | Комплексный статус Defender, версии баз и служб |
| `POST` | `/api/v1/defender/scan` | Запуск антивирусного сканирования |
| `POST` | `/api/v1/defender/update-signatures` | Обновление антивирусных баз сигнатур |
| `GET` | `/api/v1/defender/asr` | Аудит и статус правил Attack Surface Reduction |
| `GET` | `/api/v1/defender/cfa` | Сведения о Controlled Folder Access (Ransomware) |
| `GET` | `/api/v1/defender/exclusions` | Аудит исключений с эвристикой выявления рисков |
| `GET` | `/api/v1/defender/threats` | История обнаруженных угроз и инцидентов |
| `GET` | `/api/v1/defender/events` | События из журнала Windows Defender/Operational |
| `GET` | `/api/v1/defender/process-tree` | Анализ подозрительных цепочек процессов |
| `GET` | `/api/v1/defender/diagnostics` | Итоговый AI-отчет защищенности (Security Score) |
