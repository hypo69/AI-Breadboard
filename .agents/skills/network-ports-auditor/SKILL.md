---
name: network-ports-auditor
description: Automated assistant skill for: Проверка активных сетевых адаптеров, прослушиваемых портов TCP/UDP и соединений.
---

# Аудит сетевых интерфейсов и портов (Network Ports Auditor)

## 🎯 Назначение (Purpose)
Проверка активных сетевых адаптеров, прослушиваемых портов TCP/UDP и соединений.

## 🚀 Триггеры и применение (When to Use & Triggers)
Используется при запросах пользователя о системном оборудовании, истории подключений и экспресс-диагностике в интерфейсе Test Computer (/tc) и консоли.

## ⚙️ Протокол выполнения (Execution Protocol)
1. Запустить NetworkCollector из apps/windows/core/modules.
2. Собрать список открытых портов и адаптеров.
