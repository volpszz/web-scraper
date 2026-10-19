import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urldefrag, urljoin, urlsplit

import requests
from bs4 import BeautifulSoup


DEFAULT_OUTPUT_PATH = Path(__file__).resolve().parent.parent / "results" / "result.json"


def save_result(result, output_path=DEFAULT_OUTPUT_PATH):
    """Save the latest result as readable UTF-8 JSON, replacing an existing file."""
    path = Path(output_path)
    content = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def is_valid_url(url):
    """Validate URL structure, without checking DNS or reaching the server."""
    if not url or any(char.isspace() or ord(char) < 32 or ord(char) == 127 for char in url):
        return False

    try:
        parsed = urlsplit(url)
        if parsed.scheme not in ("http", "https") or not parsed.hostname:
            return False
        if parsed.username is not None or parsed.password is not None:
            return False
        if parsed.port is not None and parsed.port == 0:
            return False
        parsed.hostname.encode("idna")
    except (ValueError, UnicodeError):
        return False

    return True


def extract_title(html):
    """Return the first document title, or None if its element is missing."""
    soup = BeautifulSoup(html, "html.parser")
    title_element = soup.find("title")

    if title_element is None:
        return None

    return title_element.get_text(strip=True)


def extract_links(html, base_url):
    """Return unique HTTP/HTTPS anchor destinations in document order."""
    soup = BeautifulSoup(html, "html.parser")
    links = []
    seen = set()

    for element in soup.find_all("a", href=True):
        href = element["href"].strip()

        if not href or href.startswith("#"):
            continue

        if any(char.isspace() or ord(char) < 32 or ord(char) == 127 for char in href):
            continue

        try:
            absolute_url = urljoin(base_url, href)
            absolute_url, _ = urldefrag(absolute_url)
        except ValueError:
            continue

        if not is_valid_url(absolute_url):
            continue

        if absolute_url in seen:
            continue

        seen.add(absolute_url)
        links.append(absolute_url)

    return links


def fetch_page(url):
    """Fetch a page, following redirects; return None for request/HTTP errors."""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response
    except requests.exceptions.HTTPError as error:
        print(f"Erro HTTP ao acessar a página: {error}")
        return None
    except requests.exceptions.RequestException as error:
        print(f"Erro ao acessar a página: {error}")
        return None


def show_response(response):
    print("Status:", response.status_code)
    print("Content type:", response.headers.get("Content-Type"))
    print("Body preview:")
    print(response.text[:500])


def initial_scrap(output_path=DEFAULT_OUTPUT_PATH):
    """Run one interactive scrape; return True only after saving its result."""
    while True:
        try:
            url = input("Insert the target url: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nCancelled.")
            return False

        if is_valid_url(url):
            break

        print("Error: enter a valid HTTP/HTTPS URL with a host, no spaces or credentials, and a valid port.")

    response = fetch_page(url)

    if response is None:
        return False

    show_response(response)

    content_type = response.headers.get("Content-Type", "")
    media_type = content_type.split(";", 1)[0].strip().lower()

    if media_type not in ("text/html", "application/xhtml+xml"):
        print("Error: response is not an HTML document.")
        return False

    title = extract_title(response.text)
    links = extract_links(response.text, response.url)

    print("Page title:", title if title is not None else "not found")
    print("Links found:", len(links))
    for link in links:
        print("-", link)

    result = {
        "source_url": url,
        "url": response.url,
        "status_code": response.status_code,
        "content_type": content_type,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "title": title,
        "links": links,
        "link_count": len(links),
    }

    try:
        path = save_result(result, output_path)
    except OSError as error:
        print(f"Error saving JSON: {error}")
        return False

    print("Saved to:", path)
    return True