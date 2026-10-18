import asyncio
import time

import httpx
from bs4 import BeautifulSoup
from mosques import MOSQUES

HTTPX_TIMEOUT = 20


def fetch_via_requests(mosque, retries: int = 3, backoff: float = 3.0):
    # NOTE: Some mosque WAFs (e.g. irccan.com) block requests that claim to be
    # a browser via a spoofed User-Agent but lack a matching browser TLS
    # fingerprint. A plain client with a consistent fingerprint is served
    # normally, so we intentionally do NOT send browser-spoofing headers here.
    url = mosque.get("scrape_url") or mosque["website"]
    for attempt in range(1, retries + 1):
        try:
            with httpx.Client(timeout=HTTPX_TIMEOUT, follow_redirects=True) as http_client:
                response = http_client.get(url)
                response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")
            for tag in soup(["script", "style", "noscript"]):
                tag.decompose()

            text = soup.get_text(separator="\n")
            if attempt > 1:
                print(f"[httpx] {mosque['name']} succeeded on attempt {attempt}")
            return {**mosque, "raw_text": text}
        except Exception as e:
            print(f"[httpx] Attempt {attempt}/{retries} failed for {mosque['name']}: {e}")
            if attempt < retries:
                time.sleep(backoff * attempt)

    print(f"[httpx] All {retries} attempts failed for {mosque['name']}")
    return None


async def scrape_all_mosques():
    """Fetch every mosque's page text sequentially via httpx."""
    return [await asyncio.to_thread(fetch_via_requests, m) for m in MOSQUES]
