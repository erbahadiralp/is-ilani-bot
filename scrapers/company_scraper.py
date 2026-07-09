"""
scrapers/company_scraper.py — Şirket kariyer sayfası izleyici

Desteklenen yöntemler:
  1. Lever ATS   — JSON API (api.lever.co) — en güvenilir
  2. Greenhouse  — JSON API (boards-api.greenhouse.io) — güvenilir
  3. Generic     — requests + BeautifulSoup ile HTML parse

companies.json dosyasından şirket listesini okur.
Yeni ilan tespiti için URL hash bazlı mükerrer kontrolü yapılır.
"""

import hashlib
import json
import logging
import os
import urllib.parse

import requests
from bs4 import BeautifulSoup

import config
from .base import BaseScraper

logger = logging.getLogger("scraper.company")

# companies.json dosyasının yolu (proje kökü)
COMPANIES_FILE = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "companies.json"
)

# SAP/ABAP + Junior ile ilgili ek whitelist
SAP_KEYWORDS = [
    "sap", "abap", "s/4hana", "s4hana", "fiori", "bw", "bapi",
    "sap basis", "sap mm", "sap sd", "sap fi", "sap hr", "sap pm",
    "sap qm", "sap wm", "sap ewm",
]

# Şirket ilanları için özel whitelist — daha geniş tutar
# (şirket sitelerinde "junior" yazmıyor olabilir, pozisyon adı yeterli)
COMPANY_WHITELIST = config.WHITELIST_KEYWORDS + SAP_KEYWORDS + [
    "developer",
    "engineer",
    "analyst",
    "geliştirici",
    "mühendis",
    "uzman yardımcısı",
    "uzman yard.",
]


