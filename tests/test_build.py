"""Integration tests for the editing workflow, not template implementation details."""
import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))


class BuildTests(unittest.TestCase):
    def setUp(self):
        from build import render_site
        self.render = render_site
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.site = Path(self.temp.name)
        import shutil
        shutil.copytree(ROOT / 'site/content', self.site / 'content')
        shutil.copytree(ROOT / 'site/templates', self.site / 'templates')
        (self.site / 'assets').symlink_to(ROOT / 'site/assets', target_is_directory=True)

    def edit(self, filename, update):
        path = self.site / 'content' / filename
        data = json.loads(path.read_text())
        update(data)
        path.write_text(json.dumps(data, ensure_ascii=False))

    def test_title_price_and_html_description_can_be_edited(self):
        def update(page):
            product = next(s for s in page['sections'] if s['type'] == 'product')
            product.update(title='New bird <3 & "friend"', price='123', description_html='Hello<br><strong>bird</strong>')
        self.edit('fur.json', update)
        soup = BeautifulSoup(self.render(self.site)['fur/index.html'], 'html.parser')
        self.assertEqual(soup.select_one('.js-product-name').get_text(strip=True), 'New bird <3 & "friend"')
        self.assertEqual(soup.select_one('.js-product-price').get_text(strip=True), '123')
        self.assertEqual(soup.select_one('.t744__descr strong').get_text(), 'bird')
        self.assertTrue(soup.select_one('.t744__descr br'))

    def test_new_product_and_photos_generate_matching_controls(self):
        def update(page):
            product = copy.deepcopy(next(s for s in page['sections'] if s['type'] == 'product'))
            product['id'] = '9000000001'
            product['title'] = 'New product'
            product['images'] *= 3
            page['sections'].append(product)
        self.edit('fur.json', update)
        soup = BeautifulSoup(self.render(self.site)['fur/index.html'], 'html.parser')
        product = soup.select_one('#rec9000000001')
        self.assertEqual(len(product.select('.t-slds__item')), 3)
        self.assertEqual(len(product.select('.t-slds__thumbsbullet')), 3)
        self.assertEqual(len(product.select('.t-slds__arrow')), 2)
        self.assertEqual([s['data-slide-index'] for s in product.select('.t-slds__item')], ['1', '2', '3'])
        self.assertEqual(len(product.select('.js-product-img')), 1)

    def test_nested_paths_and_shared_links_are_resolved(self):
        self.edit('common.json', lambda data: data['links'].update(bluesky='https://example.org/contact?a=1&b=2'))
        pages = self.render(self.site)
        soup = BeautifulSoup(pages['fur/index.html'], 'html.parser')
        self.assertEqual(soup.select_one('.t744__btn')['href'], 'https://example.org/contact?a=1&b=2')
        self.assertTrue(soup.select_one('.t744 .t-bgimg')['data-original'].startswith('../assets/'))
        main = BeautifulSoup(pages['index.html'], 'html.parser')
        self.assertTrue(main.select_one('.t744 .t-bgimg')['data-original'].startswith('assets/'))
        self.assertEqual(main.select_one('.t744__btn')['href'], 'fur/')
        self.assertEqual(soup.select_one('link[rel="canonical"]')['href'], 'https://artdearthouse.github.io/sofibirdsofi/fur/')

    def test_duplicate_record_id_is_rejected(self):
        def update(page):
            page['sections'].append(copy.deepcopy(next(s for s in page['sections'] if s['type'] == 'product')))
        self.edit('fur.json', update)
        with self.assertRaisesRegex(ValueError, 'Duplicate.*id'):
            self.render(self.site)

    def test_missing_image_is_rejected_before_any_output(self):
        def update(page):
            next(s for s in page['sections'] if s['type'] == 'product')['images'][0]['src'] = 'assets/missing.jpeg'
        self.edit('fur.json', update)
        from build import build_site
        with self.assertRaisesRegex(ValueError, 'missing.jpeg'):
            build_site(self.site)
        self.assertFalse((self.site / 'index.html').exists())

    def test_unsafe_button_url_is_rejected(self):
        def update(page):
            next(s for s in page['sections'] if s['type'] == 'product')['button']['href'] = 'javascript:alert(1)'
        self.edit('fur.json', update)
        with self.assertRaisesRegex(ValueError, 'URL'):
            self.render(self.site)

    def test_empty_gallery_is_rejected(self):
        def update(page):
            next(s for s in page['sections'] if s['type'] == 'product')['images'] = []
        self.edit('fur.json', update)
        with self.assertRaisesRegex(ValueError, 'images'):
            self.render(self.site)

    def test_menu_is_real_links_instead_of_escaped_markup(self):
        soup = BeautifulSoup(self.render(self.site)['index.html'], 'html.parser')
        links = soup.select('.t-menu-base__list .t-menu__link-item')
        self.assertEqual(len(links), 5)
        self.assertEqual(links[0]['href'], '#about')
        self.assertEqual(links[1]['href'], '#shop')

    def test_invalid_record_id_is_rejected(self):
        def update(page):
            next(s for s in page['sections'] if s['type'] == 'product')['id'] = 'bad-id'
        self.edit('fur.json', update)
        with self.assertRaisesRegex(ValueError, 'digits'):
            self.render(self.site)

    def test_preview_is_optional_for_product_and_about_images(self):
        def update(page):
            next(s for s in page['sections'] if s['type'] == 'product')['images'][0].pop('preview')
        self.edit('fur.json', update)
        self.edit('common.json', lambda data: data['about']['image'].pop('preview'))
        soup = BeautifulSoup(self.render(self.site)['fur/index.html'], 'html.parser')
        self.assertIn(soup.select_one('.t744 .t-bgimg')['data-original'], soup.select_one('.t744 .t-bgimg')['style'])
        self.assertEqual(soup.select_one('.t194 img')['src'], soup.select_one('.t194 img')['data-original'])

    def test_render_is_deterministic(self):
        self.assertEqual(self.render(self.site), self.render(self.site))
        self.assertEqual(set(self.render(self.site)), {'index.html', 'fur/index.html', 'ceramic/index.html', 'prints/index.html'})

    def test_templates_fail_on_unknown_field(self):
        path = self.site / 'templates/base.html'
        path.write_text(path.read_text() + '{{ page.missing_field }}')
        from jinja2 import UndefinedError
        with self.assertRaises(UndefinedError):
            self.render(self.site)


if __name__ == '__main__':
    unittest.main()
