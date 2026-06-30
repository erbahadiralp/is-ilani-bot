"""
scrapers/kariyer.py — Kariyer.net scraper

requests + BeautifulSoup4 kullanır (JavaScript gerektirmiyor).
Her query için ayrı istek atar, sonuçları birleştirir.
"""

import logging
import urllib.parse

import requests
from bs4 import BeautifulSoup

import config
from .base import BaseScraper

logger = logging.getLogger("scraper.kariyer")


class KariyerScraper(BaseScraper):
    SOURCE_NAME = "kariyer"

    BASE_URL = "https://www.kariyer.net/is-ilanlari"

    def scrape(self) -> list[dict]:
        """Kariyer.net'i tüm sorgular için tara."""
        import tls_client

        all_jobs: list[dict] = []
        seen_urls: set[str] = set()

        # Create one session to persist cookies/headers like a real browser
        session = tls_client.Session(
            client_identifier="chrome_120",
            random_tls_extension_order=True
        )

        for query in config.SEARCH_QUERIES:
            self.logger.info("Kariyer.net sorgu: '%s'", query)
            try:
                jobs = self._scrape_query(session, query)
                for job in jobs:
                    url = job["url"]
                    if url not in seen_urls:
                        seen_urls.add(url)
                        all_jobs.append(job)
            except Exception as e:
                self.logger.warning("Kariyer.net sorgu hatası ('%s'): %s", query, e)
            self.random_sleep(3, 6) # slightly longer sleep to avoid detection

        return all_jobs

    def _scrape_query(self, session, query: str) -> list[dict]:
        """Tek bir sorgu için Kariyer.net'i tara."""
        params = {
            "q": query,
            "city": "istanbul",
        }
        url = f"{self.BASE_URL}?{urllib.parse.urlencode(params)}"

        headers = {
            "Accept-Language": "tr-TR,tr;q=0.9,en;q=0.8",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Referer": "https://www.kariyer.net/",
        }

        proxy_url = config.PROXY_URL or None

        resp = session.get(
            url,
            headers=headers,
            proxy=proxy_url,
            timeout_seconds=15,
            allow_redirects=True,
        )
        if resp.status_code != 200:
            raise Exception(f"HTTP {resp.status_code}")

        return self._parse(resp.text)

    def _parse(self, html: str) -> list[dict]:
        """HTML'den ilan kartlarını parse et."""
        soup = BeautifulSoup(html, "html.parser")
        jobs: list[dict] = []

        # Kariyer.net ilan kartları — class adı değişebilir, birden fazla selector dene
        # Birincil selector: liste item
        cards = soup.select("div.job-list-item")
        if not cards:
            # Alternatif selector (sayfa yapısı değişmişse)
            cards = soup.select("article.job-item")
        if not cards:
            cards = soup.select("[class*='job-list']")

        self.logger.debug("Kariyer.net: %d kart bulundu", len(cards))

        for card in cards:
            try:
                job = self._parse_card(card)
                if job and self.passes_filter(job["title"]):
                    jobs.append(job)
            except Exception as e:
                self.logger.debug("Kart parse hatası: %s", e)
                continue

        # Eğer yukarıdaki selector'lar çalışmazsa, JSON LD dene
        if not jobs:
            jobs = self._parse_json_ld(soup)

        return jobs

    def _parse_card(self, card) -> dict | None:
        """Tek bir ilan kartını dict'e çevir."""
        # Başlık
        title_el = (
            card.select_one("h3 a")
            or card.select_one("h2 a")
            or card.select_one("a.job-title")
            or card.select_one("[class*='title']")
        )
        if not title_el:
            return None
        title = title_el.get_text(strip=True)

        # URL
        href = title_el.get("href", "")
        if href.startswith("http"):
            url = href
        elif href:
            url = f"https://www.kariyer.net{href}"
        else:
            return None

        # Firma
        company_el = (
            card.select_one("[class*='company']")
            or card.select_one("[class*='employer']")
            or card.select_one("span.company-name")
        )
        company = company_el.get_text(strip=True) if company_el else "Belirtilmemiş"

        # Konum
        location_el = (
            card.select_one("[class*='location']")
            or card.select_one("[class*='city']")
            or card.select_one("span.location")
        )
        location = location_el.get_text(strip=True) if location_el else config.SEARCH_LOCATION

        return {
            "title": title,
            "company": company,
            "location": location,
            "source": self.SOURCE_NAME,
            "url": url,
        }

    def _parse_json_ld(self, soup: BeautifulSoup) -> list[dict]:
        """
        JSON-LD structured data'dan ilanları topla.
        Modern siteler bunu kullanır, daha güvenilir.
        """
        import json

        jobs = []
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                data = json.loads(script.string or "")
                if isinstance(data, list):
                    items = data
                elif isinstance(data, dict):
                    items = [data]
                else:
                    continue
                for item in items:
                    if item.get("@type") == "JobPosting":
                        title = item.get("title", "")
                        if not title or not self.passes_filter(title):
                            continue
                        org = item.get("hiringOrganization", {})
                        company = (
                            org.get("name", "Belirtilmemiş")
                            if isinstance(org, dict)
                            else "Belirtilmemiş"
                        )
                        loc = item.get("jobLocation", {})
                        if isinstance(loc, dict):
                            addr = loc.get("address", {})
                            if isinstance(addr, dict):
                                location = addr.get("addressLocality", config.SEARCH_LOCATION)
                            else:
                                location = config.SEARCH_LOCATION
                        else:
                            location = config.SEARCH_LOCATION
                        url = item.get("url", "")
                        if not url:
                            continue
                        jobs.append(
                            {
                                "title": title,
                                "company": company,
                                "location": location,
                                "source": self.SOURCE_NAME,
                                "url": url,
                            }
                        )
            except (json.JSONDecodeError, AttributeError):
                continue
        return jobs
