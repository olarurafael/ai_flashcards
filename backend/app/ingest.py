"""Turn PDFs and web pages into plain text for the generator."""

import io
import ipaddress
import re
import socket
from dataclasses import dataclass
from urllib.parse import urljoin, urlsplit

import httpx
from bs4 import BeautifulSoup
from pypdf import PdfReader
from pypdf.errors import PdfReadError

MAX_PAGE_BYTES = 2 * 1024 * 1024
MAX_REDIRECTS = 3


class IngestError(Exception):
    pass


@dataclass(frozen=True)
class Document:
    text: str
    truncated: bool


def clean_text(raw: str, max_chars: int) -> Document:
    text = re.sub(r"[ \t\f\v]+", " ", raw)
    text = re.sub(r"\s*\n\s*", "\n", text).strip()
    if not text:
        raise IngestError("No readable text found")
    return Document(text=text[:max_chars], truncated=len(text) > max_chars)


def extract_pdf_text(data: bytes, max_chars: int) -> Document:
    try:
        reader = PdfReader(io.BytesIO(data))
        if reader.is_encrypted:
            raise IngestError("Password-protected PDFs are not supported")
        parts = []
        length = 0
        for page in reader.pages:
            page_text = page.extract_text() or ""
            parts.append(page_text)
            length += len(page_text)
            if length > max_chars:
                break
    except PdfReadError as exc:
        raise IngestError("This file is not a readable PDF") from exc

    try:
        return clean_text("\n".join(parts), max_chars)
    except IngestError:
        raise IngestError("No text found in the PDF (scanned PDFs are not supported)") from None


def extract_html_text(html: str, max_chars: int) -> Document:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript", "nav", "header", "footer", "aside", "form"]):
        tag.decompose()
    root = soup.find("article") or soup.find("main") or soup.body or soup
    return clean_text(root.get_text("\n"), max_chars)


def _check_public_url(url: str) -> None:
    """Reject URLs that point at the server's own network (SSRF).

    Every address the host resolves to must be public. A host could still
    re-resolve to a private address between this check and the request (DNS
    rebinding); the Lambda runs outside any VPC, so it has little to reach.
    """
    parts = urlsplit(url)
    if parts.scheme not in ("http", "https") or not parts.hostname:
        raise IngestError("Only http and https URLs are supported")
    try:
        infos = socket.getaddrinfo(parts.hostname, parts.port or 443, proto=socket.IPPROTO_TCP)
    except socket.gaierror:
        raise IngestError("Could not resolve that address") from None
    for info in infos:
        if not ipaddress.ip_address(info[4][0]).is_global:
            raise IngestError("That address is not allowed")


def fetch_url_text(url: str, max_chars: int) -> Document:
    with httpx.Client(timeout=10, follow_redirects=False) as client:
        for _ in range(MAX_REDIRECTS + 1):
            _check_public_url(url)
            try:
                with client.stream("GET", url, headers={"User-Agent": "ai-flashcards/1.0"}) as resp:
                    if resp.is_redirect:
                        url = urljoin(url, resp.headers["location"])
                        continue
                    if resp.status_code != 200:
                        raise IngestError(f"The page returned HTTP {resp.status_code}")
                    content_type = resp.headers.get("content-type", "")
                    if not content_type.startswith(("text/html", "text/plain")):
                        raise IngestError("The URL is not a web page")
                    body = b""
                    for chunk in resp.iter_bytes():
                        body += chunk
                        if len(body) > MAX_PAGE_BYTES:
                            break
            except httpx.HTTPError as exc:
                raise IngestError("Could not fetch that page") from exc

            text = body.decode(resp.encoding or "utf-8", errors="replace")
            if content_type.startswith("text/plain"):
                return clean_text(text, max_chars)
            return extract_html_text(text, max_chars)

    raise IngestError("Too many redirects")
