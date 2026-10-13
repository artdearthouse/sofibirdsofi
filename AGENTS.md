# Редактирование и публикация сайта

- Исходники находятся в `site/`: содержимое в `site/content/*.json`, разметка в `site/templates/`, ресурсы в `site/assets/`.
- Готовые `site/index.html` и `site/*/index.html` генерируются. Правьте данные и шаблоны, затем запускайте `python3 scripts/build.py`; не редактируйте готовые страницы вручную.
- Общие контакты и блок об авторе задаются один раз в `site/content/common.json`. Собственные стили — `site/assets/site.css`; библиотеки Tilda с хешами в именах не изменяйте.
- Инструкция с примерами товаров и фотографий: `docs/editing.md`.

## Локальный просмотр

Команды выполняются из корня репозитория. Нужны Python 3.10+ и Node.js 22+.

Первый запуск:

```sh
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
python3 scripts/build.py
python3 -m http.server 8000 --directory site
```

При следующих запусках активируйте `.venv`, выполните сборку и запустите сервер. Откройте http://localhost:8000/; каталоги доступны по `/fur/`, `/ceramic/`, `/prints/`.

После правки данных или шаблонов запустите `python3 scripts/build.py` в другом терминале и обновите страницу. Сервер перезапускать не нужно. После правки CSS достаточно обновить страницу. Остановка сервера — Ctrl+C.

## Проверка и публикация

- Перед push: `python3 -m unittest discover -s tests -v`, `python3 scripts/build.py`, `python3 scripts/build.py --check`, `python3 scripts/verify.py`.
- Перед публикацией проверьте главную, `fur/`, `ceramic/`, `prints/`, меню и галереи при широком и узком окне; не возвращайте блок `#tildacopy`.
- Закоммитьте изменения, включая сгенерированные HTML, и выполните `git push origin main`. Workflow `.github/workflows/pages.yml` собирает и проверяет сайт перед публикацией.
- В Pages публикуется артефакт из готовых HTML и ресурсов; данные и шаблоны не публикуются. `scripts/package.py --output <новая пустая папка>` формирует этот артефакт.
- Проверка публикации: `gh run list --workflow pages.yml --limit 1`, затем `gh run watch <ID> --exit-status`.
- Адрес: https://artdearthouse.github.io/sofibirdsofi/
- `scripts/mirror.py` повторно скачивает оригинал Tilda и перезаписывает готовый сайт. Запускайте его только при явном запросе обновить копию из оригинала. Он не обновляет JSON и шаблоны; изменения оригинала переносите в исходники отдельно.
