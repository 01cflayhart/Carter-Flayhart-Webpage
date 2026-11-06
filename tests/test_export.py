import tempfile
import unittest
from pathlib import Path

from tennis.export import export_assets


class AssetExportTests(unittest.TestCase):
    def test_assets_only_requires_both_tours_and_preserves_data(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'site').mkdir(); (root / 'web').mkdir()
            (root / 'site/index.html').write_text('new public page')
            (root / 'web/runtime.js').write_text('local runtime')
            with self.assertRaises(ValueError):
                export_assets(root)
            self.assertFalse((root / '_site/index.html').exists())
            data = root / '_site/sports/tennis/data'
            for tour in ('ATP', 'WTA'):
                (data / tour).mkdir(parents=True)
                (data / tour / 'meta.json').write_text('{"existing":"snapshot"}')
            export_assets(root)
            self.assertEqual((root / '_site/index.html').read_text(), 'new public page')
            self.assertEqual((root / '_site/sports/tennis/runtime.js').read_text(), 'window.COURT_STATIC = true;\n')
            for tour in ('ATP', 'WTA'):
                self.assertEqual((data / tour / 'meta.json').read_text(), '{"existing":"snapshot"}')
