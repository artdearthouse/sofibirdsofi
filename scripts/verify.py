"""Check local dependencies, JavaScript syntax and absence of Tilda credit."""
import re
import subprocess
from pathlib import Path
from urllib.parse import unquote, urlparse
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1] / 'site'
errors = []

def check(owner, value):
    if not value or value.startswith(('#', '//', 'data:', 'mailto:', 'tel:')) or urlparse(value).scheme:
        return
    if not (owner.parent / unquote(urlparse(value).path)).exists():
        errors.append(f'{owner.relative_to(ROOT)}: missing {value}')

for page in ROOT.rglob('*.html'):
    html = page.read_text()
    soup = BeautifulSoup(html, 'html.parser')
    if soup.select('#tildacopy'):
        errors.append(f'{page}: Tilda credit present')
    for tag in soup.find_all(True):
        for attr in ('src', 'href', 'data-original', 'data-zoom', 'poster'):
            check(page, tag.get(attr))
    for value in re.findall(r'url\([\"\']?([^\)\"\']+)', html):
        check(page, value)
    print('Verified page:', page.relative_to(ROOT))
for css in ROOT.rglob('*.css'):
    for value in re.findall(r'url\([\"\']?([^\)\"\']+)', css.read_text()):
        check(css, value)
for script in ROOT.rglob('*.js'):
    result = subprocess.run(['node', '--check', str(script)], capture_output=True, text=True)
    if result.returncode:
        errors.append(result.stderr)
for error in errors:
    print(error)
assert not errors, f'{len(errors)} verification errors'
print('Local dependencies, JavaScript syntax and footer checks passed.')
