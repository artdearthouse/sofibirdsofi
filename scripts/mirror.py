"""Download the published site and localize its static dependencies."""
import concurrent.futures
import hashlib
import gzip
import json
import re
import time
import subprocess
from pathlib import Path
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup, Comment

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / 'site'
ORIGIN = 'https://softbirdsofi.tilda.ws'
URL_RE = re.compile(r'https?://[^\s\"\'<>\\)]+')

def fetch(url):
    cache = ROOT / '.mirror-cache' / hashlib.sha256(url.encode()).hexdigest()
    if cache.exists():
        data = cache.read_bytes()
        return gzip.decompress(data) if data.startswith(b'\x1f\x8b') else data
    cache.parent.mkdir(exist_ok=True)
    for attempt in range(3):
        try:
            data = subprocess.check_output(['curl', '-fL', '--connect-timeout', '15', '--max-time', '60', '-sS', url], stderr=subprocess.PIPE)
            cache.write_bytes(data)
            return gzip.decompress(data) if data.startswith(b'\x1f\x8b') else data
        except Exception:
            if attempt == 2:
                raise
            time.sleep(1)

def is_asset(url):
    host = urlparse(url).hostname or ''
    return bool(urlparse(url).path.strip('/')) and ('tildacdn' in host or host in ('fonts.googleapis.com', 'fonts.gstatic.com'))

def asset_path(url):
    suffix = Path(urlparse(url).path).suffix
    if urlparse(url).hostname == 'fonts.googleapis.com':
        suffix = '.css'
    if not re.fullmatch(r'\.[a-zA-Z0-9]{1,8}', suffix):
        suffix = '.bin'
    return 'assets/' + hashlib.sha256(url.encode()).hexdigest()[:20] + suffix

def main():
    SITE.mkdir(exist_ok=True)
    (SITE / 'assets').mkdir(exist_ok=True)
    pages = {}
    pending = ['/']
    unavailable = set()
    while pending:
        path = pending.pop(0)
        if path in pages or path in unavailable:
            continue
        try:
            html = fetch(ORIGIN + path).decode('utf-8')
        except Exception as error:
            if path == '/':
                raise
            print('Unavailable page:', path, error, flush=True)
            unavailable.add(path)
            continue
        soup = BeautifulSoup(html, 'html.parser')
        for credit in soup.select('#tildacopy'):
            credit.decompose()
        for comment in soup.find_all(string=lambda x: isinstance(x, Comment)):
            if 'Tilda copyright' in comment:
                comment.extract()
        for link in soup.select('a[href]'):
            href = link['href']
            if href.startswith('/https://'):
                link['href'] = href[1:]
                continue
            parsed = urlparse(urljoin(ORIGIN + path, href))
            if parsed.hostname == urlparse(ORIGIN).hostname and not parsed.path.endswith(('.jpg', '.png', '.pdf')):
                target = parsed.path or '/'
                if target not in pages and target not in pending and target not in unavailable:
                    pending.append(target)
        pages[path] = str(soup)
        print('Page:', path, flush=True)
    urls = set()
    for html in pages.values():
        urls.update(u.replace('&amp;', '&') for u in URL_RE.findall(html) if is_asset(u))
    downloaded = {}
    while urls:
        batch = sorted(urls - downloaded.keys())
        if not batch:
            break
        urls = set()
        def download(url):
            return url, fetch(url)
        with concurrent.futures.ThreadPoolExecutor(max_workers=12) as pool:
            for url, data in pool.map(download, batch):
                downloaded[url] = data
                if asset_path(url).endswith('.css'):
                    css = data.decode('utf-8')
                    urls.update(u for u in URL_RE.findall(css) if is_asset(u))
                    for relative in re.findall(r'url\([\"\']?([^\)\"\']+)', css):
                        if not relative.startswith(('data:', 'http')):
                            urls.add(urljoin(url, relative))
        print('Assets:', len(downloaded), flush=True)
    def replace_urls(content, prefix):
        for url in sorted(downloaded, key=len, reverse=True):
            replacement = prefix + asset_path(url)
            content = content.replace(url.replace('&', '&amp;'), replacement).replace(url, replacement)
        return content
    for url, data in downloaded.items():
        local = asset_path(url)
        if local.endswith('.css'):
            css = data.decode('utf-8')
            for relative in re.findall(r'url\([\"\']?([^\)\"\']+)', css):
                absolute = urljoin(url, relative)
                if absolute in downloaded and not relative.startswith('http'):
                    css = css.replace(relative, '../' + asset_path(absolute))
            data = replace_urls(css, '../').encode()
        (SITE / local).write_bytes(data)
    for path, html in pages.items():
        output = 'index.html' if path == '/' else path.strip('/') + '/index.html'
        prefix = '../' * (len(Path(output).parts) - 1)
        html = replace_urls(html, prefix)
        soup = BeautifulSoup(html, 'html.parser')
        for link in soup.select('a[href]'):
            href = link['href']
            parsed = urlparse(urljoin(ORIGIN + path, href))
            if parsed.hostname == urlparse(ORIGIN).hostname and parsed.path in pages and not href.startswith('#'):
                target = '' if parsed.path == '/' else parsed.path.strip('/') + '/'
                link['href'] = prefix + ('./' if not target else target) + (('#' + parsed.fragment) if parsed.fragment else '')
        destination = SITE / output
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(str(soup), encoding='utf-8')
    (SITE / '.nojekyll').touch()
    (ROOT / 'scripts' / 'asset-manifest.json').write_text(json.dumps({u: asset_path(u) for u in sorted(downloaded)}, indent=2) + '\n')
    print('Done:', len(pages), 'pages,', len(downloaded), 'assets')

if __name__ == '__main__':
    main()
