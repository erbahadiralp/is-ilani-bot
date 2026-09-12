"""Build coverage from configured sources and recorded public checks."""
import json
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from watchlist import coverage

def write_report():
    companies = json.loads((ROOT / "companies.json").read_text(encoding="utf-8"))
    audit_path = ROOT / "source_audit.json"
    audits = {r["name"]: r for r in json.loads(audit_path.read_text(encoding="utf-8"))} if audit_path.exists() else {}
    radar = coverage()
    enabled = [c for c in companies if c.get("enabled", True)]
    checked = [audits[c["name"]] for c in enabled if c["name"] in audits and audits[c["name"]].get("url") == c["url"] and audits[c["name"]].get("status") == "ok"]
    working = sum(r["enabled"] and r["status"] == "verified_at_last_audit" for r in radar)
    pending = sum(bool(r["url"]) and not (r["enabled"] and r["status"] == "verified_at_last_audit") for r in radar)
    rows = ["# Resmi şirket kaynakları — kapsam", "", f"Radar: {len(radar)} şirket adı. Yapılandırılmış etkin kaynak: {len(enabled)}. Son kayıtlı kontrolü başarılı etkin kaynak: {len(checked)}.",
            f"Radarda etkin kaynağa eşleşen ad: {sum(r['enabled'] for r in radar)}. Kaynak adresi henüz eşleşmeyen: {sum(not r['url'] for r in radar)}.",
            f"Başarılı kontrollerde okunan ilan: {sum(r['raw'] for r in checked)}; filtreye uygun: {sum(r['eligible'] for r in checked)}.", "",
            "Bunlar geliştirme ortamındaki tarihli kontrollerdir; sunucunun anlık sağlık durumu değildir. Aynı şirketin listedeki farklı adları tek kaynağı paylaşabilir. Kaynağı bulunmuş ama devre dışı olan şirketler taranmaz.", "", f"Şirket bazında: {working} doğrulanmış aktif kaynağa bağlı; {pending} adresi kayıtlı fakat entegrasyonu tamamlanmamış; {sum(not r['url'] for r in radar)} adresi henüz kayıtlı değil.", "", "## Etkin kaynaklar", "", "| Şirket | Son kontrol (UTC) | Durum | Okunan | Uygun |", "|---|---|---|---:|---:|"]
    for c in enabled:
        a = audits.get(c['name'], {})
        if a.get('url') != c['url']:
            a = {}
        rows.append(f"| [{c['name']}]({c['url']}) | {a.get('checked_at','—')} | {a.get('status','kontrol bekliyor')} | {a.get('raw','—')} | {a.get('eligible','—')} |")
    rows += ["", "Ek erken kariyer panoları: " + "; ".join(c["name"] + ": " + ", ".join(b["url"] for b in c["additional_boards"]) for c in enabled if c.get("additional_boards"))]
    rows += ["", "## Devre dışı / entegrasyon bekleyen kaynaklar", "", "| Şirket | Durum | Açıklama |", "|---|---|---|"]
    for c in companies:
        if not c.get('enabled',True):
            rows.append(f"| [{c['name']}]({c['url']}) | {c.get('verification_status','bekliyor')} | {c.get('verification_note','')} |")
    rows += ["", "## Henüz kaynak eşleşmeyen radar şirketleri", ""]
    rows += ['- '+r['name'] for r in radar if not r['url']]
    rows += ["", "Raporu yenile: `python tools/report_coverage.py`. Canlı kontrol: `python tools/audit_companies.py` (dört kaynak eşzamanlı; Telegram/DB kullanılmaz).", ""]
    (ROOT / 'SOURCE_COVERAGE.md').write_text('\n'.join(rows),encoding='utf-8')
    from report_banks import write_report as write_bank_report
    write_bank_report()
    print(json.dumps({'radar':len(radar),'enabled_sources':len(enabled),'successful_sources':len(checked),'raw_jobs':sum(r['raw'] for r in checked),'eligible_jobs':sum(r['eligible'] for r in checked)},ensure_ascii=True))

if __name__ == '__main__':
    write_report()
