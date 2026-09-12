"""companies.json'a aday kaynak ekler/gunceller. Etkinlestirme kanit gerektirir."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "companies.json"


def upsert(entries):
    data = json.loads(TARGET.read_text(encoding="utf-8"))
    index = {c["name"]: i for i, c in enumerate(data)}
    added, updated = [], []
    for entry in entries:
        if entry["name"] in index:
            data[index[entry["name"]]] = {**data[index[entry["name"]]], **entry}
            updated.append(entry["name"])
        else:
            data.append(entry)
            added.append(entry["name"])
    TARGET.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"added": added, "updated": updated}, ensure_ascii=False))


if __name__ == "__main__":
    upsert(json.loads(Path(sys.argv[1]).read_text(encoding="utf-8")))