class CompanyScraper(BaseScraper):
    """
    Şirket kariyer sayfalarını izler.
    Lever, Greenhouse ATS JSON API'lerini ve generic HTML scraping'i destekler.
    """
    SOURCE_NAME = "company"

    def __init__(self):
        super().__init__()
        self.companies = self._load_companies()

    def _get_request(self, url: str, headers: dict = None, proxies: dict = None, timeout: int = 15) -> requests.Response:
        """SSL hatası durumunda verify=False ile tekrar deneyen güvenli requests sarmalayıcısı."""
        try:
            resp = requests.get(url, headers=headers, proxies=proxies, timeout=timeout)
            resp.raise_for_status()
            return resp
        except requests.exceptions.SSLError:
            self.logger.warning("SSL doğrulama hatası, doğrulamayı devre dışı bırakarak tekrar deneniyor: %s", url)
            resp = requests.get(url, headers=headers, proxies=proxies, timeout=timeout, verify=False)
            resp.raise_for_status()
            return resp

    def _load_companies(self) -> list[dict]:
        """companies.json'dan şirket listesini yükle."""
        try:
            with open(COMPANIES_FILE, encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            self.logger.error("companies.json bulunamadı: %s", COMPANIES_FILE)
            return []
        except json.JSONDecodeError as e:
            self.logger.error("companies.json parse hatası: %s", e)
            return []

    def scrape(self) -> list[dict]:
        """Tüm şirketlerin kariyer sayfalarını tara."""
        all_jobs: list[dict] = []
        seen_urls: set[str] = set()

        for company in self.companies:
            name = company.get("name", "?")
            ctype = company.get("type", "generic")
            self.logger.info("Şirket taranıyor: %s (%s)", name, ctype)

            try:
                if ctype == "lever":
                    jobs = self._scrape_lever(company)
                elif ctype == "greenhouse":
                    jobs = self._scrape_greenhouse(company)
                elif ctype == "teamtailor":
                    jobs = self._scrape_teamtailor(company)
                else:
                    jobs = self._scrape_generic(company)

                for job in jobs:
                    url = job.get("url", "")
                    if url and url not in seen_urls:
                        seen_urls.add(url)
                        all_jobs.append(job)

                self.logger.info("  → %s: %d ilan bulundu", name, len(jobs))
            except Exception as e:
                self.logger.error("  → %s tarama hatası: %s", name, e)

            self.random_sleep(1, 3)

        return all_jobs

    # ─── Lever ATS ───────────────────────────────────────────────────────────
    def _scrape_lever(self, company: dict) -> list[dict]:
        """
        Lever ATS JSON API'si.
        https://api.lever.co/v0/postings/{company}?mode=json
        Tüm ilanları JSON olarak döner — scraping gerekmez.
        """
        api_url = company.get("api_url")
        if not api_url:
            return []

        headers = {"User-Agent": self.rotate_user_agent()}
        resp = self._get_request(api_url, headers=headers, timeout=15)

        data = resp.json()
        if not isinstance(data, list):
            return []

        jobs = []
        for item in data:
            title = item.get("text", "")
            if not title:
                continue
            if not self._passes_company_filter(title):
                continue

            location = ""
            categories = item.get("categories", {})
            if isinstance(categories, dict):
                location = categories.get("location", "") or categories.get("city", "") or ""
            if not location:
                location = "Belirtilmemiş"

            url = item.get("hostedUrl", "") or item.get("applyUrl", "")
            if not url:
                continue

            jobs.append({
                "title": title,
                "company": company["name"],
                "location": location,
                "source": "company",
                "url": url,
            })

        return jobs

    # ─── Greenhouse ATS ──────────────────────────────────────────────────────
    def _scrape_greenhouse(self, company: dict) -> list[dict]:
        """
        Greenhouse ATS JSON API'si.
        https://boards-api.greenhouse.io/v1/boards/{company}/jobs
        """
        api_url = company.get("api_url")
        if not api_url:
            return []

        headers = {"User-Agent": self.rotate_user_agent()}
        resp = self._get_request(api_url, headers=headers, timeout=15)

        data = resp.json()
        job_list = data.get("jobs", []) if isinstance(data, dict) else []

        jobs = []
        for item in job_list:
            title = item.get("title", "")
            if not title:
                continue
            if not self._passes_company_filter(title):
                continue

            # Konum
            location = ""
            loc = item.get("location", {})
            if isinstance(loc, dict):
                location = loc.get("name", "")
            if not location:
                location = "Belirtilmemiş"

            url = item.get("absolute_url", "")
            if not url:
                continue

            jobs.append({
                "title": title,
                "company": company["name"],
                "location": location,
                "source": "company",
                "url": url,
            })

        return jobs

    # ─── Teamtailor ATS ──────────────────────────────────────────────────────
    def _scrape_teamtailor(self, company: dict) -> list[dict]:
        """
        Teamtailor ATS JSON API'si.
        https://{slug}.teamtailor.com/jobs.json
        """
        url = company.get("url") or company.get("api_url")
        if not url:
            return []

        parsed = urllib.parse.urlparse(url)
        base_url = f"{parsed.scheme}://{parsed.netloc}"
        api_url = f"{base_url}/jobs.json"

        headers = {"User-Agent": self.rotate_user_agent()}
        try:
            resp = self._get_request(api_url, headers=headers, timeout=15)
            data = resp.json()
        except Exception as e:
            self.logger.debug("Teamtailor API hatası (%s): %s", company["name"], e)
            return []

        job_list = data if isinstance(data, list) else data.get("jobs", [])
        jobs = []

        for item in job_list:
            title = item.get("title", "") or item.get("name", "")
            if not title:
                continue
            if not self._passes_company_filter(title):
                continue

            location = "Belirtilmemiş"
            loc = item.get("location", {})
            if isinstance(loc, dict):
                location = loc.get("name") or loc.get("city") or "Belirtilmemiş"

            job_url = item.get("absolute_url") or item.get("url") or url

            jobs.append({
                "title": title,
                "company": company["name"],
                "location": location,
                "source": "company",
                "url": job_url,
            })

        return jobs

    # ─── Generic HTML ────────────────────────────────────────────────────────
    def _scrape_generic(self, company: dict) -> list[dict]:
        """
        requests + BeautifulSoup ile HTML scraping.
        CSS selector ile ilan linklerini toplar.
        """
        url = company.get("url", "")
        selector = company.get("selector", "a[href*='job'], a[href*='kariyer']")

        if not url:
            return []

        headers = {
            "User-Agent": self.rotate_user_agent(),
            "Accept-Language": "tr-TR,tr;q=0.9,en;q=0.8",
            "Referer": url,
        }
        proxies = self.get_proxy_url()

        resp = self._get_request(url, headers=headers, proxies=proxies, timeout=15)

        soup = BeautifulSoup(resp.text, "html.parser")
        jobs = []
        seen_texts: set[str] = set()

        # Selector ile ilan elementlerini bul
        elements = soup.select(selector)
        if not elements:
            # Geniş fallback: tüm linklere bak
            elements = soup.find_all("a", href=True)

        base_domain = urllib.parse.urlparse(url).scheme + "://" + urllib.parse.urlparse(url).netloc

        for el in elements:
            text = el.get_text(strip=True)
            if not text or len(text) < 5 or len(text) > 200:
                continue
            if text in seen_texts:
                continue

            # Menü, hakkımızda, iletişim gibi iş ilanı olmayan yönlendirme linklerini ele
            nav_blacklist = [
                "takım", "süreç", "mülakat", "fırsat", "hakkımızda", "giriş", "üye", "kayıt",
                "biz kimiz", "iletişim", "anasayfa", "home", "about", "contact", "login",
                "register", "signin", "signup", "site haritası", "sitemap", "gizlilik", "privacy",
                "kvkk", "çerez", "cookie", "kurumsal", "yardım", "destek", "career", "kariyer",
                "programı", "yetenek", "bize ulaşın", "insan kaynakları", "haberler", "duyuru",
                "künye", "vizyon", "misyon"
            ]
            text_lower = text.lower()
            if any(term in text_lower for term in nav_blacklist):
                continue

            if not self._passes_company_filter(text):
                continue

            href = el.get("href", "")
            if not href or href == "#" or href.startswith("javascript"):
                continue

            if href.startswith("http"):
                job_url = href
            elif href.startswith("/"):
                job_url = base_domain + href
            else:
                job_url = base_domain + "/" + href

            seen_texts.add(text)
            jobs.append({
                "title": text,
                "company": company["name"],
                "location": "Belirtilmemiş",
                "source": "company",
                "url": job_url,
            })

        return jobs[:30]  # Şirket başına max 30 ilan

    def _passes_company_filter(self, title: str) -> bool:
        """
        Şirket ilanları için filtre.
        - Kara listedeki kelimelerden herhangi biri varsa → REDDEDİLDİ
        - Hedef teknolojilerden en az birini içermeli (Java, Python, Data, SAP/ABAP)
        - Hedef pozisyon rollerinden birini içermeli (Junior, Developer, Engineer vb.)
        """
        title_lower = title.lower()

        # 1. Kara liste kontrolü (senior/lead/müdür elensin)
        for kw in config.BLACKLIST_KEYWORDS:
            if kw.lower() in title_lower:
                return False

        # 2. Teknoloji kontrolü (Java, Python, Data, SAP/ABAP)
        has_tech = False
        for kw in config.TECH_KEYWORDS:
            if kw.lower() in title_lower:
                has_tech = True
                break
        if not has_tech:
            return False

        # 3. Rol/Pozisyon kontrolü (Junior, Developer, Engineer, Uzman Yardımcısı vb.)
        has_role = False
        for kw in COMPANY_WHITELIST:
            if kw.lower() in title_lower:
                has_role = True
                break
        if not has_role:
            return False

        return True
