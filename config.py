"""
config.py — Tüm uygulama ayarları
.env dosyasını okur ve tek bir Config nesnesi üzerinden sunar.
"""

import os
import logging
from dotenv import load_dotenv

load_dotenv()

# ─── Logging ────────────────────────────────────────────────────────────────
LOG_PATH = os.getenv("LOG_PATH", "bot.log")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler(LOG_PATH, encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger("config")

# ─── Telegram ───────────────────────────────────────────────────────────────
TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID: str = os.getenv("TELEGRAM_CHAT_ID", "")

if not TELEGRAM_BOT_TOKEN:
    logger.warning("TELEGRAM_BOT_TOKEN boş! .env dosyanızı kontrol edin.")
if not TELEGRAM_CHAT_ID:
    logger.warning("TELEGRAM_CHAT_ID boş! .env dosyanızı kontrol edin.")

# ─── Zamanlama ─────────────────────────────────────────────────────────────
# Tarama aralıkları scheduler.py içinde INTERVAL_DAY / INTERVAL_EVE olarak tanımlıdır.
# Sessiz saatler: 00:00–07:59 (şemasüstü tamamen sabit, değiştirilmez)

# ─── Veritabanı ─────────────────────────────────────────────────────────────
DB_PATH: str = os.getenv("DB_PATH", "jobs.db")

# ─── Proxy ──────────────────────────────────────────────────────────────────
PROXY_URL: str | None = os.getenv("PROXY_URL") or None

# ─── Arama Sorguları ────────────────────────────────────────────────────────
# (Türkçe + İngilizce kombinasyonları)
SEARCH_QUERIES: list[str] = [
    "junior java", "junior backend", "junior spring boot", "new grad java",
    "junior python", "junior data scientist", "junior data engineer",
    "junior veri bilimci", "yeni mezun veri mühendisi",
    "junior software engineer", "new grad software engineer", "yeni mezun yazılım",
    "junior frontend", "junior full stack", "junior .net", "junior mobile developer",
    "junior QA engineer", "junior devops", "junior cloud engineer",
    "junior machine learning", "junior cyber security", "junior embedded software",
    "junior sap abap", "graduate program", "management trainee", "genç yetenek",
    "uzman yardımcısı",
]

# Teknolojik hedeflerimiz — broad aramalar sonrasında hedeflenen işleri filtreler
TECH_KEYWORDS: list[str] = [
    "java", "spring", "python", "data", "veri", "abap", "sap"
]

SEARCH_LOCATION: str = "Istanbul, Turkey"

# ─── Kara Liste Kelimeleri ───────────────────────────────────────────────────
# Bu kelimelerden birini içeren ilanlar filtrelenir
BLACKLIST_KEYWORDS: list[str] = [
    "senior",
    "lead",
    "manager",
    "müdür",
    "direktör",
    "baş ",
    "3+ yıl",
    "4+ yıl",
    "5+ yıl",
    "6+ yıl",
    "3 yıl",
    "4 yıl",
    "5 yıl",
    "experienced",
    "mid-level",
    "mid level",
    "principal",
    "staff engineer",
    "tech lead",
    "team lead",
]

# ─── Whitelist Kelimeleri ────────────────────────────────────────────────────
# İlanlarda bu kelimelerden en az biri olmalı (başlıkta geçerse kabul)
WHITELIST_KEYWORDS: list[str] = [
    "junior",
    "jr",
    "jr.",
    "entry",
    "yeni mezun",
    "stajyer",
    "intern",
    "graduate",
    "0-1 yıl",
    "0-2 yıl",
    "1 yıl",
    "fresher",
]


# Sirket sayfalari ayri bir gorevle gece dahil izlenir.
COMPANY_INTERVAL_MINUTES = max(5, int(os.getenv("COMPANY_INTERVAL_MINUTES", "15")))
KARIYER_ENABLED = os.getenv("KARIYER_ENABLED", "false").lower() == "true"
