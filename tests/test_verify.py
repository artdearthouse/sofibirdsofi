"""Regression checks for failures that otherwise silently reach Pages."""
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))


class VerificationTests(unittest.TestCase):
    def setUp(self):
        import verify
        self.assertTrue(hasattr(verify, 'verify_site'), 'Reusable verifier is not implemented yet')
        self.verify = verify.verify_site
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.site = Path(self.temp.name)
        (self.site / 'assets').mkdir()
        (self.site / 'assets/photo.jpeg').write_bytes(b'image fixture')

    def page(self, html):
        (self.site / 'index.html').write_text('<html><body>' + html + '</body></html>')

    def test_missing_same_page_anchor_is_reported(self):
        self.page('<a href="#missing">About</a>')
        self.assertTrue(any('anchor' in error for error in self.verify(self.site)))

    def test_nested_page_anchor_is_checked(self):
        (self.site / 'fur').mkdir()
        (self.site / 'fur/index.html').write_text('<a name="about"></a>')
        self.page('<a href="fur/#about">Good</a>')
        self.assertEqual(self.verify(self.site), [])
        self.page('<a href="fur/#missing">Bad</a>')
        self.assertTrue(any('anchor' in error for error in self.verify(self.site)))

    def test_missing_zoom_image_is_reported(self):
        self.page('<div data-img-zoom-url="assets/missing.jpeg"></div>')
        self.assertTrue(any('missing.jpeg' in error for error in self.verify(self.site)))

    def test_gallery_indices_and_thumbnail_count_are_checked(self):
        self.page('<div class="t-slds"><div class="t-slds__items-wrapper"><div class="t-slds__item" data-slide-index="2"></div></div><div class="t-slds__thumbsbullet-wrapper"></div></div>')
        errors = self.verify(self.site)
        self.assertTrue(any('slide indices' in error for error in errors))
        self.assertTrue(any('gallery controls' in error for error in errors))

    def test_duplicate_ids_and_credit_are_reported(self):
        self.page('<div id="same"></div><div id="same"></div><div id="tildacopy"></div>')
        errors = self.verify(self.site)
        self.assertTrue(any('duplicate id' in error for error in errors))
        self.assertTrue(any('Tilda credit' in error for error in errors))

    def test_templates_are_not_published_pages(self):
        (self.site / 'templates').mkdir()
        (self.site / 'templates/component.html').write_text('<img src="{{ image.src }}">')
        self.page('<img src="assets/photo.jpeg">')
        self.assertEqual(self.verify(self.site), [])

    def test_inline_javascript_syntax_is_checked(self):
        self.page('<script>function broken( {</script>')
        self.assertTrue(any('JavaScript' in error for error in self.verify(self.site)))

    def test_unrendered_template_is_reported(self):
        self.page('<div>{{ page.title }}</div>')
        self.assertTrue(any('template' in error for error in self.verify(self.site)))


if __name__ == '__main__':
    unittest.main()
