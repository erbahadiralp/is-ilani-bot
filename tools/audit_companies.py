"""Live read-only source checks; writes report, never initializes DB or alerts."""
import os
os.environ["LOG_PATH"] = os.devnull
import sys
import json
from datetime import datetime, timezone
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scrapers.company_scraper import CompanyScraper

if __name__ == "__main__":
    scraper = CompanyScraper()
    rows = []
    selected = set(sys.argv[1:])
    def check(company):
        worker = CompanyScraper()
        row = {"name": company["name"], "url": company["url"], "checked_at": datetime.now(timezone.utc).isoformat()}
        try:
            jobs = worker.scrape_company(company)
            row.update(status="ok", raw=worker.raw_count, eligible=len(jobs), jobs=jobs)
        except Exception as exc:
            row.update(status="error", error=str(exc))
        print(json.dumps({k:v for k,v in row.items() if k != "jobs"}, ensure_ascii=True), flush=True)
        return row
    companies = [c for c in scraper.companies if c.get("enabled", True) and (not selected or c["name"] in selected)]
    with ThreadPoolExecutor(max_workers=4) as pool:
        rows = list(pool.map(check, companies))
    target = ROOT / "source_audit.json"
    if selected and target.exists():
        previous = {r["name"]: r for r in json.loads(target.read_text(encoding="utf-8"))}
        previous.update({r["name"]: r for r in rows})
        rows = list(previous.values())
    target.write_text(json.dumps(rows, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")

    from report_coverage import write_report
    write_report()
