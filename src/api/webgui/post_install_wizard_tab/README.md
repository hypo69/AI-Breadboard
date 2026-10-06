# Вкладка Post-Install Wizard (Мастер настройки Windows)

**Путь:** `src/api/webgui/post_install_wizard_tab/`

## Описание
Вкладка **Post-Install Wizard** предоставляет интерактивный пошаговый мастер первичной настройки и оптимизации Windows после установки системы.

## Основные возможности
- Выбор готовых профилей оптимизации (Post-Install Baseline, Security Hardening, Developer Workstation).
- Выборочное или пакетное применение шагов конфигурации.
- Отображение статусов выполнения каждого шага и прав доступа.
- Интеграция с API `/api/system-control/profiles`.
