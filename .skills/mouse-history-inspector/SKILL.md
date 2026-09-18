---
name: mouse-history-inspector
description: Automated assistant skill for: Автоматизированная инспекция активных и ранее подключенных мышей и манипуляторов через PnP и реестр Windows.
---

# Аудит и история подключенных мышей (Mouse History Inspector)

## 🎯 Назначение (Purpose)
Автоматизированная инспекция активных и ранее подключенных мышей и манипуляторов через PnP и реестр Windows.

## 🚀 Триггеры и применение (When to Use & Triggers)
Используется при запросах пользователя о системном оборудовании, истории подключений и экспресс-диагностике в интерфейсе Test Computer (/tc) и консоли.

## ⚙️ Протокол выполнения (Execution Protocol)
1. Выполнить `Get-PnpDevice -Class Mouse`.
2. Извлечь свойства FriendlyName, InstanceId и Status.
3. Сопоставить VID с каталогом производителей.
