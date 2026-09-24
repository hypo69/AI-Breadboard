# 🛡️ Windows Backup, Libraries & File History Manager (`apps/windows/backup_manager`)

**Status:** ✅ Active  
**Author:** hypo69  
**Version:** 1.0.0  

Комплексное нативное приложение операционной системы Windows для:
1. **Управления системными библиотеками Windows (`.library-ms`):** Создание виртуальных коллекций, объединение локальных папок с разных дисков, проверка доступности каталогов.
2. **Службы и конфигурации Истории файлов (`File History / fhsvc`):** Мониторинг фоновой службы, проверка `Config.xml`, принудительный запуск циклов бэкапа (`fhexec -f`).
3. **Аудита хранилища резервных копий:** Сканирование версий файлов `FileHistory\<User>\<PC>\Data`, учет объемов и контроль дискового пространства.
4. **Теневых копий томов (VSS):** Инспекция теневых моментальных снимков томов.
5. **Аудита и переноса пользовательских директорий:** Подсчет объемов (Рабочий стол, Документы, Загрузки, Изображения, Музыка, Видео), проверка наличия вторичных дисков с достаточным местом и безопасный перенос папок с обновлением реестра `User Shell Folders` и библиотек Windows.

---

## 🚀 Запуск из терминала (Rich TUI)

```powershell
python -m apps.windows.backup_manager
```

---

## 🌐 FastAPI REST API Endpoints (`/api/v1/windows-backup`)

| Метод | Эндпоинт | Описание |
|---|---|---|
| `GET` | `/api/v1/windows-backup/health` | Сводный отчет готовности защиты данных (Health Score 0-100) и рекомендации |
| `GET` | `/api/v1/windows-backup/libraries` | Список всех библиотек Windows и включенных в них папок |
| `POST` | `/api/v1/windows-backup/libraries` | Создание новой библиотеки Windows (`.library-ms`) |
| `POST` | `/api/v1/windows-backup/libraries/{name}/folders` | Добавление физической папки в существующую библиотеку |
| `GET` | `/api/v1/windows-backup/file-history/status` | Статус службы `fhsvc` и конфигурации пользователя |
| `POST` | `/api/v1/windows-backup/file-history/trigger` | Принудительный запуск цикла архивации (`fhexec -f`) |
| `GET` | `/api/v1/windows-backup/storage/audit` | Аудит версий и занятого объема в целевом хранилище |
| `GET` | `/api/v1/windows-backup/vss/snapshots` | Список теневых копий томов VSS |
| `GET` | `/api/v1/windows-backup/user-folders/overview` | Подсчет объемов пользовательских папок и аудит свободного места на дисках |
| `POST` | `/api/v1/windows-backup/user-folders/relocate` | Перенос пользовательской директории на выбранный вторичный диск |