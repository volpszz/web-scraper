import io
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

import requests

from functions.scraping import fetch_page


class FetchPageTests(unittest.TestCase):
    def test_success_returns_original_response(self):
        response = requests.Response()
        response.status_code = 200

        with patch("functions.scraping.requests.get", return_value=response) as get:
            result = fetch_page("https://example.com/page")

        self.assertIs(result, response)
        get.assert_called_once_with("https://example.com/page", timeout=10)

    def test_network_failure_returns_none_and_explains_failure(self):
        for error in (requests.exceptions.Timeout("timeout"),
                      requests.exceptions.ConnectionError("connection failed")):
            with self.subTest(error=type(error).__name__):
                output = io.StringIO()
                with patch("functions.scraping.requests.get", side_effect=error):
                    with redirect_stdout(output):
                        result = fetch_page("https://example.com/page")

                self.assertIsNone(result)
                self.assertIn("Erro ao acessar a página", output.getvalue())

    def test_http_error_returns_none_and_explains_failure(self):
        for status in (403, 404, 500):
            with self.subTest(status=status):
                response = requests.Response()
                response.status_code = status
                response.url = "https://example.com/page"
                output = io.StringIO()

                with patch("functions.scraping.requests.get", return_value=response):
                    with redirect_stdout(output):
                        result = fetch_page(response.url)

                self.assertIsNone(result)
                self.assertIn("Erro HTTP", output.getvalue())
                self.assertIn(str(status), output.getvalue())


if __name__ == "__main__":
    unittest.main()
