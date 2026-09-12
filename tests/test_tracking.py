"""Harici servis/canli Telegram kullanmadan regresyon testleri."""
import ast
import importlib.util
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import threading
import types
import unittest
from unittest.mock import Mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import watchlist

class TrackingTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        cfg = types.ModuleType("config")
        cfg.DB_PATH = str(Path(self.tmp.name) / "jobs.db")
        self.old_config = sys.modules.get("config")
        sys.modules["config"] = cfg
        spec = importlib.util.spec_from_file_location("test_database", ROOT / "database.py")
        self.db = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.db)
        self.db.init_db()
        self.job = {"title": "Java Developer", "company": "Test & Co", "source": "company", "url": "https://example.com/jobs/1", "location": "Türkiye"}

    def tearDown(self):
        if self.old_config is None:
            sys.modules.pop("config", None)
        else:
            sys.modules["config"] = self.old_config
        self.tmp.cleanup()

    def test_program_and_technology_filters(self):
        for title in ["GNÇYTNK Yazılım", "Data MT", "Technology Management Trainee", "Yeni Mezun Programı - Bilgi Teknolojileri",
                      "SAP Young Professionals Program Turkiye 2026", "Road to Tech", "Junior .NET Developer", "Junior Software Engineer"]:
            self.assertTrue(watchlist.relevant(title), title)
        # Program adi tek basina alan kaniti degildir; teknoloji disi programlar bildirilmez.
        for title in ["GNÇYTNK", "NestLéaders", "Management Trainee", "Yeni Mezun Programı",
                      "Management Trainee for People & Culture (Fresh Grad)", "Sales Graduate Program",
                      "Senior Java Developer", "Data Manager", "Leadership", "Sales Manager", "SAP Senior Consultant"]:
            self.assertFalse(watchlist.relevant(title), title)
        self.assertEqual(watchlist.program_name("HTML Developer"), "")

    def test_new_grad_technology_scope(self):
        for title in ["Junior Java Backend Developer", "Junior Spring Boot Developer",
                      "Junior Python Developer", "Junior Data Scientist", "Junior Data Engineer",
                      "Yeni Mezun Yazılım Mühendisi", "Junior QA Engineer", "Junior Android Developer",
                      "Junior Cloud Engineer", "Junior Embedded Software Engineer"]:
            self.assertTrue(watchlist.relevant(title), title)
        for title in ["Java Developer", "Software Engineer", "Data Engineer", "Junior Sales Representative",
                      "Senior Graduate Program Manager", "Senior GNÇYTNK", "Java Developer 3+ years"]:
            self.assertFalse(watchlist.relevant(title), title)
        self.assertTrue(watchlist.relevant("Java Developer", "New graduates are welcome"))
        self.assertTrue(watchlist.relevant("Data Engineer", "0-2 years of experience"))
        self.assertFalse(watchlist.relevant("Java Developer", "Mentor junior developers"))
        self.assertFalse(watchlist.relevant("Junior Java Developer", "Minimum 3 years experience"))

    def test_assistant_specialist_titles(self):
        for title in ["Bilgi Teknolojileri Uzman Yardımcısı", "Yazılım Geliştirme Uzman Yardımcısı",
                      "BT — Uzman Yardımcısı", "Veri Analitiği Uzm. Yrd.", "Siber Güvenlik Uzman Yard."]:
            self.assertTrue(watchlist.relevant(title), title)
        # Teknoloji alani belirtmeyen uzman yardimcisi ilanlari bildirilmez.
        for title in ["Uzman Yardımcısı", "Teslimat Uzman Yardımcısı", "Yurt İçi Operasyon Uzman Yardımcısı",
                      "Müşteri Memnuniyeti Uzman Yardımcısı - Engelli", "Finans Uzman Yardımcısı",
                      "Uzman", "Uzman Yardımcılığına Hazırlık", "Kıdemli Uzman Yardımcısı"]:
            self.assertFalse(watchlist.relevant(title), title)

    def test_radar_does_not_treat_keywords_as_companies(self):
        companies, programs = watchlist.read_radar()
        names = [c["name"] for c in companies]
        self.assertIn("Akbank", names)
        self.assertNotIn("GNÇYTNK", names)
        self.assertEqual(len(names), len(set(names)))
        self.assertIn("GNÇYTNK", programs)

    def test_duplicate_and_pending_delivery(self):
        self.assertTrue(self.db.save_job(self.job))
        self.assertFalse(self.db.save_job(self.job))
        pending = self.db.pending_alerts()
        self.assertEqual(len(pending), 1)
        self.assertEqual(pending[0][1]["company"], "Test & Co")
        self.db.mark_notified(pending[0][0])
        self.assertEqual(self.db.pending_alerts(), [])

    def test_failed_telegram_is_retried(self):
        tree = ast.parse((ROOT / "scheduler.py").read_text(encoding="utf-8"))
        fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "deliver_pending")
        notifier = types.SimpleNamespace(send_job_alert=Mock(side_effect=[False, True]))
        scope = {"database": self.db, "notifier": notifier, "_delivery_lock": threading.Lock()}
        exec(compile(ast.Module(body=[fn], type_ignores=[]), "scheduler.py", "exec"), scope)
        self.db.save_job(self.job)
        scope["deliver_pending"]()
        self.assertEqual(len(self.db.pending_alerts()), 1)
        scope["deliver_pending"]()
        self.assertEqual(len(self.db.pending_alerts()), 0)
        self.assertEqual(notifier.send_job_alert.call_count, 2)

    def test_program_baseline_and_change_are_atomic(self):
        url = self.job["url"]
        self.assertFalse(self.db.program_event(url, "closed", self.job))
        self.assertEqual(self.db.pending_alerts(), [])
        self.assertFalse(self.db.program_event(url, "closed", self.job))
        self.assertTrue(self.db.program_event(url, "open", self.job))
        self.assertFalse(self.db.program_event(url, "open", self.job))
        self.assertEqual(len(self.db.pending_alerts()), 1)
        self.assertTrue(self.db.program_event(url, "closed", self.job))
        self.assertTrue(self.db.program_event(url, "open", self.job))
        self.assertEqual(len(self.db.pending_alerts()), 3)

    def test_existing_database_migrates_without_old_alerts(self):
        with self.db._get_conn() as conn:
            conn.execute("DROP TABLE jobs")
            conn.execute("CREATE TABLE jobs(id TEXT PRIMARY KEY,title TEXT,company TEXT,location TEXT,source TEXT,url TEXT,found_at TEXT)")
            conn.execute("INSERT INTO jobs VALUES('old','old','x','x','company','https://old','2020-01-01')")
        self.db.init_db()
        self.assertEqual(self.db.pending_alerts(), [])
        self.assertTrue(self.db.save_job(self.job))
        self.assertEqual(len(self.db.pending_alerts()), 1)

    def test_cleanup_preserves_unsent_jobs(self):
        self.db.save_job(self.job)
        with self.db._get_conn() as conn:
            conn.execute("UPDATE jobs SET found_at='2000-01-01'")
        self.db.cleanup_old_jobs(30)
        self.assertEqual(len(self.db.pending_alerts()), 1)

if __name__ == "__main__":
    unittest.main()
