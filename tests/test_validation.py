import unittest

from functions import scraping


class URLValidationTests(unittest.TestCase):
    def test_url_validation(self):
        cases = {
            "https://example.com/path?q=1": True,
            "http://localhost:8080/": True,
            "http://127.0.0.1/": True,
            "http://[::1]:8080/": True,
            "HTTPS://example.com": True,
            "https://": False,
            "example.com": False,
            "ftp://example.com": False,
            "https://example.com:abc": False,
            "http://example.com:99999": False,
            "http://[broken": False,
            "https://exa mple.com": False,
            "https://user:password@example.com": False,
            "https://example.com/\npath": False,
            "https://" + "a" * 64 + ".com": False,
            "": False,
        }
        for url, expected in cases.items():
            with self.subTest(url=url):
                self.assertEqual(scraping.is_valid_url(url), expected)


if __name__ == "__main__":
    unittest.main()
