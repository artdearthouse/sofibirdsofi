# Публикация сайта

- Статический сайт находится в `site/`. Редактируйте HTML и ресурсы там.
- Для локального просмотра: `python3 -m http.server 8000 --directory site`.
- Проверка файлов перед push: `python3 scripts/verify.py` (Python, `beautifulsoup4` и Node.js).
- Перед публикацией проверьте главную, `ceramic/`, `prints/`, меню и галереи; не возвращайте блок `#tildacopy`. Исходная `/fur` вернула HTTP 410 при переносе: пока ссылка ведёт на оригинал.
- Публикация: закоммитьте изменения и выполните `git push origin main`. Workflow `.github/workflows/pages.yml` автоматически выкладывает `site/` на GitHub Pages.
- Проверка публикации: `gh run list --workflow pages.yml --limit 1`, затем `gh run watch <ID> --exit-status`.
- Адрес: https://artdearthouse.github.io/sofibirdsofi/
- `scripts/mirror.py` повторно скачивает оригинал Tilda (нужен `beautifulsoup4`) и перезаписывает локальную копию. Запускайте его только при явном запросе обновить копию из оригинала.
