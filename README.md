# SofiBirdPlush

Сайт: https://artdearthouse.github.io/sofibirdsofi/

Статический сайт с дизайном, перенесённым из Tilda. Тексты, товары и фотографии редактируются в JSON, общая разметка — в шаблонах Jinja2. Готовые страницы находятся в `site/`; серверная часть не требуется.

## Начать редактирование

Нужны Python 3.10+ и Node.js 22+ (для проверки JavaScript).

```sh
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
python3 scripts/build.py
python3 -m http.server 8000 --directory site
```

Откройте http://localhost:8000/. После изменения данных или шаблонов повторите `python3 scripts/build.py` и обновите страницу в браузере. Сервер перезапускать не нужно.

## Где редактировать

| Что изменить | Файл |
| --- | --- |
| Главная, доставка, заказ игрушки, каталог и галерея | `site/content/home.json` |
| Плюшевые игрушки | `site/content/fur.json` |
| Керамика | `site/content/ceramic.json` |
| Открытки, стикеры и постеры | `site/content/prints.json` |
| Соцсети, контакт для заказа, пожертвования и блок об авторе | `site/content/common.json` |
| Общая разметка страницы | `site/templates/base.html` |
| Меню, карточки и галереи | `site/templates/components/` |
| Внешний вид карточек и пользовательские стили | `site/assets/site.css` |

Пошаговые примеры: [инструкция по редактированию](docs/editing.md).

## Проверка и публикация

```sh
python3 -m unittest discover -s tests -v
python3 scripts/build.py
python3 scripts/build.py --check
python3 scripts/verify.py
```

Перед публикацией проверьте главную, `/fur/`, `/ceramic/`, `/prints/`, меню и галереи на компьютере и телефоне. Закоммитьте изменения, включая сгенерированные HTML, и выполните `git push origin main`.

Workflow `.github/workflows/pages.yml` устанавливает зависимости, запускает тесты, собирает сайт и проверяет файлы перед публикацией. В Pages отправляются только готовые страницы и `assets/`; JSON, шаблоны и документация не публикуются. Pull request проходит те же проверки без деплоя. Также доступен ручной запуск workflow.

```sh
gh run list --workflow pages.yml --limit 1
gh run watch <ID> --exit-status
```

## Ресурсы оригинала

Локальные библиотеки Tilda сохранены для совместимости меню, галерей и увеличения изображений. Файлы поставщика в `site/assets/` не следует править; собственные изменения вносятся в `site.css` и шаблоны. Соответствие исходных URL ресурсам записано в `scripts/asset-manifest.json`.

`scripts/mirror.py` повторно скачивает оригинал https://softbirdsofi.tilda.ws/ и **перезаписывает готовый сайт**. Запускайте его только по явному запросу обновить копию из оригинала. Он не обновляет новые JSON и шаблоны: изменения оригинала нужно отдельно перенести в исходники. Блок `#tildacopy` не возвращаем. Серверные сервисы Tilda на GitHub Pages не работают.
