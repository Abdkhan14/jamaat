import asyncio
import logging
import time

import httpx
from bs4 import BeautifulSoup
from mosques import MOSQUES
from observability import mosque_scope
from scraping.errors import STAGE_FETCH, MosqueScrapeError

HTTPX_TIMEOUT = 20

logger = logging.getLogger(__name__)


def fetch_page_text(url: str) -> str:
    # NOTE: Some mosque WAFs (e.g. irccan.com) block requests that claim to be
    # a browser via a spoofed User-Agent but lack a matching browser TLS
    # fingerprint. A plain client with a consistent fingerprint is served
    # normally, so we intentionally do NOT send browser-spoofing headers here.
    with httpx.Client(timeout=HTTPX_TIMEOUT, follow_redirects=True) as http_client:
        response = http_client.get(url)
        response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    return soup.get_text(separator="\n")


def fetch_via_requests(mosque, retries: int = 3, backoff: float = 3.0):
    url = mosque.get("scrape_url") or mosque["website"]
    with mosque_scope(mosque["name"], op="scrape.fetch"):
        for attempt in range(1, retries + 1):
            try:
                text = fetch_page_text(url)
            except Exception as e:
                if attempt == retries:
                    logger.error(
                        "Fetch failed for %s after %d attempts",
                        mosque["name"],
                        retries,
                        exc_info=e,
                        extra={"url": url, "attempts": retries},
                    )
                    return None
                logger.warning(
                    "Fetch attempt %d/%d failed for %s: %s",
                    attempt,
                    retries,
                    mosque["name"],
                    e,
                    extra={"url": url, "attempt": attempt},
                )
                time.sleep(backoff * attempt)
                continue

            if attempt > 1:
                logger.info("Fetch for %s succeeded on attempt %d", mosque["name"], attempt)
            return {**mosque, "raw_text": text}


async def scrape_all_mosques():
    """Fetch every mosque's page text sequentially via httpx. Failed fetches come back as MosqueScrapeError."""
    results = []
    for mosque in MOSQUES:
        page = await asyncio.to_thread(fetch_via_requests, mosque)
        results.append(page or MosqueScrapeError(mosque["name"], STAGE_FETCH))
    return results
