import json
import tempfile
import unittest
from pathlib import Path

from functions import scraping


class StorageTests(unittest.TestCase):
    def test_save_creates_parents_and_writes_utf8_json(self):
        result = {"title": "Cibersegurança", "links": [], "link_count": 0}
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "nested" / "result.json"
            saved = scraping.save_result(result, path)
            self.assertEqual(saved, path)
            self.assertEqual(json.loads(path.read_text(encoding="utf-8")), result)
            self.assertIn("Cibersegurança", path.read_text(encoding="utf-8"))
            scraping.save_result({"title": None}, path)
            self.assertEqual(json.loads(path.read_text(encoding="utf-8")), {"title": None})

    def test_write_error_propagates_to_caller(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(OSError):
                scraping.save_result({}, Path(directory))


if __name__ == "__main__":
    unittest.main()
