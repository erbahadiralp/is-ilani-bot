"""Build a review queue from cached public ATS directories; no network or bot writes."""
import json
import re
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from watchlist import coverage, normalize

def key(value):
    value = re.sub(r"\([^)]*\)", "", normalize(value))
    value = re.sub(r"\b(turkiye|turkey)\b", "", value)
    return re.sub(r"[^a-z0-9]", "", value)

def build():
    directories = [("lever", "2a81715b0fdb078b"), ("greenhouse", "1f6efe5ef8563e51"),
                   ("ashby", "b506258dabe81d5f"), ("workday", "c89cd55e85676584")]
    index = {}
    for kind, filename in directories:
        path = ROOT / ".source-audit" / (filename + ".txt")
        if not path.exists():
            continue
        for slug in json.loads(path.read_text(encoding="utf-8")):
            tenant = slug.split("|")[0]
            index.setdefault(key(tenant), []).append({"type": kind, "slug": slug})
    queue = []
    for company in coverage():
        if company["enabled"] and company["status"] == "verified_at_last_audit":
            continue
        candidates = index.get(key(company["name"]), [])
        priority = 0 if any(t in company["sector"] for t in ["Bankacılık", "Yazılım", "Telekom"]) else 1
        queue.append({**company, "priority": priority, "candidates": candidates})
    queue.sort(key=lambda r: (r["priority"], not bool(r["candidates"]), r["name"]))
    target = ROOT / ".source-audit" / "source_queue.json"
    target.parent.mkdir(exist_ok=True)
    target.write_text(json.dumps(queue, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"remaining_company_names":len(queue), "with_directory_candidates":sum(bool(r["candidates"]) for r in queue)}, ensure_ascii=True))
    for row in queue:
        if row["candidates"]:
            print(json.dumps({"name":row["name"], "priority":row["priority"], "candidates":row["candidates"]}, ensure_ascii=True))

if __name__ == "__main__":
    build()
