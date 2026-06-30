"""
scrapers/base.py — Ortak scraper altyapısı

Tüm scraper'ların miras alacağı BaseScraper sınıfı:
- User-agent rotasyonu (fake-useragent)
- Anti-bot random sleep
- Proxy yönlendirmesi
- Keyword filtresi (whitelist/blacklist)
- Hata yakalama ve Telegram alarmı
"""

import logging
import random
import time
from abc import ABC, abstractmethod

try:
    from fake_useragent import UserAgent
    _ua = UserAgent()
except Exception:
    _ua = None

import config

logger = logging.getLogger("scraper.base")


class BaseScraper(ABC):
    """Tüm scraper'ların temel sınıfı."""

    SOURCE_NAME: str = "base"  # Alt sınıflar override eder

    def __init__(self):
        self.logger = logging.getLogger(f"scraper.{self.SOURCE_NAME}")

    # ─── Anti-Bot Yardımcıları ───────────────────────────────────────────────
    @staticmethod
    def rotate_user_agent() -> str:
        """Rastgele bir User-Agent döner."""
        if _ua:
            try:
                return _ua.random
            except Exception:
                pass
        # Fallback UA listesi
        fallback = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64; rv:124.0) Gecko/20100101 Firefox/124.0",
        ]
        return random.choice(fallback)

    @staticmethod
    def random_sleep(min_sec: float = 1.5, max_sec: float = 4.5) -> None:
        """Anti-bot: rastgele bekleme süresi."""
        sleep_time = random.uniform(min_sec, max_sec)
        time.sleep(sleep_time)

    @staticmethod
    def get_proxy_url() -> dict | None:
        """requests için proxy dict döner (Kariyer.net için)."""
        if config.PROXY_URL:
            return {"http": config.PROXY_URL, "https": config.PROXY_URL}
        return None

    def passes_filter(self, title: str) -> bool:
        """
        İlan başlığı filtreden geçiyor mu?
        - Teknoloji hedeflerimizden en az birini içermeli (Java, Python, Data, SAP/ABAP)
        - Kara listedeki kelimelerden herhangi biri varsa → REDDEDİLDİ
        - Beyaz listedeki kelimelerden en az birini içermeli → KABUL EDİLDİ
        """
        title_lower = title.lower()

        # 1. Teknoloji filtre kontrolü
        has_tech = False
        for kw in config.TECH_KEYWORDS:
            if kw.lower() in title_lower:
                has_tech = True
                break
        if not has_tech:
            self.logger.debug("Teknoloji eşleşmedi: %s", title)
            return False

        # 2. Kara liste kontrolü
        for kw in config.BLACKLIST_KEYWORDS:
            if kw.lower() in title_lower:
                self.logger.debug("Kara liste eşleşti ('%s'): %s", kw, title)
                return False

        # 3. Beyaz liste kontrolü
        for kw in config.WHITELIST_KEYWORDS:
            if kw.lower() in title_lower:
                return True

        return True

    # ─── Soyut Metot ─────────────────────────────────────────────────────────
    @abstractmethod
    def scrape(self) -> list[dict]:
        """
        Kaynağı tara ve ilanları döner.

        Her eleman şu anahtarları içermeli:
            title (str), company (str), location (str),
            source (str), url (str)
        """
        ...

    # ─── Güvenli Çalıştırma ──────────────────────────────────────────────────
    def safe_scrape(self) -> list[dict]:
        """
        scrape() metodunu güvenli çalıştırır.
        Hata oluşursa Telegram'a alarm gönderir, boş liste döner.
        """
        try:
            results = self.scrape()
            self.logger.info(
                "%s taraması tamamlandı: %d ilan bulundu",
                self.SOURCE_NAME,
                len(results),
            )
            return results
        except Exception as e:
            self.logger.error(
                "%s taraması çöktü: %s: %s",
                self.SOURCE_NAME,
                type(e).__name__,
                e,
                exc_info=True,
            )
            # Telegram hata alarmı — döngüsel import'u önlemek için lazy import
            try:
                from notifier import send_error_alert
                send_error_alert(self.SOURCE_NAME, e)
            except Exception as notify_err:
                self.logger.error("Hata alarmı gönderilemedi: %s", notify_err)
            return []
