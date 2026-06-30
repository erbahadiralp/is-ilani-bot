"""
bot.py — Telegram Bot komut işleyicileri

Desteklenen komutlar:
  /start  — Bot durumu
  /durum  — Bot durumu (aynı)
  /tara   — Anlık manuel tarama başlat
"""

import logging
import threading

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)

import config
import database
import notifier

logger = logging.getLogger("bot")


# ─── /start ve /durum ────────────────────────────────────────────────────────
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Bot durumu ve istatistikleri göster."""
    stats = database.get_stats()
    await update.message.reply_text(
        _build_status_text(stats),
        parse_mode="HTML",
        disable_web_page_preview=True,
    )


async def cmd_durum(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/durum — /start ile aynı."""
    await cmd_start(update, context)


# ─── /tara ──────────────────────────────────────────────────────────────────
async def cmd_tara(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Manuel anlık tarama başlat. Gece saati olsa bile çalışır."""
    from scheduler import _get_window, INTERVAL_DAY, INTERVAL_EVE

    window = _get_window()
    window_notes = {
        "night": "\n⚠️ <i>Gece saati (00:00–07:59) aktif, ama /tara komutu yine de çalışıyor.</i>",
        "day":   f"\n☀️ <i>Mesai saati — normal tarama aralığı {INTERVAL_DAY} dk.</i>",
        "eve":   f"\n🌆 <i>Akşam saati — normal tarama aralığı {INTERVAL_EVE} dk.</i>",
    }
    note = window_notes.get(window, "")

    await update.message.reply_text(
        f"🔍 <b>Anlık tarama başlatılıyor...</b>\n"
        f"Kaynaklar taranıyor, yeni ilanlar bildirilecek.{note}",
        parse_mode="HTML",
    )

    # Taramayı ayrı thread'de çalıştır (async bot döngüsünü bloklamaz)
    def _run():
        try:
            from scheduler import run_scraping_cycle
            result = run_scraping_cycle(force=True)  # sessiz saati atla
            total_new = result.get("total_new", 0)
            by_source = result.get("by_source", {})

            lines = [f"  • {k}: {v} yeni" for k, v in by_source.items()]
            source_text = "\n".join(lines) if lines else "  • Sonuç yok"

            summary = (
                f"✅ <b>Tarama tamamlandı!</b>\n\n"
                f"📬 <b>Toplam yeni ilan:</b> {total_new}\n\n"
                f"<b>Kaynağa göre:</b>\n{source_text}"
            )
            notifier._send_message(summary)
        except Exception as e:
            logger.error("/tara komutu hata: %s", e, exc_info=True)
            notifier._send_message(
                f"❌ <b>Tarama sırasında hata oluştu:</b>\n<code>{e}</code>"
            )

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()


# ─── Yardımcı ────────────────────────────────────────────────────────────────
def _build_status_text(stats: dict) -> str:
    from scheduler import _get_window, INTERVAL_DAY, INTERVAL_EVE

    total = stats.get("total", 0)
    by_source = stats.get("by_source", {})
    last_found = stats.get("last_found_at", "Henüz yok")

    source_lines = "\n".join(
        f"  • {k.capitalize()}: {v} ilan" for k, v in by_source.items()
    ) or "  • Henüz ilan bulunamadı"

    window = _get_window()
    window_status = {
        "day":   f"☀️ <b>Mod:</b> Aktif mesai — her {INTERVAL_DAY} dakika",
        "eve":   f"🌆 <b>Mod:</b> Akşam saati — her {INTERVAL_EVE} dakika",
        "night": "🌙 <b>Mod:</b> Gece sessiz saati (00:00–07:59) — tarama yok",
    }.get(window, "")

    return (
        "🤖 <b>Job Hunter Bot — Aktif ✅</b>\n"
        "\n"
        f"{window_status}\n"
        "\n"
        f"📊 <b>Toplam takip edilen ilan:</b> {total}\n"
        "\n"
        "<b>Kaynağa göre dağılım:</b>\n"
        f"{source_lines}\n"
        "\n"
        f"🕐 <b>Son bulunan ilan:</b> {last_found}\n"
        "\n"
        "<b>Tarama programı:</b>\n"
        f"  ☀️ 08:00–18:59 → her {INTERVAL_DAY} dk\n"
        f"  🌆 19:00–23:59 → her {INTERVAL_EVE} dk\n"
        "  🌙 00:00–07:59 → tarama yok\n"
        "\n"
        "📌 <b>Komutlar:</b>\n"
        "  /tara — Anlık tarama başlat\n"
        "  /durum — Bu mesajı göster"
    )


# ─── Uygulama Oluşturucu ─────────────────────────────────────────────────────
def create_application() -> Application:
    """Telegram bot uygulamasını oluştur ve komutları kaydet."""
    if not config.TELEGRAM_BOT_TOKEN:
        raise ValueError("TELEGRAM_BOT_TOKEN boş! .env dosyasını kontrol edin.")

    app = Application.builder().token(config.TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("durum", cmd_durum))
    app.add_handler(CommandHandler("tara", cmd_tara))

    logger.info("Telegram bot uygulaması hazır.")
    return app
