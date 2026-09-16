# Установка

## Инструкции по установке AI-Breadboard

### Системные требования

- **Python 3.12** или выше
- **Git**
- **pip** (диспетчер пакетов Python)
- 4 GB свободной оперативной памяти (для локального инференса моделей рекомендуется 16+ GB RAM / GPU)
- Доступ в интернет

### Быстрая автоматическая установка

#### Windows (PowerShell):
```powershell
git clone https://github.com/hypo69/AI-Breadboard.git
cd AI-Breadboard
.\install.ps1
```

#### Linux / macOS (Bash):
```bash
git clone https://github.com/hypo69/AI-Breadboard.git
cd AI-Breadboard
bash install.sh
```

Интерактивный установщик автоматически:
1. Проверит версию Python (3.12+).
2. Создаст изолированное виртуальное окружение `venv`.
3. Установит все необходимые зависимости из `requirements.txt`.
4. Сгенерирует локальные SSL-сертификаты для HTTPS/WSS.
5. Настроит CLI-команды в окружении.

### Ручная установка из репозитория

```powershell
git clone https://github.com/hypo69/AI-Breadboard.git
cd AI-Breadboard
python -m venv venv
.\venv\Scripts\Activate.ps1    # Для Linux/macOS: source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### Дополнительные инструменты анализа сети (Wireshark и TShark)

Для работы модуля анализа сетевого трафика и захвата пакетов (`src/network/tshark_wrapper.py`) требуется TShark:
- Отдельно TShark устанавливать не нужно — он входит в состав официального пакета Wireshark вместе с драйвером Npcap.
- **Установка через winget (рекомендуется для Windows):**
  ```powershell
  winget install --id WiresharkFoundation.Wireshark
  ```
- **Обычная установка через установщик:**
  Скачайте [Wireshark для Windows (x64 Installer)](https://www.wireshark.org/download.html) и оставьте настройки по умолчанию (включая Npcap).
- **Проверка установки:**
  В новом окне PowerShell выполните:
  ```powershell
  tshark --version
  ```
  Проверка доступности из Python:
  ```powershell
  python -c "import shutil; print(shutil.which('tshark'))"
  ```
  Ожидаемый путь: `C:\Program Files\Wireshark\tshark.exe`.

### Проверка установки и первый запуск

Чтобы убедиться, что установка прошла успешно и сервисы готовы к работе:

```powershell
# Запуск через PowerShell-лончер
.\run.ps1

# Или проверка статуса через CLI
assist status
```

### Следующие шаги

После успешной установки:
1. Перейдите в раздел [Конфигурация](configuration.md) и [Справочник `config.json`](config.md)
2. Настройте файл `.env` на основе `.env.example`
3. Ознакомьтесь с [Руководством по запуску (`RUN.md`)](RUN.md)
4. Изучите [примеры использования](usage-examples.md)

### Возникли проблемы?

Смотрите раздел [Решение проблем](troubleshooting.md) для решения частых ошибок.
