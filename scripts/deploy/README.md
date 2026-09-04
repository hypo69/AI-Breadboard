# Сценарии деплоя

Этот каталог содержит сценарий PowerShell для автоматизации создания репозитория на GitHub и регистрации проекта на Read the Docs.

Файл: create_and_register.ps1

Как использовать:

1) Убедитесь, что у вас установлен git и (рекомендовано) gh CLI:
   - gh: https://github.com/cli/cli

2) Для автоматической регистрации на Read the Docs задайте переменную окружения READTHEDOCS_API_TOKEN или передайте параметр -RtdToken.

3) Запуск (PowerShell):
   ./create_and_register.ps1 -RepoName AI-Breadboard

Параметры:
-RepoName  - имя репозитория (по умолчанию AI-Breadboard)
-Branch    - ветка для пуша (по умолчанию main)
-RemoteUrl - если gh отсутствует, можно дать URL удалённого репозитория
-RtdToken  - токен Read the Docs (если не задан, будет использован READTHEDOCS_API_TOKEN)

Внимание:
- Скрипт не хранит токены и не публикует их в репозитории.
- Если автоматическая регистрация на RTD не удалась, импортируйте проект вручную через веб-интерфейс Read the Docs.
