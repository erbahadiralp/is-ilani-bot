"""
main.py — Job Hunter Telegram Bot — Ana Giriş Noktası

Başlatma sırası:
1. Veritabanını başlat
2. APScheduler'ı başlat
3. İlk taramayı hemen çalıştır (opsiyonel)
4. Telegram bot'u polling modunda çalıştır (asenkron)
"""

import logging
import sys

import config  # logging setup burada yapılır

logger = logging.getLogger("main")


def main():
    logger.info("╔══════════════════════════════════════╗")
    logger.info("║     Job Hunter Telegram Bot v1.0     ║")
    logger.info("╚══════════════════════════════════════╝")

    # ── 1. Ön Kontrol ──────────────────────────────────────────────────────
    if not config.TELEGRAM_BOT_TOKEN:
        logger.critical("TELEGRAM_BOT_TOKEN tanımlı değil! .env dosyasını kontrol edin.")
        sys.exit(1)
    if not config.TELEGRAM_CHAT_ID:
        logger.critical("TELEGRAM_CHAT_ID tanımlı değil! .env dosyasını kontrol edin.")
        sys.exit(1)

    # ── 2. Veritabanı ──────────────────────────────────────────────────────
    import database
    database.init_db()

    # ── 3. Scheduler ───────────────────────────────────────────────────────
    from scheduler import create_scheduler, run_scraping_cycle
    scheduler = create_scheduler()
    scheduler.start()
    logger.info("Scheduler başlatıldı.")

    # ── 4. Başlangıç Bildirimi ─────────────────────────────────────────────
    import notifier
    from scheduler import INTERVAL_DAY, INTERVAL_EVE
    stats = database.get_stats()
    notifier.send_status_message(stats, INTERVAL_DAY)

    # ── 5. İlk Taramayı Hemen Çalıştır ────────────────────────────────────
    logger.info("İlk tarama başlıyor (bekleme olmadan)...")
    try:
        run_scraping_cycle()
    except Exception as e:
        logger.error("İlk tarama hatası: %s", e, exc_info=True)

    # ── 6. Telegram Bot (Polling) ──────────────────────────────────────────
    from bot import create_application
    app = create_application()

    logger.info("Telegram bot polling başlatılıyor...")
    logger.info("Durdurmak için Ctrl+C.")

    try:
        app.run_polling(
            allowed_updates=["message"],
            drop_pending_updates=True,  # Eski komutları yoksay
        )
    except KeyboardInterrupt:
        logger.info("Bot durduruldu (Ctrl+C).")
    finally:
        scheduler.shutdown(wait=False)
        logger.info("Scheduler kapatıldı.")
        logger.info("Bot temiz şekilde sonlandırıldı.")


if __name__ == "__main__":
    main()
