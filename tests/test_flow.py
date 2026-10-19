import io
import json
import shutil
import subprocess
import sys
import tempfile
import threading
import unittest
from contextlib import redirect_stdout
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch

from functions.scraping import initial_scrap


class FixtureHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/redirect":
            self.send_response(302)
            self.send_header("Location", "/pages/index.html")
            self.end_headers()
            return
        if self.path == "/missing":
            self.send_error(404)
            return
        if self.path == "/json":
            content_type = "application/json"
            body = json.dumps({"fake": '<a href="/bad">x</a>'})
        elif self.path == "/no-type":
            content_type, body = None, "<title>No type</title>"
        elif self.path == "/empty":
            content_type, body = "text/html", "<p>No title or links</p>"
        else:
            content_type = "text/html; charset=utf-8"
            body = '<title>Olá web</title><a href="child#one">Child</a><a href="child#two">Duplicate</a><a href="mailto:a@example.com">Email</a>'
        self.send_response(200)
        if content_type:
            self.send_header("Content-Type", content_type)
        self.end_headers()
        self.wfile.write(body.encode("utf-8"))

    def log_message(self, format, *args):
        pass


class FlowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), FixtureHandler)
        cls.base_url = f"http://127.0.0.1:{cls.server.server_port}"
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

    def run_scraper(self, url, path):
        output = io.StringIO()
        with patch("builtins.input", return_value=url), redirect_stdout(output):
            result = initial_scrap(path)
        return result, output.getvalue()

    def test_redirect_extracts_and_saves_using_final_url(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "out.json"
            success, output = self.run_scraper(self.base_url + "/redirect", path)
            self.assertTrue(success)
            data = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(data["source_url"], self.base_url + "/redirect")
            self.assertEqual(data["url"], self.base_url + "/pages/index.html")
            self.assertEqual(data["title"], "Olá web")
            self.assertEqual(data["links"], [self.base_url + "/pages/child"])
            self.assertEqual(data["link_count"], len(data["links"]))
            self.assertEqual(data["status_code"], 200)
            self.assertTrue(data["fetched_at"].endswith("+00:00"))
            self.assertIn("Saved to:", output)

    def test_non_html_is_rejected_before_any_extraction_and_preserves_previous_file(self):
        for route in ("/json", "/no-type"):
            with self.subTest(route=route), tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / "out.json"
                path.write_text("previous", encoding="utf-8")
                with patch("functions.scraping.extract_links") as links, patch("functions.scraping.extract_title") as title:
                    success, output = self.run_scraper(self.base_url + route, path)
                self.assertFalse(success)
                links.assert_not_called()
                title.assert_not_called()
                self.assertIn("not an HTML", output)
                self.assertEqual(path.read_text(encoding="utf-8"), "previous")

    def test_missing_title_and_links_are_valid_results(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "out.json"
            success, _ = self.run_scraper(self.base_url + "/empty", path)
            self.assertTrue(success)
            data = json.loads(path.read_text(encoding="utf-8"))
            self.assertIsNone(data["title"])
            self.assertEqual(data["links"], [])
            self.assertEqual(data["link_count"], 0)

    def test_http_error_does_not_create_output(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "out.json"
            success, output = self.run_scraper(self.base_url + "/missing", path)
            self.assertFalse(success)
            self.assertFalse(path.exists())
            self.assertIn("404", output)

    def test_invalid_input_reprompts_before_fetching(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch("builtins.input", side_effect=["https://", self.base_url + "/empty"]), redirect_stdout(io.StringIO()):
                self.assertTrue(initial_scrap(Path(directory) / "out.json"))

    def test_save_failure_reports_failure_not_success(self):
        with tempfile.TemporaryDirectory() as directory:
            success, output = self.run_scraper(self.base_url + "/empty", Path(directory))
            self.assertFalse(success)
            self.assertIn("Error saving JSON", output)
            self.assertNotIn("Saved to:", output)

    def test_eof_cancels_cleanly(self):
        with patch("builtins.input", side_effect=EOFError), redirect_stdout(io.StringIO()):
            self.assertFalse(initial_scrap())

    def test_real_cli_exit_codes_and_default_output(self):
        root = Path(__file__).resolve().parent.parent
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory) / "project"
            project.mkdir()
            shutil.copy2(root / "main.py", project / "main.py")
            shutil.copytree(root / "functions", project / "functions", ignore=shutil.ignore_patterns("__pycache__"))
            output_path = project / "results" / "result.json"
            for route, exit_code in (("/redirect", 0), ("/json", 1), ("/missing", 1)):
                with self.subTest(route=route):
                    output_path.unlink(missing_ok=True)
                    completed = subprocess.run(
                        [sys.executable, str(project / "main.py")],
                        input=self.base_url + route + "\n", capture_output=True,
                        text=True, cwd=directory, timeout=15,
                    )
                    self.assertEqual(completed.returncode, exit_code, completed.stdout + completed.stderr)
                    self.assertNotIn("Traceback", completed.stderr)
                    self.assertEqual(output_path.exists(), exit_code == 0)
                    if exit_code == 0:
                        data = json.loads(output_path.read_text(encoding="utf-8"))
                        self.assertEqual(data["title"], "Olá web")


if __name__ == "__main__":
    unittest.main()
