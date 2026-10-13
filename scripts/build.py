"""Build the static site from editable JSON and shared Jinja2 templates."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from urllib.parse import urlparse

from bs4 import BeautifulSoup
from jinja2 import Environment, FileSystemLoader, StrictUndefined, TemplateError, select_autoescape
from markupsafe import Markup

SITE = Path(__file__).resolve().parents[1] / 'site'
PAGES = {'home': 'index.html', 'fur': 'fur/index.html', 'ceramic': 'ceramic/index.html', 'prints': 'prints/index.html'}


def load_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f'{path}: {error}') from error
    if not isinstance(value, dict):
        raise ValueError(f'{path}: expected a JSON object')
    return value


def require_text(value: object, context: str, *, empty: bool = False) -> str:
    if not isinstance(value, str) or (not empty and not value.strip()):
        raise ValueError(f'{context}: expected {"a string" if empty else "a non-empty string"}')
    return value


def resolve_link(value: str, common: dict, prefix: str = '') -> str:
    require_text(value, 'URL')
    if value.startswith('@'):
        key = value[1:]
        if key not in common['links']:
            raise ValueError(f'URL: unknown shared link {value}')
        value = common['links'][key]
    parsed = urlparse(value)
    if any(ord(c) < 32 or c.isspace() for c in value) or '\\' in value:
        raise ValueError(f'URL: invalid characters in {value!r}')
    if parsed.scheme:
        if parsed.scheme not in {'https', 'http', 'mailto', 'tel'}:
            raise ValueError(f'URL: unsupported scheme in {value!r}')
        if parsed.scheme in {'https', 'http'} and not parsed.netloc:
            raise ValueError(f'URL: missing host in {value!r}')
        return value
    if value.startswith(('//', '/')) or '..' in Path(parsed.path).parts:
        raise ValueError(f'URL: use site-relative paths, not {value!r}')
    return value if value.startswith('#') else prefix + value


def validate_image(image: object, site: Path, context: str) -> None:
    if not isinstance(image, dict):
        raise ValueError(f'{context}: expected an image object')
    for key in ('src', 'preview'):
        if key == 'preview' and key not in image:
            continue
        value = require_text(image.get(key), f'{context}.{key}')
        path = Path(value)
        if not value.startswith('assets/') or path.is_absolute() or '..' in path.parts or not (site / path).is_file():
            raise ValueError(f'{context}.{key}: missing or invalid image {value!r}')
    require_text(image.get('alt', ''), f'{context}.alt', empty=True)
    image.setdefault('preview', image['src'])
    image.setdefault('alt', '')


def render_rich(value: str, common: dict, prefix: str) -> Markup:
    """HTML fields are trusted local editorial content, with validated links."""
    require_text(value, 'HTML content', empty=True)
    soup = BeautifulSoup(value, 'html.parser')
    for tag in soup.find_all(True):
        if tag.name in {'script', 'iframe', 'object', 'embed'} or any(a.lower().startswith('on') for a in tag.attrs):
            raise ValueError('HTML content: executable content belongs in templates, not JSON')
        if tag.has_attr('href'):
            tag['href'] = resolve_link(tag['href'], common, prefix)
    return Markup(str(soup))


def validate_page(page: dict, site: Path, common: dict, name: str) -> None:
    require_text(page.get('title'), f'{name}.title')
    require_text(page.get('description'), f'{name}.description', empty=True)
    validate_image({'src': page.get('social_image')}, site, f'{name}.social_image')
    sections = page.get('sections')
    if not isinstance(sections, list) or not sections:
        raise ValueError(f'{name}.sections: expected a non-empty list')
    ids = set()
    for index, section in enumerate(sections):
        context = f'{name}.sections[{index}]'
        if not isinstance(section, dict):
            raise ValueError(f'{context}: expected an object')
        record_id = require_text(section.get('id'), f'{context}.id')
        if not re.fullmatch(r'[0-9]{1,16}', record_id):
            raise ValueError(f'{context}.id: expected 1–16 digits')
        if record_id in ids:
            raise ValueError(f'Duplicate record id {record_id} in {name}')
        ids.add(record_id)
        kind = section.get('type')
        if kind not in {'menu', 'about', 'product', 'gallery', 'section'}:
            raise ValueError(f'{context}.type: unknown section {kind!r}')
        if kind == 'menu':
            if not isinstance(section.get('links'), list):
                raise ValueError(f'{context}.links: expected a list')
            for link in section['links']:
                if not isinstance(link, dict):
                    raise ValueError(f'{context}.links: expected link objects')
                require_text(link.get('label'), f'{context}.link.label')
                resolve_link(link.get('href'), common)
        if kind == 'product':
            for key in ('title', 'price', 'currency'):
                require_text(section.get(key), f'{context}.{key}')
            section.setdefault('subtitle_html', '')
            section.setdefault('description_html', '')
            section.setdefault('space_top', 120)
            section.setdefault('button_color', '#ff623b')
            section.setdefault('description_size', 20)
            for key in ('subtitle_html', 'description_html'):
                render_rich(section[key], common, '')
            for key, minimum, maximum in [('space_top', 0, 500), ('description_size', 10, 48)]:
                value = section[key]
                if type(value) is not int or not minimum <= value <= maximum:
                    raise ValueError(f'{context}.{key}: expected integer from {minimum} to {maximum}')
            if not re.fullmatch(r'#[0-9a-fA-F]{6}', require_text(section['button_color'], f'{context}.button_color')):
                raise ValueError(f'{context}.button_color: expected #RRGGBB')
            button = section.get('button')
            if not isinstance(button, dict):
                raise ValueError(f'{context}.button: expected an object')
            require_text(button.get('label'), f'{context}.button.label')
            resolve_link(button.get('href'), common)
        if kind in {'product', 'gallery', 'section'}:
            images = section.get('images')
            if not isinstance(images, list) or (kind != 'section' and not images):
                raise ValueError(f'{context}.images: expected {"a" if kind == "section" else "a non-empty"} list')
            for i, image in enumerate(images):
                validate_image(image, site, f'{context}.images[{i}]')
        if kind == 'section':
            template = require_text(section.get('template'), f'{context}.template')
            if not template.startswith('sections/') or '..' in Path(template).parts or not template.endswith('.html') or not (site / 'templates' / template).is_file():
                raise ValueError(f'{context}.template: missing or invalid template {template!r}')
            if not isinstance(section.get('fields'), dict):
                raise ValueError(f'{context}.fields: expected an object')
            if 'anchor' in section and not re.fullmatch(r'[a-zA-Z][a-zA-Z0-9_-]*', require_text(section['anchor'], f'{context}.anchor')):
                raise ValueError(f'{context}.anchor: invalid anchor')
            for button in section.get('buttons', []):
                require_text(button.get('label'), f'{context}.button.label')
                resolve_link(button.get('href'), common)
            for value in section['fields'].values():
                render_rich(value, common, '')


def render_site(site_root: Path = SITE) -> dict[str, str]:
    """Validate every page, then render all outputs in memory before any writes."""
    site_root = Path(site_root)
    common = load_json(site_root / 'content/common.json')
    base_url = require_text(common.get('base_url'), 'common.base_url')
    if not base_url.startswith('https://') or not base_url.endswith('/') or not urlparse(base_url).netloc or urlparse(base_url).query or urlparse(base_url).fragment:
        raise ValueError('common.base_url: expected an HTTPS site URL ending in /')
    if not isinstance(common.get('links'), dict):
        raise ValueError('common.links: expected an object')
    for value in common['links'].values():
        if not isinstance(value, str) or value.startswith('@'):
            raise ValueError('common.links: expected literal URLs')
        resolve_link(value, common)
    about = common.get('about')
    if not isinstance(about, dict):
        raise ValueError('common.about: expected an object')
    for key in ('title', 'description'):
        require_text(about.get(key), f'common.about.{key}')
    render_rich(about.get('text_html'), common, '')
    validate_image(about.get('image'), site_root, 'common.about.image')
    pages = {name: load_json(site_root / f'content/{name}.json') for name in PAGES}
    for name, page in pages.items():
        validate_page(page, site_root, common, name)
    rendered = {}
    for name, output in PAGES.items():
        prefix = '' if name == 'home' else '../'
        env = Environment(loader=FileSystemLoader(site_root / 'templates'), autoescape=select_autoescape(['html']), undefined=StrictUndefined, keep_trailing_newline=True, trim_blocks=True, lstrip_blocks=True)
        env.filters['asset'] = lambda value: prefix + value
        env.filters['link_url'] = lambda value: resolve_link(value, common, prefix)
        env.filters['rich'] = lambda value: render_rich(value, common, prefix)
        page_url = base_url + ('' if name == 'home' else name + '/')
        result = env.get_template(f'pages/{name}.html').render(page=pages[name], common=common, asset_prefix=prefix, page_url=page_url, social_image_url=base_url + pages[name]['social_image'])
        rendered[output] = '<!-- Generated by scripts/build.py; edit site/content and site/templates. -->\n' + result
    return rendered


def build_site(site_root: Path = SITE, check: bool = False) -> None:
    rendered = render_site(site_root)
    stale = []
    for output, content in rendered.items():
        path = site_root / output
        if check:
            if not path.is_file() or path.read_text(encoding='utf-8') != content:
                stale.append(output)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding='utf-8')
    if stale:
        raise ValueError('Generated pages are out of date: ' + ', '.join(stale) + '. Run python3 scripts/build.py')
    print(f'{"Checked" if check else "Built"} {len(rendered)} static pages.')


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='fail if generated HTML is out of date; do not write')
    args = parser.parse_args()
    try:
        build_site(check=args.check)
    except (ValueError, OSError, TemplateError) as error:
        parser.exit(1, f'Build failed: {error}\n')


if __name__ == '__main__':
    main()
