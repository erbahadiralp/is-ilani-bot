"""Bilinen ATS panolarini sirket adindan turetilen kimliklerle dener ve pano kimligini dogrular."""
import argparse
import json
import re
import sys
import time
import unicodedata
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import urlsplit

import requests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from watchlist import normalize

OUT = ROOT / ".source-audit"
HEADERS = {"User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                          "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"),
           "Accept": "application/json"}


def slugs(entry):
    """Sirket adi ve alan adindan aday pano kimlikleri."""
    base = normalize(entry["name"])
    base = re.sub(r"\b(turkiye|turkey|holding|grubu|group|as|a s|sigorta|teknoloji)\b", " ", base)
    base = "".join(c for c in unicodedata.normalize("NFKD", base) if not unicodedata.combining(c))
    words = [w for w in re.split(r"[^a-z0-9]+", base) if w]
    domain = urlsplit(entry["home"]).netloc.replace("www.", "").split(".")[0]
    out = ["".join(words), "-".join(words), domain]
    return [s for i, s in enumerate(out) if s and s not in out[:i]]


def probe(task):
    name, slug, kind = task
    urls = {"lever": "https://api.lever.co/v0/postings/{}?mode=json",
            "greenhouse": "https://boards-api.greenhouse.io/v1/boards/{}/jobs?content=true",
            "ashby": "https://api.ashbyhq.com/posting-api/job-board/{}",
            "smartrecruiters": "https://api.smartrecruiters.com/v1/companies/{}/postings?limit=10"}
    try:
        response = requests.get(urls[kind].format(slug), headers=HEADERS, timeout=20)
    except requests.RequestException:
        return None
    if response.status_code != 200:
        return None
    try:
        data = response.json()
    except ValueError:
        return None
    if kind == "lever":
        rows = data if isinstance(data, list) else None
    elif kind == "greenhouse":
        rows = data.get("jobs") if isinstance(data, dict) else None
    elif kind == "ashby":
        rows = data.get("jobs") if isinstance(data, dict) else None
    else:
        rows = data.get("content") if isinstance(data, dict) else None
    if rows is None:
        return None
    # Bos pano yanlis eslesmeyi ayirt ettirmez; kimlik dogrulamasi icin en az bir ilan gerekir.
    def place(row):
        value = row.get("location") or (row.get("categories") or {}).get("location") or ""
        if isinstance(value, dict):
            value = value.get("fullLocation") or value.get("name") or value.get("city") or value.get("country") or ""
        return str(value)[:40]
    return {"name": name, "type": kind, "slug": slug, "jobs": len(rows),
            "sample": [str(r.get("text") or r.get("title") or r.get("name") or "")[:60] for r in rows[:3]],
            "locations": [place(r) for r in rows[:5] if isinstance(r, dict)]}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("seed")
    parser.add_argument("--workers", type=int, default=10)
    parser.add_argument("--out", default=str(OUT / "ats_sweep.json"))
    args = parser.parse_args()
    entries = json.loads(Path(args.seed).read_text(encoding="utf-8"))
    tasks = [(e["name"], slug, kind) for e in entries for slug in slugs(e)
             for kind in ("lever", "greenhouse", "ashby", "smartrecruiters")]
    print(json.dumps({"probes": len(tasks)}, ensure_ascii=True), flush=True)
    rows = []
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        for row in pool.map(probe, tasks):
            if row and row["jobs"]:
                rows.append(row)
                print(json.dumps(row, ensure_ascii=False), flush=True)
    Path(args.out).write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"hits": len(rows), "companies": len({r["name"] for r in rows})}, ensure_ascii=True))


if __name__ == "__main__":
    main()
