"""
scheduler.py — APScheduler görev yöneticisi

Zaman dilimine göre akıllı tarama aralığı:
  ☀️  08:00 – 18:59  →  Her 15 dakikada bir  (aktif mesai)
  🌆  19:00 – 23:59  →  Her 45 dakikada bir  (akşam saatleri)
  🌙  00:00 – 07:59  →  Tarama yok           (gece sessiz saati)

/tara komutu her zaman çalışır — zaman dilimini atlar.
"""

import logging
from datetime import datetime

import pytz
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

import config
import database
import notifier
from scrapers import KariyerScraper, JobSpyScraper, CompanyScraper

logger = logging.getLogger("scheduler")

TZ = pytz.timezone("Europe/Istanbul")

# ─── Zaman Dilimi Tanımları ──────────────────────────────────────────────────
#
#  DAY   : 08:00 – 18:59  → aktif mesai, 15 dk
#  EVE   : 19:00 – 23:59  → akşam, 45 dk
#  NIGHT : 00:00 – 07:59  → gece, tarama yok
#
INTERVAL_DAY   = 15   # dakika — mesai saati
INTERVAL_EVE   = 45   # dakika — akşam saati
NIGHT_START_H  = 0    # gece başlangıcı
NIGHT_END_H    = 8    # gece bitişi (08:00 = gündüz başlar)
EVE_START_H    = 19   # akşam başlangıcı


def _get_window() -> str:
    """
    Şu anki zaman dilimine göre 'day' | 'eve' | 'night' döner.
    Tüm saatler Europe/Istanbul (TR) saat dilimine göredir.
    """
    hour = datetime.now(TZ).hour
    if NIGHT_START_H <= hour < NIGHT_END_H:   # 00–07
        return "night"
    elif EVE_START_H <= hour <= 23:            # 19–23
        return "eve"
    else:                                      # 08–18
        return "day"


def _is_quiet_hours() -> bool:
    """Gece saati mi? (bot.py sessiz saat gösterimi için kullanır)"""
    return _get_window() == "night"


# Sessiz saat aralığı gösterimi için (bot.py /durum komutu)
QUIET_START = (NIGHT_START_H, 0)
QUIET_END   = (NIGHT_END_H,   0)


# ─── Scraping Döngüsü ────────────────────────────────────────────────────────
def run_scraping_cycle(force: bool = False) -> dict:
    """
    Tüm kaynakları tarar, yeni ilanları DB'ye kaydeder, Telegram'a bildirir.

    force=True → zaman dilimi kontrolünü atla (/tara komutu kullanır)
    """
    window = _get_window()

    # ── Gece Kontrolü ────────────────────────────────────────────────────────
    if not force and window == "night":
        now_str = datetime.now(TZ).strftime("%H:%M")
        logger.info(
            "🌙 Gece sessiz saati (%s). Tarama 08:00'e ertelendi.", now_str
        )
        return {"total_new": 0, "by_source": {}, "skipped": True, "window": "night"}

    window_label = {
        "day": f"☀️ Mesai ({INTERVAL_DAY} dk aralık)",
        "eve": f"🌆 Akşam ({INTERVAL_EVE} dk aralık)",
    }.get(window, window)

    logger.info("=" * 55)
    logger.info("Tarama döngüsü başlıyor... | %s", window_label)
    logger.info("=" * 55)

    scrapers = [
        KariyerScraper(),   # Kariyer.net — requests + BS4
        JobSpyScraper(),    # LinkedIn + Indeed — python-jobspy
        CompanyScraper(),   # Şirket kariyer sayfaları (Lever/Greenhouse API)
    ]

    total_new = 0
    stats_per_source: dict[str, int] = {}

    for scraper in scrapers:
        source = scraper.SOURCE_NAME
        logger.info("▶ %s taranıyor...", source)
        jobs = scraper.safe_scrape()

        new_count = 0
        for job in jobs:
            if database.save_job(job):
                new_count += 1
                notifier.send_job_alert(job)

        stats_per_source[source] = new_count
        total_new += new_count
        logger.info("✓ %s: %d yeni ilan", source, new_count)

    logger.info("=" * 55)
    logger.info("Döngü tamamlandı. Toplam yeni ilan: %d", total_new)
    logger.info("=" * 55)

    return {
        "total_new": total_new,
        "by_source": stats_per_source,
        "skipped": False,
        "window": window,
    }


# ─── DB Bakımı ───────────────────────────────────────────────────────────────
def run_db_cleanup():
    """30 günden eski ilanları sil."""
    deleted = database.cleanup_old_jobs(days=30)
    logger.info("Haftalık DB temizliği: %d eski kayıt silindi", deleted)


# ─── Scheduler Başlatma ──────────────────────────────────────────────────────
def create_scheduler() -> BackgroundScheduler:
    """
    APScheduler'ı 3 zaman dilimine göre yapılandırır.

    Mesai (08:00–18:59)  → CronTrigger: her 15 dakikada
    Akşam (19:00–23:59)  → CronTrigger: her 45 dakikada
    Gece  (00:00–07:59)  → Görev yok (hiç tetiklenmez)
    """
    scheduler = BackgroundScheduler(
        timezone="Europe/Istanbul",
        job_defaults={
            "coalesce": True,           # Gecikmiş çalışmaları birleştir
            "max_instances": 1,         # Aynı anda tek instance
            "misfire_grace_time": 300,  # 5 dk gecikmeye tolerans
        },
    )

    # ── Görev 1: Mesai Taraması (08:00 – 18:59, her 15 dk) ──────────────────
    # minute='0,15,30,45' → 08:00, 08:15, 08:30, 08:45, 09:00 ... 18:45
    scheduler.add_job(
        run_scraping_cycle,
        trigger=CronTrigger(
            hour="8-18",
            minute="0,15,30,45",
            timezone=TZ,
        ),
        id="scraping_day",
        name=f"Mesai Tarama (her {INTERVAL_DAY} dk)",
        replace_existing=True,
    )

    # ── Görev 2: Akşam Taraması (19:00 – 23:59, her 45 dk) ─────────────────
    # 19:00, 19:45, 20:30, 21:15, 22:00, 22:45, 23:30
    scheduler.add_job(
        run_scraping_cycle,
        trigger=CronTrigger(
            hour="19-23",
            minute="0,45",
            timezone=TZ,
        ),
        id="scraping_eve",
        name=f"Akşam Tarama (her {INTERVAL_EVE} dk)",
        replace_existing=True,
    )

    # ── Görev 3: Haftalık DB Bakımı (Pazartesi 08:00) ────────────────────────
    scheduler.add_job(
        run_db_cleanup,
        trigger=CronTrigger(day_of_week="mon", hour=8, minute=5, timezone=TZ),
        id="db_cleanup",
        name="Haftalık DB Temizliği",
        replace_existing=True,
    )

    logger.info(
        "Scheduler hazır:\n"
        "  ☀️  08:00–18:59 → her %d dakika\n"
        "  🌆  19:00–23:59 → her %d dakika\n"
        "  🌙  00:00–07:59 → tarama yok",
        INTERVAL_DAY,
        INTERVAL_EVE,
    )
    return scheduler
