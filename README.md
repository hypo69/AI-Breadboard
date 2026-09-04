# AI-Breadboard

Этот репозиторий готов для публикации документации только на Read the Docs.

Что сделано в репозитории:
- Удалён дублирующий файл `.readthedocs.yaml`. Оставлен `.readthedocs.yml` как канонический файл конфигурации Read the Docs.
- Конфигурация MkDocs (`mkdocs.yml`) и зависимости для документации (`docs-requirements.txt`) уже присутствуют.

Как создать репозиторий на GitHub и запушить локально:
1) Создайте репозиторий на GitHub с именем `AI-Breadboard` или используйте GitHub CLI:
   - gh repo create AI-Breadboard --public --source=. --remote=origin --push
   или стандартно:
   - git remote add origin git@github.com:<ваш-пользователь>/AI-Breadboard.git
   - git branch -M main
   - git push -u origin main

Регистрация проекта на Read the Docs:
1) Войдите на https://readthedocs.org/ и перейдите в Import a Project.
2) Выберите GitHub как поставщик, предоставьте доступ и выберите репозиторий `AI-Breadboard`.
3) В настройках проекта убедитесь, что:
   - Файл конфигурации: `.readthedocs.yml` (файл уже есть в корне репозитория).
   - Requirements: `docs-requirements.txt` (Read the Docs установит зависимости).
   - Branch: `main` (или нужная вам ветка).
4) Сохраните и нажмите "Build" для первого билда. Webhook для автоматических билдов создаётся Read the Docs автоматически при интеграции с GitHub.

Примечания и ограничения:
- Я не имею доступа для создания репозитория на GitHub или для регистрации проекта в Read the Docs — эти шаги должен выполнить вы или CI с доступом.
- GitHub Actions в репозитории только проверяют сборку документации и не публикуют сайт. Read the Docs будет единственной платформой публикации согласно вашим требованиям.

Если хотите, я могу подготовить дополнительные файлы (например, шаблон для .github/workflows, файл CNAME и т.д.) перед тем, как вы запушите. Напишите конкретно, что добавить.