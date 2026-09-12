"""Rebuild the bank report using the same alias matching as the watchlist."""
import json
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from watchlist import normalize


def write_report():
    target = ROOT / "BANK_COVERAGE.md"
    names = [line.split("|")[1].strip() for line in target.read_text(encoding="utf-8").splitlines() if line.startswith("| ") and not line.startswith("| Kurum")]
    sources = json.loads((ROOT / "companies.json").read_text(encoding="utf-8"))
    by_name = {normalize(name): c for c in sources for name in [c["name"], *c.get("aliases", [])]}
    audits = {a["name"]: a for a in json.loads((ROOT / "source_audit.json").read_text(encoding="utf-8"))}
    programs = json.loads((ROOT / "programs.json").read_text(encoding="utf-8"))
    lines = ["# Banka ve iştirak takip durumu", "", "İlan okuyucusu, program/duyuru takibi ve erişim engeli farklı durumlardır. Bankaların tamamı entegre değildir.", "", "| Kurum | İlan kaynağı durumu | Program / duyuru takibi | Açıklama |", "|---|---|---|---|"]
    for name in dict.fromkeys(names):
        c = by_name.get(normalize(name), {})
        a = audits.get(c.get("name"), {})
        state = "verified_at_last_audit" if c.get("enabled") and a.get("url") == c.get("url") and a.get("status") == "ok" else c.get("verification_status", "needs_source")
        tracks = ", ".join(p["name"] for p in programs if normalize(p["company"]) in {normalize(name), normalize(c.get("name", ""))}) or "Yok"
        lines.append("| " + " | ".join([name, state, tracks, c.get("verification_note", "")]) + " |")
    lines += ["", "Tarih ve ham/uygun ilan sayıları source_audit.json içindedir. Raporda ING Türkiye, ING kaynak adına eşleştirilir; aynı banka için ikinci okuyucu oluşturulmaz.", "", "Softtech ve HRPeak banka okuyucuları için Chromium, İş Bankası için paketteki certificates klasörü gereklidir. Engelli kaynaklar sıfır ilan veya tamamlanmış entegrasyon olarak sayılmaz.", ""]
    target.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    write_report()
