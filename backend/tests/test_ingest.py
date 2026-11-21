import pytest

from app.ingest import IngestError, clean_text, extract_html_text, fetch_url_text


def test_html_extraction_prefers_article_and_drops_chrome():
    html = """
    <html><body>
      <nav>Home | About</nav>
      <article><h1>Mitochondria</h1><p>The   powerhouse
      of the cell.</p><script>track()</script></article>
      <footer>Copyright</footer>
    </body></html>
    """
    document = extract_html_text(html, 1000)
    assert document.text == "Mitochondria\nThe powerhouse\nof the cell."
    assert document.truncated is False


def test_clean_text_truncates_and_flags_it():
    document = clean_text("abcdef", 4)
    assert document.text == "abcd"
    assert document.truncated is True


def test_empty_text_is_an_error():
    with pytest.raises(IngestError):
        clean_text(" \n\t ", 100)


@pytest.mark.parametrize(
    "url",
    [
        "file:///etc/passwd",
        "ftp://example.com/file",
        "http://localhost/",
        "http://127.0.0.1/",
        "http://10.0.0.5/",
        "http://169.254.169.254/latest/meta-data/",
        "http://[::1]/",
    ],
)
def test_fetch_rejects_non_public_urls(url):
    with pytest.raises(IngestError):
        fetch_url_text(url, 1000)
