"""Check configured program readers without DB writes or notifications."""
import os
os.environ["LOG_PATH"] = os.devnull
import sys
import json
from pathlib import Path
from datetime import datetime, timezone
from unittest.mock import patch
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scrapers.program_scraper import ProgramScraper

if __name__ == "__main__":
    scraper = ProgramScraper()
    with patch("scrapers.program_scraper.database.program_event"), patch.object(scraper, "random_sleep"):
        scraper.scrape()
    rows = [{**row, "checked_at": datetime.now(timezone.utc).isoformat()} for row in scraper.source_results]
    (ROOT / "program_audit.json").write_text(json.dumps(rows, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({"checked": len(rows), "ok": sum(row["status"] == "ok" for row in rows), "errors": [r for r in rows if r["status"] != "ok"]}, ensure_ascii=True))
