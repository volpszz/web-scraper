import os
import shutil
import tempfile
import unittest
from pathlib import Path

from pypdf import PdfReader

from build_guide_pdf import ROOT, build_html, render_pdf


class GuidePDFTests(unittest.TestCase):
    def test_rendered_text_table_source_lines_and_outline(self):
        guide = '''# Teste

## Roteiro de leitura

1. Sumário antigo

## 1. Ação e código

| Estado | Significado |
|---|---|
| open\\|filtered | Exemplo |

```python
print("ação")
```
'''
        browser = os.environ.get("PDF_BROWSER") or next(
            (shutil.which(name) for name in ("chromium", "chromium-browser", "google-chrome", "brave") if shutil.which(name)), None
        )
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "sample.pdf"
            render_pdf(build_html(guide, [ROOT / "main.py"]), output, browser)
            reader = PdfReader(output)
            text = "\n".join(page.extract_text() for page in reader.pages)
            self.assertIn("Ação e código", text)
            self.assertIn("open|filtered", text)
            self.assertIn('print("ação")', text)
            self.assertIn("Código de referência: main.py", text)
            self.assertIn("raise SystemExit(0 if success else 1)", text)
            self.assertRegex(text, r"1\s+import functions.greetings")
            self.assertRegex(text, r"11\s+raise SystemExit")
            self.assertTrue(reader.outline)
            self.assertTrue(any(page.get("/Annots") for page in reader.pages))


if __name__ == "__main__":
    unittest.main()
