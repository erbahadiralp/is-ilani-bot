"""Markdown radar listesi: sirketler, programlar ve kapsam raporu."""
from pathlib import Path
import json
import re
import unicodedata

ROOT = Path(__file__).resolve().parent

def normalize(value):
    value = value.replace("ı", "i").replace("İ", "i").casefold()
    return "".join(c for c in unicodedata.normalize("NFKD", value) if not unicodedata.combining(c))

def matches(text, keyword):
    return bool(re.search(r"(?<!\w)" + re.escape(normalize(keyword)) + r"(?!\w)", normalize(text)))

def read_radar():
    companies, programs = [], []
    mode, sector = "companies", ""
    for line in (ROOT / "turkiye_yeni_mezun_sirket_takip_listesi.md").read_text(encoding="utf-8-sig").splitlines():
        if line.startswith("# Bilinen Program"):
            mode = "programs"
        elif line.startswith("# Global"):
            break
        elif line.startswith("## ") and mode == "companies":
            sector = line[3:].strip()
        elif line.startswith("- "):
            value = line[2:].strip()
            if mode == "companies":
                if not any(normalize(c["name"]) == normalize(value) for c in companies):
                    companies.append({"name": value, "sector": sector})
            else:
                programs.append(value)
    return companies, programs

PROGRAMS = read_radar()[1] + ["Yetenek Kuşağı", "Road to Tech", "SAP Young Professionals Program", "SAP Academy for Customer Success"]
EARLY = ["yeni mezun", "new graduate", "new grad", "graduate", "management trainee",
         "genç yetenek", "young talent", "yönetici adayı", "yetiştirilmek üzere",
         "bootcamp", "trainee", "entry level", "entry-level",
         "uzman yardımcısı", "uzman yard.", "junior", "jr", "fresher", "fresh graduate"]
TECH = ["monitoring specialist", "system engineer", "systems engineer", "network engineer", "sistem mühendisi", "ağ mühendisi", "java", "python", "sap", "abap", "data", "veri", "software", "yazılım",
        "backend", "frontend", ".net", "cloud", "bulut", "devops", "machine learning",
        "yapay zeka", "siber", "cyber", "bilgi teknolojileri", "technology consulting",
        "spring", "spring boot", "full stack", "full-stack", "fullstack", "front-end", "back-end",
        "computer engineer", "bilgisayar mühendisi", "developer", "geliştirici", "development",
        "qa", "test engineer", "test mühendisi", "quality assurance", "sdet",
        "android", "ios", "mobile", "mobil", "embedded", "gömülü", "artificial intelligence"]
# Program ve uzman yardimcisi basliklarinda alan kaniti olarak kabul edilen terimler.
TECH_TITLE = TECH + ["bt", "it", "bilişim", "bilgi işlem", "tech", "technology", "teknoloji"]
SENIOR = ["senior", "lead", "manager", "müdür", "direktör", "principal", "experienced",
          "mid-level", "mid level", "staff engineer", "kıdemli"]

def program_name(title):
    return next((p for p in PROGRAMS if matches(title, p)), "")

def relevant(title, description=""):
    """Teknoloji rolu + erken kariyer kaniti; genel graduate programlari istisna."""
    if any(matches(title, k) for k in SENIOR):
        return False
    text = normalize(title + " " + description)
    # Acikca 3+ yil alt siniri istenen ilanlar yeni mezun profiline uymaz.
    if re.search(r"(?<![\d-])(?:[3-9]|[1-9]\d)\s*\+\s*(?:years?|yil)", text):
        return False
    if re.search(r"(?:at least|minimum|min\.|en az)\s+(?:[3-9]|[1-9]\d)\s*(?:years?|yil)", text):
        return False
    # Kullanici yalniz yazilim/bilgisayar muhendisligi alanindaki ilanlari istiyor. Program,
    # management trainee ve uzman yardimcisi basliklari deneyim kaniti sayilir fakat alan kaniti
    # sayilmaz; basligin kendisi teknoloji alanini gostermelidir. Aciklama kullanilmaz: genel MT
    # ilanlarinin kabul edilen bolumler listesinde "Bilgisayar Muhendisligi", KVKK metinlerinde
    # "kisisel veri" gecer ve teknoloji disi ilanlari da eslestirir.
    tech_title = any(matches(title, k) for k in TECH_TITLE)
    general_program = ["graduate program", "graduate programme", "management trainee",
                       "genç yetenek", "young talent", "yeni mezun programı", "yönetici adayı"]
    assistant = ["uzman yardımcısı", "uzman yard.", "uzm.yrd", "uzm. yrd.", "uzman yrd."]
    if program_name(title) or any(matches(title, k) for k in general_program + assistant):
        return tech_title
    tech = any(matches(title, k) for k in TECH)
    early_title = any(matches(title, k) for k in EARLY)
    # Aciklamada 'juniorlara mentorluk' gibi ifadeler yeterli degil.
    early_description = any(matches(description, k) for k in [
        "new graduates are welcome", "fresh graduates are welcome", "new grads welcome",
        "no experience required", "no prior experience required", "yeni mezun adaylar",
        "deneyim şartı aranmamaktadır", "deneyim aranmamaktadır", "yetiştirilmek üzere"])
    early_description = early_description or bool(re.search(
        r"(?<!\d)0\s*[-–]\s*[12]\s*(?:years?|yil)", normalize(description)))
    return tech and (early_title or early_description)


def coverage():
    sources = json.loads((ROOT / "companies.json").read_text(encoding="utf-8-sig"))
    by_name = {normalize(n): c for c in sources for n in [c["name"], *c.get("aliases", [])]}
    audit_path = ROOT / "source_audit.json"
    audits = {r["name"]: r for r in json.loads(audit_path.read_text(encoding="utf-8"))} if audit_path.exists() else {}
    result = []
    for company in read_radar()[0]:
        source = by_name.get(normalize(company["name"]))
        audit = audits.get(source["name"], {}) if source else {}
        if audit.get("url") != (source or {}).get("url"):
            audit = {}
        status = ("verified_at_last_audit" if audit.get("status") == "ok" else "last_audit_error") if audit else (source.get("verification_status", "needs_live_check") if source else "needs_source")
        result.append({**company, "status": status, "checked_at": audit.get("checked_at", ""),
                       "source_name": source["name"] if source else "",
                       "enabled": source.get("enabled", True) if source else False,
                       "url": source.get("url", "") if source else ""})
    return result

if __name__ == "__main__":
    print(json.dumps(coverage(), ensure_ascii=False, indent=2))
