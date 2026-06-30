"""
scrapers/jobspy_scraper.py — LinkedIn + Indeed scraper

python-jobspy kullanır: Playwright yok, proxy yok, kurulum basit.
JobSpy, LinkedIn'in iç /voyager/api/ endpoint'lerini kullandığı için
normal web scraping'den çok daha az bot tespitine maruz kalır.
"""

import logging
from typing import Optional

import config
from .base import BaseScraper

logger = logging.getLogger("scraper.jobspy")


class JobSpyScraper(BaseScraper):
    """
    LinkedIn ve Indeed TR'yi python-jobspy ile tara.
    Tek çağrıyla her iki kaynaktan da sonuç döner.
    """
    SOURCE_NAME = "jobspy"

    # JobSpy'ın döndürdüğü DataFrame sütun adları
    COLUMN_MAP = {
        "title":        "title",
        "company":      "company",
        "location":     "location",
        "job_url":      "url",
        "site":         "source",
    }

    def scrape(self) -> list[dict]:
        """LinkedIn + Indeed'i tüm sorgular için tara."""
        try:
            from jobspy import scrape_jobs
        except ImportError:
            raise ImportError(
                "python-jobspy kurulu değil. Çalıştırın: pip install python-jobspy"
            )

        all_jobs: list[dict] = []
        seen_urls: set[str] = set()

        for query in config.SEARCH_QUERIES:
            self.logger.info("JobSpy sorgu: '%s'", query)
            try:
                jobs = self._scrape_query(scrape_jobs, query)
                for job in jobs:
                    url = job.get("url", "")
                    if url and url not in seen_urls:
                        seen_urls.add(url)
                        all_jobs.append(job)
            except Exception as e:
                self.logger.error("JobSpy hata (query='%s'): %s", query, e)
            # Sorgular arası bekleme (rate limit)
            self.random_sleep(2, 5)

        self.logger.info("JobSpy toplam: %d benzersiz ilan", len(all_jobs))
        return all_jobs

    def _scrape_query(self, scrape_jobs_fn, query: str) -> list[dict]:
        """Tek bir sorgu için JobSpy çalıştır."""
        df = scrape_jobs_fn(
            site_name=["linkedin", "indeed"],
            search_term=query,
            location=config.SEARCH_LOCATION,
            results_wanted=15,          # Sorgu başına max ilan
            hours_old=24 * 7,           # Son 7 günlük ilanlar
            country_indeed="Turkey",
            linkedin_fetch_description=False,  # Hız için açıklama getirme
            verbose=0,                  # Log sessiz
        )

        if df is None or df.empty:
            return []

        jobs = []
        for _, row in df.iterrows():
            try:
                job = self._row_to_job(row)
                if job and self.passes_filter(job["title"]):
                    jobs.append(job)
            except Exception as e:
                self.logger.debug("Satır parse hatası: %s", e)

        return jobs

    def _row_to_job(self, row) -> Optional[dict]:
        """DataFrame satırını job dict'ine çevir."""
        title   = str(row.get("title",   "") or "").strip()
        company = str(row.get("company", "") or "").strip()
        location= str(row.get("location","") or "").strip()
        url     = str(row.get("job_url", "") or "").strip()
        site    = str(row.get("site",    "") or "").strip().lower()

        if not title or not url:
            return None

        # Kaynak adını normalize et
        source_map = {
            "linkedin": "linkedin",
            "indeed":   "indeed",
        }
        source = source_map.get(site, site)

        return {
            "title":    title,
            "company":  company or "Belirtilmemiş",
            "location": location or config.SEARCH_LOCATION,
            "source":   source,
            "url":      url,
        }
