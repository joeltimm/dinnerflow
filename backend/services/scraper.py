"""
Web scraper service.

Replicates the n8n nodes:
  1. "Fetch URL"   — HTTP GET with browser-like headers (avoids simple bot blocks)
  2. "Clean HTML"  — strips scripts/styles/nav, returns plain text ≤ 15 KB

fetch_and_clean(url) → str (cleaned text ready for LLM)
"""
import ipaddress
import logging
import re
import socket
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# Browser-like headers to reduce bot-detection rejections (mirrors n8n workflow)
_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}

_FETCH_TIMEOUT = 15  # seconds
_TEXT_LIMIT = 15_000  # characters — matches n8n workflow limit


def _validate_url(url: str) -> None:
    """
    Reject non-HTTP(S) schemes and private/loopback IP targets (SSRF prevention).
    Raises ValueError on invalid or disallowed URLs.
    """
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise ValueError(f"Disallowed URL scheme: {parsed.scheme!r}")

    hostname = parsed.hostname
    if not hostname:
        raise ValueError("URL has no hostname")

    try:
        ip = ipaddress.ip_address(socket.gethostbyname(hostname))
    except socket.gaierror:
        raise ValueError(f"Cannot resolve hostname: {hostname!r}")

    if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
        raise ValueError("Requests to private/internal addresses are not allowed")


def fetch_and_clean(url: str) -> str:
    """
    Download a recipe page and return cleaned plain text.
    Raises ValueError for disallowed URLs, requests.HTTPError on non-2xx responses.
    """
    _validate_url(url)
    resp = requests.get(url, headers=_HEADERS, timeout=_FETCH_TIMEOUT)
    resp.raise_for_status()
    return _clean_html(resp.text)


def _clean_html(raw_html: str) -> str:
    """
    Strip away everything that isn't content:
    - <script>, <style>, <nav>, <header>, <footer>, <aside> tags
    - HTML comments
    - Excess whitespace

    Returns plain text, truncated to _TEXT_LIMIT characters.
    """
    soup = BeautifulSoup(raw_html, "lxml")

    # Remove non-content tags entirely
    for tag in soup(["script", "style", "nav", "header", "footer", "aside", "iframe"]):
        tag.decompose()

    text = soup.get_text(separator="\n")

    # Collapse multiple blank lines into one
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Collapse multiple spaces
    text = re.sub(r"[ \t]{2,}", " ", text)

    return text.strip()[:_TEXT_LIMIT]
