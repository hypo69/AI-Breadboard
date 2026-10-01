# 🧱 Windows Defender Firewall Manager

Модуль инспекции, настройки и управления профилями (Domain, Private, Public) и правилами фильтрации сетевого трафика Windows Defender Firewall (`netsh advfirewall`, HNetCfg COM API).

---

## 🚀 Возможности
- Мониторинг активности профилей (Domain, Private, Public) и действий по умолчанию (Inbound/Outbound)
- Перечисление входящих и исходящих правил фильтрации с протоколами и портами
- Добавление, включение/отключение и удаление правил
- SafeOps симуляция (Dry-Run) модификаций брандмауэра

---

## 📡 REST API Эндпоинты (`/api/firewall-manager`)
- `GET /api/firewall-manager/report` — сводный отчет брандмауэра
- `GET /api/firewall-manager/profiles` — состояние сетевых профилей
- `GET /api/firewall-manager/rules` — список правил (с фильтрацией `?direction=In`)
- `POST /api/firewall-manager/actions` — добавление или изменение правила

---

## 🖥️ Использование через CLI
```powershell
# Запуск TUI дашборда
py -m apps.windows.modules.firewall_manager

# Запуск REST сервера
py -m apps.windows.modules.firewall_manager --mode server --port 8126
```
