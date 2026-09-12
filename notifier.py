"""
notifier.py — Telegram bildirim gönderici
- Yeni ilan bildirimleri (🚀 formatı)
- Hata alarmları (🚨 formatı)
- Rate limit koruması (mesajlar arası bekleme)

NOT: APScheduler thread'leri ve python-telegram-bot v20 event loop'u çakışmasını
önlemek için mesaj gönderimi doğrudan Telegram HTTP API'si üzerinden requests
ile yapılır (asyncio kullanılmaz).
"""

from html import escape
import logging
import time
from datetime import datetime

import requests

import config

logger = logging.getLogger("notifier")

TELEGRAM_API_BASE = "https://api.telegram.org/bot{token}/sendMessage"


# ─── Mesaj Gönderici ────────────────────────────────────────────────────────
def _send_message(text: str, parse_mode: str = "HTML", retry: int = 3) -> bool:
    """
    Telegram Bot API'sine doğrudan HTTP POST ile mesaj gönderir.
    Thread-safe — APScheduler thread'lerinden güvenle çağrılabilir.
    Rate limit durumunda bekler ve yeniden dener.
    """
    if not config.TELEGRAM_BOT_TOKEN or not config.TELEGRAM_CHAT_ID:
        logger.error("Telegram kimlik bilgileri eksik! .env dosyasını kontrol edin.")
        return False

    url = TELEGRAM_API_BASE.format(token=config.TELEGRAM_BOT_TOKEN)
    payload = {
        "chat_id": config.TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": parse_mode,
        "disable_web_page_preview": True,
    }

    for attempt in range(retry):
        try:
            resp = requests.post(url, json=payload, timeout=10)
            if resp.status_code == 200:
                return True
            elif resp.status_code == 429:
                # Rate limit — Retry-After başlığını oku
                retry_after = int(resp.json().get("parameters", {}).get("retry_after", 5))
                logger.warning("Telegram rate limit! %d saniye bekleniyor...", retry_after)
                time.sleep(retry_after + 1)
            else:
                logger.error(
                    "Telegram API hatası (deneme %d/%d): HTTP %d — %s",
                    attempt + 1,
                    retry,
                    resp.status_code,
                    resp.text[:200],
                )
                if attempt < retry - 1:
                    time.sleep(2)
        except requests.RequestException as e:
            logger.error(
                "Telegram bağlantı hatası (deneme %d/%d): %s",
                attempt + 1,
                retry,
                e,
            )
            if attempt < retry - 1:
                time.sleep(3)

    return False


# ─── İlan Bildirimi ─────────────────────────────────────────────────────────
def send_job_alert(job: dict) -> bool:
    """
    Yeni iş ilanı bildirimi gönder.

    Beklenen job anahtarları:
        title, company, location, source, url
    """
    job = {k: escape(str(v), quote=True) for k, v in job.items()}
    source_emoji = {
        "linkedin": "💼",
        "kariyer":  "🇹🇷",
        "indeed":   "🔍",
        "company":  "🏢",
    }
    emoji = source_emoji.get(job.get("source", "").lower(), "📋")

    source_display = {
        "linkedin": "LinkedIn",
        "kariyer":  "Kariyer.net",
        "indeed":   "Indeed TR",
        "company":  "Şirket Sayfası",
    }.get(job.get("source", "").lower(), job.get("source", "Bilinmiyor"))

    text = (
        ("📣 <b>PROGRAM SAYFASI DEĞİŞTİ</b>\n" if job.get("source") == "program" else "🚀 <b>YENİ İLAN BULDUM!</b>\n")
        +
        "\n"
        f"{emoji} <b>Kaynak:</b> {source_display}\n"
        f"🏢 <b>Firma:</b> {job.get('company', 'Belirtilmemiş')}\n"
        f"👤 <b>Pozisyon:</b> {job.get('title', 'Belirtilmemiş')}\n"
        f"📍 <b>Konum:</b> {job.get('location', 'Belirtilmemiş')}\n"
        f"🎓 <b>Program:</b> {job.get('program', '') or '—'}\n"
        f"{job.get('note', '')}\n"
        "\n"
        f'<a href="{job.get("url", "#")}">📎 İlana Git / Başvur</a>'
    )

    result = _send_message(text)
    if result:
        logger.info("İlan bildirimi gönderildi: %s", job.get("title"))
    # Rate limit koruması: mesajlar arası 1.5 saniye bekle
    time.sleep(1.5)
    return result


# Hata bildirimlerini sınırlamak için son gönderim zamanlarını tutan dict
_last_error_times: dict[str, float] = {}


def send_error_alert(source: str, error: Exception) -> bool:
    """
    Scraper hatası durumunda Telegram'a hata alarmı gönder.
    Aynı kaynak için 6 saatte en fazla 1 kez alarm gönderilir (spam önleme).
    """
    now_ts = time.time()
    last_sent = _last_error_times.get(source, 0.0)

    # 6 saat = 21600 saniye
    if now_ts - last_sent < 21600:
        logger.info("Hata alarmı gönderilmedi (rate-limited): %s — %s", source, error)
        return False

    _last_error_times[source] = now_ts

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    text = (
        f"🚨 <b>HATA: {source} taraması çöktü!</b>\n"
        "\n"
        f"❌ <b>Hata:</b> <code>{type(error).__name__}: {str(error)[:300]}</code>\n"
        f"🕐 <b>Zaman:</b> {now}\n"
        "\n"
        f"<i>💡 Not: Bu kaynak için hata alarmları 6 saat boyunca susturuldu.</i>"
    )
    result = _send_message(text)
    if result:
        logger.info("Hata alarmı gönderildi: %s — %s", source, error)
    return result


# ─── Durum Mesajı ───────────────────────────────────────────────────────────
def send_status_message(stats: dict, interval: int) -> bool:
    """
    Bot durum mesajı gönder (/start, /durum komutları için kullanılır).
    """
    total = stats.get("total", 0)
    by_source = stats.get("by_source", {})
    last_found = stats.get("last_found_at", "Henüz yok")

    source_lines = "\n".join(
        f"  • {k}: {v} ilan" for k, v in by_source.items()
    ) or "  • Henüz ilan bulunamadı"

    text = (
        "🤖 <b>Job Hunter Bot — Aktif</b>\n"
        "\n"
        f"📊 <b>Toplam takip edilen ilan:</b> {total}\n"
        "\n"
        "<b>Kaynağa göre dağılım:</b>\n"
        f"{source_lines}\n"
        "\n"
        f"🕐 <b>Son tarama sonucu:</b> {last_found}\n"
        f"⏱ <b>Tarama aralığı:</b> Her {interval} dakika\n"
        "\n"
        "📌 <b>Komutlar:</b>\n"
        "  /tara — Anlık tarama başlat\n"
        "  /durum — Bu mesajı göster"
    )
    return _send_message(text)
