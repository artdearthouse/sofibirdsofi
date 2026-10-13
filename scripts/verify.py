"""Verify generated pages, local resources, anchors, galleries and JavaScript."""
from __future__ import annotations

import argparse
import re
import subprocess
from collections import Counter
from pathlib import Path
from urllib.parse import unquote, urlparse

from bs4 import BeautifulSoup

SITE = Path(__file__).resolve().parents[1] / 'site'
CSS_URL = re.compile(r'url\([\"\']?([^\)\"\']+)')


def verify_site(root: Path = SITE) -> list[str]:
    root = Path(root).resolve()
    errors = []
    # Source templates have unresolved expressions and must never be treated as pages.
    pages = [p for p in root.rglob('*.html') if 'templates' not in p.relative_to(root).parts]
    soups = {page: BeautifulSoup(page.read_text(encoding='utf-8'), 'html.parser') for page in pages}
    anchors = {page: {str(t.get('id') or t.get('name')) for t in soup.select('[id],a[name]')} for page, soup in soups.items()}

    def check(owner: Path, value: str | None, *, anchor: bool = False) -> None:
        if not value or value.startswith(('//', 'data:', 'mailto:', 'tel:')) or urlparse(value).scheme:
            return
        parsed = urlparse(value)
        target = (owner.parent / unquote(parsed.path)).resolve() if parsed.path else owner
        if parsed.path.startswith('/') or not target.is_relative_to(root):
            errors.append(f'{owner.relative_to(root)}: path escapes site or Pages base: {value}')
            return
        if target.is_dir():
            target /= 'index.html'
        if not target.is_file():
            errors.append(f'{owner.relative_to(root)}: missing {value}')
        elif anchor and parsed.fragment and target in anchors and unquote(parsed.fragment) not in anchors[target]:
            # Tilda action hooks are not document anchors (none used by this site).
            if not parsed.fragment.startswith(('popup:', 'order:', 'link:')):
                errors.append(f'{owner.relative_to(root)}: missing anchor {value}')

    def check_js(owner: Path, code: str | None = None) -> None:
        cmd = ['node', '--check', str(owner)] if code is None else ['node', '--check']
        result = subprocess.run(cmd, input=code, capture_output=True, text=True, timeout=30)
        if result.returncode:
            errors.append(f'{owner.relative_to(root)}: JavaScript syntax error\n{result.stderr.strip()}')

    for page, soup in soups.items():
        html = page.read_text(encoding='utf-8')
        label = page.relative_to(root)
        if '{{' in html or '{%' in html:
            errors.append(f'{label}: unresolved template expression')
        if soup.select('#tildacopy'):
            errors.append(f'{label}: Tilda credit present')
        for value, count in Counter(t['id'] for t in soup.select('[id]')).items():
            if count > 1:
                errors.append(f'{label}: duplicate id {value}')
        for tag in soup.find_all(True):
            for attr in ('src', 'href', 'data-original', 'data-zoom', 'data-img-zoom-url', 'data-content-cover-bg', 'poster'):
                check(page, tag.get(attr), anchor=attr == 'href')
            if tag.name == 'meta' and tag.get('itemprop') == 'image':
                check(page, tag.get('content'))
            for value in CSS_URL.findall(tag.get('style', '')):
                check(page, value)
        for style in soup.select('style'):
            for value in CSS_URL.findall(style.get_text()):
                check(page, value)
        for script in soup.select('script:not([src])'):
            if script.get('type', '').lower() in {'', 'text/javascript', 'application/javascript'} and script.string:
                check_js(page, script.string)
        for gallery in soup.select('.t-slds'):
            slides = gallery.select('.t-slds__items-wrapper > .t-slds__item')
            expected = [str(i) for i in range(1, len(slides) + 1)]
            if not slides or [s.get('data-slide-index') for s in slides] != expected:
                errors.append(f'{label}: non-sequential gallery slide indices')
            for controls in gallery.select('.t-slds__thumbsbullet-wrapper,.t-slds__bullet_wrapper'):
                if [s.get('data-slide-bullet-for') for s in controls.select('[data-slide-bullet-for]')] != expected:
                    errors.append(f'{label}: gallery controls do not match slides')
    for css in (root / 'assets').rglob('*.css'):
        for value in CSS_URL.findall(css.read_text(encoding='utf-8')):
            check(css, value)
    for script in (root / 'assets').rglob('*.js'):
        check_js(script)
    if not pages:
        errors.append('No generated HTML pages found')
    return errors


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=SITE, help='site directory to verify')
    args = parser.parse_args()
    errors = verify_site(args.root)
    if errors:
        parser.exit(1, '\n'.join(errors) + f'\n{len(errors)} verification errors.\n')
    print('Pages, local resources, anchors, galleries, JavaScript and Tilda credit checks passed.')


if __name__ == '__main__':
    main()
