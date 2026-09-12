# 🔑 Подготовка Google Service Account - Пошаговое руководство

## 📋 Требования

- Google аккаунт (e.cat.co.il@gmail.com или другой)
- Доступ в Google Cloud Console
- Основные навыки работы с браузером

## 🚀 Пошаговая инструкция

### Шаг 1: Открыть Google Cloud Console

1. Перейти на https://console.cloud.google.com/
2. Если это первый раз, принять условия
3. Выбрать существующий проект или создать новый

### Шаг 2: Создать новый проект (если нужно)

1. В верхней части нажать на селектор проектов
2. Нажать "Новый проект"
3. Ввести имя: `AI-Breadboard-Sync`
4. Нажать "Создать"
5. Дождаться создания проекта

### Шаг 3: Активировать Google Drive API

1. В поле поиска вверху введите: `Google Drive API`
2. Нажмите на результат "Google Drive API"
3. Нажмите кнопку "ВКЛЮЧИТЬ"
4. Дождитесь активации (может занять несколько секунд)

### Шаг 4: Создать Service Account

1. В левом меню найти "Service Accounts"
   - Путь: Меню ☰ → IAM и администратор → Service Accounts
2. Нажать кнопку "Создать сервис-аккаунт"
3. Заполнить форму:
   - **Идентификатор сервис-аккаунта**: `ai-breadboard-sync`
   - **Отображаемое имя**: `AI Breadboard Sync`
   - **Описание**: `Service account for syncing data to Google Drive`
4. Нажать "Создать и продолжить"

### Шаг 5: Предоставить роли

1. В разделе "Предоставить этому сервис-аккаунту доступ к проекту":
   - Нажать на селектор ролей
   - Выбрать роль: `Editor`
2. Нажать "Продолжить"
3. Нажать "Готово"

### Шаг 6: Создать JSON ключ

1. На странице Service Accounts найти созданный сервис-аккаунт
2. Нажать на сервис-аккаунт для открытия деталей
3. Перейти в таб "Ключи"
4. Нажать "Добавить ключ" → "Создать новый ключ"
5. Выбрать "JSON"
6. Нажать "Создать"

**Ключ автоматически скачается в файл**

### Шаг 7: Скопировать JSON ключ

1. Скопируйте скачанный JSON файл:
   - Имя файла будет похоже: `ai-breadboard-sync-XXXXXXX.json`

2. Переместите его в проект в папку `src/secrets/`:
   ```
   src/secrets/google_sa_account_service_account.json
   ```

3. **Важно**: Никогда не коммитьте этот файл в Git!
   - `.gitignore` уже содержит `src/secrets/`

### Шаг 8: Проверить содержимое файла

JSON файл должен содержать:
```json
{
  "type": "service_account",
  "project_id": "ai-breadboard-sync",
  "private_key_id": "...",
  "private_key": "...",
  "client_email": "ai-breadboard-sync@ai-breadboard-sync.iam.gserviceaccount.com",
  "client_id": "...",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  ...
}
```

### Шаг 9: Тест подключения

После копирования файла запустите:

```powershell
# Windows
.\sync.ps1 init

# Linux/Mac
python scripts/setup_google_drive_sync.py --init
```

Скрипт проверит подключение и создаст папку на Google Drive.

## ✅ Что произойдёт после инициализации

1. ✓ Проверка JSON ключа
2. ✓ Проверка подключения к Google Drive API
3. ✓ Создание папки `AI-Breadboard-Sync` в вашем Google Drive
4. ✓ Готовность к синхронизации

## 🔗 Доступ к папке синхронизации

После создания папка будет доступна по ссылке:
```
https://drive.google.com/drive/folders/[FOLDER_ID]
```

Folder ID можно получить командой:
```powershell
.\sync.ps1 status
```

## 🔒 Безопасность

### ✅ Рекомендации

1. **JSON ключ**:
   - Храните в безопасности
   - Не делитесь с кем-либо
   - Не коммитьте в репозиторий

2. **Права доступа**:
   - Сервис-аккаунт имеет роль "Editor" только для своего проекта
   - Используйте отдельные проекты для разработки и production

3. **Ротация ключей**:
   - Периодически создавайте новые ключи
   - Удаляйте старые ключи

## 🐛 Решение проблем

### "Ошибка: Google Drive API не активирована"

**Решение**:
1. Убедитесь, что в Google Cloud Console активирована Google Drive API
2. Попробуйте ещё раз через несколько минут

### "Ошибка: Нет прав доступа"

**Решение**:
1. Проверьте, что сервис-аккаунту предоставлена роль "Editor"
2. Убедитесь, что используется правильный JSON ключ

### "JSON ключ не найден"

**Решение**:
1. Убедитесь, что файл находится в: `src/secrets/google_sa_account_service_account.json`
2. Проверьте имя файла (должно быть точно как выше)

## 📞 Альтернативные способы

### Использование существующего Google Drive

Если у вас уже есть папка на Google Drive, которую вы хотите использовать:

1. Создайте в ней подпапку `AI-Breadboard-Sync`
2. Получите ID этой папки
3. Отредактируйте конфиг (если нужно)

### Использование Google Workspace Admin

Если вы администратор Google Workspace:

1. Создайте сервис-аккаунт в Admin Console
2. Используйте следующие права доступа
3. Более строгие правила безопасности

## 🎯 Следующие шаги

После подготовки Google сервис-аккаунта:

1. ✅ Установить зависимости: `pip install -r req/sync_requirements.txt`
2. ✅ Инициализировать синхронизацию: `.\sync.ps1 init`
3. ✅ Синхронизировать данные: `.\sync.ps1 sync`

Смотрите [GOOGLE_DRIVE_SYNC_SETUP.md](GOOGLE_DRIVE_SYNC_SETUP.md) для полной инструкции.

## 📚 Ссылки

- [Google Cloud Console](https://console.cloud.google.com/)
- [Google Drive API Docs](https://developers.google.com/drive/api)
- [Service Accounts Documentation](https://cloud.google.com/iam/docs/service-accounts)

---

**Готово!** Теперь вы готовы использовать Google Drive Sync 🎉
