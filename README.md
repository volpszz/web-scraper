# Web Scraper — v1.0.0

An educational Python web scraper that fetches one HTML page, extracts its title and unique HTTP/HTTPS links, and saves the result as JSON. It does not follow extracted links or execute JavaScript.

**Version 1 is complete for this scope. Authenticated-site scraping is planned for version 2 and is not implemented in v1.**

## Requirements

- Python 3.10+
- Dependencies in `requirements.txt`: `requests` and `beautifulsoup4`

## Setup

From the project directory:

```bash
python -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

On Linux, activation is optional when using `.venv/bin/python` directly. To activate:

- Fish: `source .venv/bin/activate.fish`
- Bash/Zsh: `source .venv/bin/activate`
- Windows PowerShell: `.venv\Scripts\Activate.ps1`; without activation, use `.venv\Scripts\python.exe` instead of `.venv/bin/python`.

In VS Code, select `.venv/bin/python` through **Python: Select Interpreter**. The installation package is `beautifulsoup4`, while the Python import is `from bs4 import BeautifulSoup`.

## Run

```bash
.venv/bin/python main.py
```

Enter a complete HTTP/HTTPS URL when prompted. Use owned or authorized sites and respect the service's access and collection rules.

The program prints the status, content type, body preview, title and links. It writes **`results/result.json`** relative to the project root, even when launched from another directory.

**Each successful run replaces the previous result.** Copy the file if you need history. Network, HTTP and non-HTML failures do not start a save; do not confuse an older file with a new result. Write failures are reported, but writes are not atomic.

### JSON output

| Field | Contents |
|---|---|
| `source_url` | Input URL with surrounding whitespace removed |
| `url` | Final URL after redirects |
| `status_code` | Final HTTP status |
| `content_type` | Received Content-Type header |
| `fetched_at` | UTC result-assembly timestamp in ISO 8601 |
| `title` | Text of the first `<title>`, or `null` if absent |
| `links` | Unique HTTP/HTTPS destinations in document order |
| `link_count` | Number of entries in `links` |

Exit code: `0` only after saving; `1` on failure or cancellation. `results/` is ignored by Git.

## Tests

```bash
.venv/bin/python -m unittest discover -s tests -v
```

No pytest installation is needed. Tests use `unittest`, simulated responses, a loopback HTTP server and real CLI subprocesses. They do not depend on external sites; the environment must allow opening a local port. Temporary files are cleaned up afterwards.

## Version 1 scope and limitations

- One page per run; `requests` follows HTTP redirects.
- Extraction starts only for `text/html` or `application/xhtml+xml`; XHTML uses an HTML parser, not strict XML semantics.
- No JavaScript execution, authentication or access-control bypass.
- No verification of collected destinations or automatic `robots.txt` checks.
- No support for `<base href>`, iframe documents, Shadow DOM or attributes other than `a[href]`.
- Fragments are removed, queries are preserved, and URLs are not fully canonicalized.
- Basic structural validation does not guarantee DNS resolution, availability, security or permission.
- No response-size limit; `timeout=10` is not a total execution deadline.
- Intended for local, manual use. Do not expose arbitrary URL fetching as a public service without SSRF protections and resource limits.

## Roadmap — version 2 (planned, not implemented)

The next version is planned to support **scraping authenticated pages on owned or explicitly authorized sites**. Initial work will focus on a controlled form-login flow using `requests.Session`, session cookies and CSRF tokens where required.

The design must include safe credential input, explicit login-success and session-expiry detection, logout/cleanup, and local integration tests. Passwords, cookies, tokens and authenticated page bodies must not leak into source control, diagnostic previews or result metadata. Authentication will be site-specific, not a promise to log into any website; MFA, CAPTCHA and SSO bypass are out of scope.

See the **[v2 planning document (Portuguese)](docs/ROADMAP_V2.md)** for the proposed scope, acceptance criteria and open decisions. No implementation or release date is promised.

## Learn and contribute

Read the **[PDF study and maintenance guide (Portuguese)](docs/GUIA_DO_PROJETO.pdf)** for HTTP, DNS, HTTPS, HTML versus DOM, architecture, extraction decisions, JSON, testing, troubleshooting and exercises. The PDF includes numbered source listings. Its **[editable Markdown source](docs/GUIA_DO_PROJETO.md)** is kept alongside it.

### Rebuild the PDF (optional)

Documentation tooling is separate from runtime dependencies:

```bash
python -m venv .venv-docs
.venv-docs/bin/python -m pip install -r requirements-docs.txt
.venv-docs/bin/python -m playwright install chromium
.venv-docs/bin/python scripts/build_guide_pdf.py
.venv-docs/bin/python -m unittest discover -s scripts -p test_build_guide_pdf.py -v
```

The generator can instead use an installed Chromium/Chrome/Brave; set `--browser /path/to/executable` or `PDF_BROWSER`. It uses system fonts (DejaVu Sans/Mono, with fallbacks). A manifest next to the PDF records source/tooling hashes and page count; regenerate after editing the documented sources. Windows users should substitute `.venv-docs\Scripts\python.exe`.
