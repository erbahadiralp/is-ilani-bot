"""Validate eligible direct links from the last source audit; no DB/Telegram."""
import json
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import requests
from bs4 import BeautifulSoup
ROOT = Path(__file__).resolve().parents[1]

def check(job):
    row = {"url":job["url"], "title":job.get("title", ""), "checked_at":datetime.now(timezone.utc).isoformat()}
    try:
        r = requests.get(job["url"], timeout=25)
        r.raise_for_status()
        title = BeautifulSoup(r.text, "html.parser").title
        page_title = title.get_text(" ",strip=True) if title else ""
        if any(t in page_title.lower() for t in ["just a moment", "access denied", "page not found"]):
            raise ValueError("Challenge or missing page: " + page_title)
        row.update(status="ok", http_status=r.status_code, final_url=r.url, page_title=page_title)
    except Exception as exc:
        row.update(status="error", error=str(exc))
    return row

if __name__ == "__main__":
    audits = json.loads((ROOT / "source_audit.json").read_text(encoding="utf-8"))
    jobs = {j["url"]:j for row in audits if row.get("status")=="ok" for j in row.get("jobs",[])}
    with ThreadPoolExecutor(max_workers=4) as pool:
        rows = list(pool.map(check, jobs.values()))
    (ROOT / "job_link_audit.json").write_text(json.dumps(rows,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"checked":len(rows), "ok":sum(r["status"]=="ok" for r in rows), "errors":[r for r in rows if r["status"]!="ok"]},ensure_ascii=True))
