import unittest

from functions.scraping import extract_links, extract_title


class ExtractionTests(unittest.TestCase):
    def test_title(self):
        self.assertEqual(extract_title("<title>  Olá &amp; web  </title>"), "Olá & web")
        self.assertIsNone(extract_title("<body>Sem título</body>"))

    def test_links_are_absolute_unique_and_in_document_order(self):
        html = '''
        <a href="post">Post</a><a href="/about#one">Sobre</a>
        <a href="/about#two">Mesmo destino</a>
        <a href="//other.example/path?q=1">Externo</a>
        <a href="?page=2">Consulta</a><a href="../up">Pai</a>
        <a href="#section">Seção</a><a href="">Vazio</a><a>Sem href</a>
        <a href="mailto:a@example.com">Email</a><a href="tel:123">Telefone</a>
        <a href="javascript:void(0)">Script</a>
        '''
        self.assertEqual(extract_links(html, "https://example.com/blog/"), [
            "https://example.com/blog/post",
            "https://example.com/about",
            "https://other.example/path?q=1",
            "https://example.com/blog/?page=2",
            "https://example.com/up",
        ])
        self.assertEqual(extract_links("<p>Sem links</p>", "https://example.com"), [])

    def test_malformed_links_are_skipped_without_losing_valid_links(self):
        html = '''
        <a href="http://[broken">Broken</a>
        <a href="http://example.com:bad">Port</a>
        <a href="https://exa mple.com">Space</a>
        <a href="https://user:password@example.com">Credentials</a>
        <a href="/ok">OK</a>
        '''
        self.assertEqual(extract_links(html, "https://example.com"), [
            "https://example.com/ok",
        ])


if __name__ == "__main__":
    unittest.main()
