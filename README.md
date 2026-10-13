# SofiBirdPlush

Сайт: https://artdearthouse.github.io/sofibirdsofi/

Статическая копия опубликованного https://softbirdsofi.tilda.ws/ со стилями, JavaScript, изображениями и шрифтами. Блок «создано в Tilda» удалён.

Файлы сайта находятся в `site/`. GitHub Actions публикует эту папку на GitHub Pages при каждом push в `main`; также доступен ручной запуск workflow.

Локальный просмотр:

```sh
python3 -m http.server 8000 --directory site
```

Исходные страницы `/`, `/fur`, `/ceramic` и `/prints` перенесены. Внешние ссылки на соцсети и сервис пожертвований сохранены. Серверные сервисы Tilda не переносятся на статический хостинг.

`scripts/mirror.py` позволяет повторить скачивание оригинала (Python и `beautifulsoup4`). Он перезаписывает сайт; локальные изменения перед запуском нужно сохранить. Соответствие исходных URL и локальных ресурсов записано в `scripts/asset-manifest.json`.
