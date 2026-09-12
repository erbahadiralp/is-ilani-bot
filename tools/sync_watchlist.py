"""Disable sources absent from the current user radar; never auto-enable sources."""
import json
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from watchlist import read_radar, normalize

def sync():
    names = {normalize(c["name"]) for c in read_radar()[0]}
    path = ROOT / "companies.json"
    rows = json.loads(path.read_text(encoding="utf-8"))
    disabled = []
    for row in rows:
        if row.get("enabled", True) and not row.get("extra_source", False) and not any(normalize(n) in names for n in [row["name"], *row.get("aliases", [])]):
            row.update(enabled=False, verification_status="outside_current_watchlist")
            disabled.append(row["name"])
    path.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"radar":len(names), "disabled":disabled}, ensure_ascii=True))

if __name__ == "__main__":
    sync()
