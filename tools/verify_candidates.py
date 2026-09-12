"""Aday kaynaklari gercek okuyucuyla dener. Etkin olmayan kayitlar da calisir; DB/Telegram kullanmaz."""
import os
os.environ["LOG_PATH"] = os.devnull
import json
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scrapers.company_scraper import CompanyScraper


def check(company):
    worker = CompanyScraper()
    worker._detail_cache = {}
    row = {"name": company["name"], "type": company.get("type"), "url": company["url"],
           "checked_at": datetime.now(timezone.utc).isoformat()}
    try:
        jobs = worker.scrape_company(company)
        row.update(status="ok", raw=worker.raw_count, eligible=len(jobs),
                   jobs=[{"title": j["title"], "url": j["url"], "location": j["location"]} for j in jobs])
    except Exception as exc:
        row.update(status="error", error=f"{type(exc).__name__}: {exc}")
    return row


def main():
    selected = set(sys.argv[1:])
    data = json.loads((ROOT / "companies.json").read_text(encoding="utf-8"))
    targets = [c for c in data if not selected or c["name"] in selected]
    if selected:
        missing = selected - {c["name"] for c in targets}
        if missing:
            raise SystemExit("companies.json icinde bulunamadi: " + ", ".join(sorted(missing)))
    rows = []
    with ThreadPoolExecutor(max_workers=6) as pool:
        for row in pool.map(check, targets):
            rows.append(row)
            print(json.dumps({k: v for k, v in row.items() if k != "jobs"}, ensure_ascii=False), flush=True)
            for job in row.get("jobs", [])[:6]:
                print("    +", job["title"], "|", job["location"], "|", job["url"], flush=True)
    out = ROOT / ".source-audit" / "candidate_audit.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"checked": len(rows), "ok": sum(r["status"] == "ok" for r in rows)}, ensure_ascii=True))


if __name__ == "__main__":
    main()
