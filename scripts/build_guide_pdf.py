"""Build the Portuguese study guide PDF; requires requirements-docs.txt only."""
import argparse
import hashlib
import io
import json
import os
import re
import shutil
from html import escape
from pathlib import Path

import markdown
from playwright.sync_api import sync_playwright
from pypdf import PdfReader, PdfWriter

ROOT = Path(__file__).resolve().parent.parent
GUIDE = ROOT / "docs" / "GUIA_DO_PROJETO.md"
OUTPUT = ROOT / "docs" / "GUIA_DO_PROJETO.pdf"
SOURCES = [ROOT / "main.py", ROOT / "functions" / "scraping.py"]

CSS = """
@page { size: A4; margin: 18mm 17mm 20mm; }
* { box-sizing: border-box; font-variant-ligatures: none; }
body { font-family: 'DejaVu Sans', Arial, sans-serif; color: #223044;
       font-size: 10pt; line-height: 1.55; }
h1,h2,h3 { color: #142238; line-height: 1.25; break-after: avoid; }
h2 { font-size: 17pt; margin: 22pt 0 10pt; border-bottom: 1pt solid #d7dfe8; padding-bottom: 6pt; }
h3 { font-size: 12pt; margin: 15pt 0 7pt; }
p { margin: 7pt 0; orphans: 3; widows: 3; }
a { color: #1f5f8b; text-decoration: none; overflow-wrap: anywhere; }
li { margin: 4pt 0; }
code, pre { font-family: 'DejaVu Sans Mono', monospace; }
code { font-size: 8.5pt; overflow-wrap: anywhere; }
pre { background: #f0f4f8; border-left: 3pt solid #41849c; padding: 9pt;
      font-size: 8.2pt; line-height: 1.45; white-space: pre-wrap; overflow-wrap: anywhere; }
pre code { font-size: inherit; }
table { border-collapse: collapse; width: 100%; margin: 10pt 0; font-size: 8.7pt; table-layout: fixed; }
th,td { border: .5pt solid #ccd5df; padding: 6pt; text-align: left;
        vertical-align: top; overflow-wrap: anywhere; }
th { background: #e8eef4; }
thead { display: table-header-group; }
tr { break-inside: avoid; }
.cover { height: 245mm; padding-top: 32mm; break-after: page; }
.cover h1 { font-size: 38pt; letter-spacing: -1pt; margin: 18pt 0; }
.cover .edition { color: #1f6780; font-weight: bold; letter-spacing: 2pt; }
.cover p { font-size: 13pt; max-width: 145mm; }
.cover .small { font-size: 10pt; margin-top: 28mm; }
.toc { break-after: page; }
.toc ul { list-style: none; padding-left: 0; }
.toc li { margin: 10pt 0; }
.source-appendix { break-before: page; }
.listing { table-layout: fixed; font-size: 8pt; }
.listing td { border: 0; padding: 1pt 4pt; background: #f5f7fa; }
.listing .line { width: 9mm; color: #52667f; text-align: right; user-select: none; }
.listing code { font-size: 7.5pt; white-space: pre-wrap; overflow-wrap: anywhere; }
"""


def build_html(guide_text, source_paths):
    # Replace the handwritten GitHub-specific anchors with generated PDF anchors.
    guide_text = re.sub(r"^# .+\n", "", guide_text, count=1)
    guide_text = re.sub(r"## Roteiro de leitura\n.*?(?=\n## 1\.)", "[TOC]\n", guide_text, flags=re.S)
    converter = markdown.Markdown(extensions=["fenced_code", "tables", "toc"],
                                  extension_configs={"toc": {"toc_depth": "2-2"}})
    body = converter.convert(guide_text)
    appendices = []
    for path in source_paths:
        rows = []
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            rows.append(f'<tr><td class="line">{number}</td><td><code>{escape(line) or " "}</code></td></tr>')
        name = escape(path.relative_to(ROOT).as_posix())
        appendices.append(f'<section class="source-appendix"><h2>Código de referência: {name}</h2>'
                          '<p>Números são as linhas originais. Uma célula pode ocupar várias linhas visuais; '
                          'a numeração não é reiniciada nas continuações.</p>'
                          f'<table class="listing"><tbody>{"".join(rows)}</tbody></table></section>')
    cover = '''<section class="cover"><div class="edition">WEB SCRAPER · V1.0.0</div>
    <h1>Da URL<br>ao JSON.</h1>
    <p>Guia de estudo e manutenção: HTTP, HTML, extração de dados, testes e evolução do projeto.</p>
    <p>Uma página por execução. Código pequeno, decisões explícitas.</p>
    <p class="small">Projeto de Arthur Volpato · github.com/volpszz/web-scraper<br>
    Material em português · Fonte editável: docs/GUIA_DO_PROJETO.md<br>
    Autenticação na v2: planejada, não implementada nesta edição.</p></section>'''
    return ('<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">'
            '<title>Web Scraper v1 — Guia de estudo e manutenção</title>'
            f'<style>{CSS}</style></head><body>{cover}{body}{"".join(appendices)}</body></html>')


def render_pdf(html, output, browser_path=None):
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=browser_path, headless=True)
        try:
            page = browser.new_page()
            page.set_content(html, wait_until="load")
            pdf_bytes = page.pdf(format="A4", print_background=True, display_header_footer=True,
                                 header_template='<span></span>',
                                 footer_template='<div style="width:100%;font-size:8px;color:#52667f;text-align:center">Web Scraper v1 · <span class="pageNumber"></span> / <span class="totalPages"></span></div>',
                                 prefer_css_page_size=True, outline=True, tagged=True)
        finally:
            browser.close()
    reader = PdfReader(io.BytesIO(pdf_bytes))
    writer = PdfWriter(clone_from=reader)
    writer.add_metadata({"/Title": "Web Scraper v1 — Guia de estudo e manutenção",
                         "/Author": "Arthur Volpato", "/Subject": "HTTP, HTML, Python e manutenção do scraper"})
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("wb") as stream:
        writer.write(stream)
    return len(reader.pages)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--browser", default=os.environ.get("PDF_BROWSER"), help="Chromium/Chrome/Brave executable; otherwise auto-detect or use Playwright Chromium")
    args = parser.parse_args()
    browser = args.browser or next((shutil.which(name) for name in ("chromium", "chromium-browser", "google-chrome", "brave") if shutil.which(name)), None)
    html = build_html(GUIDE.read_text(encoding="utf-8"), SOURCES)
    pages = render_pdf(html, OUTPUT, browser)
    inputs = [GUIDE, *SOURCES, ROOT / "functions/greetings.py", ROOT / "requirements.txt",
              ROOT / "requirements-docs.txt", Path(__file__).resolve()]
    manifest = {"edition": "v1.0.0", "pages": pages,
                "inputs": {path.relative_to(ROOT).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest() for path in inputs},
                "pdf": {"path": OUTPUT.relative_to(ROOT).as_posix(), "sha256": hashlib.sha256(OUTPUT.read_bytes()).hexdigest()}}
    OUTPUT.with_suffix(".manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"pdf": str(OUTPUT), "pages": pages, "manifest": str(OUTPUT.with_suffix('.manifest.json'))}))


if __name__ == "__main__":
    main()
