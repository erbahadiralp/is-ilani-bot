"""
database.py — SQLite veritabanı işlemleri
- İlan kaydetme ve mükerrer tespiti
- 30 günlük otomatik temizlik
- İstatistik sorguları
"""

import hashlib
import logging
import sqlite3
from datetime import datetime, timedelta
from typing import Optional

import config

logger = logging.getLogger("database")

# ─── Tip Tanımı ─────────────────────────────────────────────────────────────
Job = dict  # title, company, location, source, url


# ─── Yardımcı ───────────────────────────────────────────────────────────────
def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(config.DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _job_id(url: str) -> str:
    """URL'nin MD5 hash'ini benzersiz ID olarak kullan."""
    return hashlib.md5(url.encode()).hexdigest()


# ─── Başlatma ───────────────────────────────────────────────────────────────
def init_db() -> None:
    """Veritabanı tablolarını oluştur (yoksa)."""
    with _get_conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS jobs (
                id        TEXT PRIMARY KEY,
                title     TEXT NOT NULL,
                company   TEXT,
                location  TEXT,
                source    TEXT NOT NULL,
                url       TEXT NOT NULL,
                found_at  DATETIME NOT NULL DEFAULT (datetime('now'))
            )
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_found_at ON jobs(found_at)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_source ON jobs(source)"
        )
        conn.commit()
    logger.info("Veritabanı hazır: %s", config.DB_PATH)


# ─── CRUD ───────────────────────────────────────────────────────────────────
def is_seen(url: str) -> bool:
    """Bu ilan daha önce görüldü mü?"""
    job_id = _job_id(url)
    with _get_conn() as conn:
        row = conn.execute(
            "SELECT 1 FROM jobs WHERE id = ?", (job_id,)
        ).fetchone()
    return row is not None


def save_job(job: Job) -> bool:
    """
    Yeni ilanı kaydet.
    Başarıyla kaydedildiyse True, zaten varsa False döner.
    """
    if is_seen(job["url"]):
        return False
    job_id = _job_id(job["url"])
    with _get_conn() as conn:
        try:
            conn.execute(
                """
                INSERT INTO jobs (id, title, company, location, source, url, found_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    job_id,
                    job.get("title", ""),
                    job.get("company", ""),
                    job.get("location", ""),
                    job.get("source", ""),
                    job.get("url", ""),
                    datetime.now().isoformat(),
                ),
            )
            conn.commit()
            logger.info("Yeni ilan kaydedildi: [%s] %s", job.get("source"), job.get("title"))
            return True
        except sqlite3.IntegrityError:
            return False


# ─── Bakım ──────────────────────────────────────────────────────────────────
def cleanup_old_jobs(days: int = 30) -> int:
    """30 günden eski ilanları sil. Silinen kayıt sayısını döner."""
    cutoff = (datetime.now() - timedelta(days=days)).isoformat()
    with _get_conn() as conn:
        cursor = conn.execute(
            "DELETE FROM jobs WHERE found_at < ?", (cutoff,)
        )
        conn.commit()
        deleted = cursor.rowcount
    logger.info("Eski ilan temizliği: %d kayıt silindi (>%d gün)", deleted, days)
    return deleted


# ─── İstatistik ─────────────────────────────────────────────────────────────
def get_stats() -> dict:
    """Veritabanı istatistiklerini döner."""
    with _get_conn() as conn:
        total = conn.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
        by_source = conn.execute(
            "SELECT source, COUNT(*) as cnt FROM jobs GROUP BY source"
        ).fetchall()
        last_job = conn.execute(
            "SELECT found_at FROM jobs ORDER BY found_at DESC LIMIT 1"
        ).fetchone()

    return {
        "total": total,
        "by_source": {row["source"]: row["cnt"] for row in by_source},
        "last_found_at": last_job["found_at"] if last_job else None,
    }


def get_recent_jobs(limit: int = 5) -> list[dict]:
    """Son eklenen N ilanı döner."""
    with _get_conn() as conn:
        rows = conn.execute(
            """
            SELECT title, company, location, source, url, found_at
            FROM jobs
            ORDER BY found_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [dict(row) for row in rows]
