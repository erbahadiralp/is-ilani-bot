"""Program sayfasindaki anlamli metin/başvuru linki degisiklikleri; acilis iddiasi yok."""
import hashlib
import json
import re
from pathlib import Path
from urllib.parse import urljoin, urlsplit
from bs4 import BeautifulSoup
import requests
import database
from watchlist import read_radar, normalize
from .base import BaseScraper

def embedded_program_content(html, component, title_terms):
    records = []
    for match in re.finditer(re.escape("Components." + component + ","), html):
        record, _ = json.JSONDecoder().raw_decode(html[match.end():].lstrip())
        if any(normalize(term) in normalize(record.get("title", "")) for term in title_terms):
            if not record.get("content"):
                raise ValueError("Program detay icerigi eksik")
            records.append({key: record.get(key) for key in
                            ("title", "description", "content", "isActiveJobAdvert", "detailUrl")})
    if not records:
        raise ValueError("Gomulu program detaylari bulunamadi")
    return json.dumps(sorted(records, key=lambda row: row["title"]), ensure_ascii=False, sort_keys=True)


def json_program_content(payload, locale, fields):
    """Basliksiz icerik API'lerinde yalniz anlamli alanlari ozetler.

    Kayit kimligi ve updatedAt gibi her yayinda degisen alanlar disarida birakilir; aksi halde
    icerik degismeden sahte degisiklik olayi uretilir.
    """
    records = []

    def walk(value):
        if isinstance(value, list):
            for item in value:
                walk(item)
        elif isinstance(value, dict):
            if locale is None or value.get("locale") == locale:
                selected = {key: value[key] for key in fields if isinstance(value.get(key), str) and value[key].strip()}
                if selected:
                    records.append(selected)
            for child in value.values():
                if isinstance(child, (list, dict)):
                    walk(child)

    walk(payload)
    if not records:
        raise ValueError("Program icerik alanlari bulunamadi")
    unique = {json.dumps(row, ensure_ascii=False, sort_keys=True) for row in records}
    return json.dumps(sorted(unique), ensure_ascii=False)


class ProgramScraper(BaseScraper):
    SOURCE_NAME = "program"

    def scrape(self):
        self.source_results = []
        programs = json.loads((Path(__file__).resolve().parents[1] / "programs.json").read_text(encoding="utf-8"))
        names = {normalize(c["name"]) for c in read_radar()[0]}
        for program in programs:
            if normalize(program["company"]) not in names:
                continue
            try:
                response = requests.get(program["url"], timeout=20)
                response.raise_for_status()
                if response.encoding is None or response.encoding.lower() in ("iso-8859-1", "latin-1"):
                    response.encoding = response.apparent_encoding or "utf-8"
                if program.get("json_fields"):
                    # Icerik API'si dondururen kaynaklar; HTML secici yerine alan secimi kullanilir.
                    content = json_program_content(response.json(), program.get("json_locale"), program["json_fields"])
                else:
                    soup = BeautifulSoup(response.text, "html.parser")
                    if program.get("expected_page_title") and (not soup.title or program["expected_page_title"].casefold() not in soup.title.get_text().casefold()):
                        raise ValueError("Duyuru sayfasi basligi dogrulanamadi")
                    sections = soup.select(program["selector"])
                    if not sections:
                        raise ValueError("Program alani okunamadi; onceki durum korundu")
                    pieces = []
                    for section in sections:
                        for el in section.select("script,style,nav,footer,header"):
                            el.decompose()
                        pieces.append(section.get_text(" ", strip=True))
                        pieces.extend(urljoin(response.url, a["href"]) for a in section.select("a[href]")
                                      if "başvur" in a.get_text().lower() or "apply" in a.get_text().lower())
                    if program.get("link_selector"):
                        pieces.extend(urljoin(response.url, a["href"]) for a in soup.select(program["link_selector"]) if a.get("href"))
                    content = " ".join(" ".join(pieces).split())
                    if program.get("embedded_component"):
                        content += " " + embedded_program_content(response.text, program["embedded_component"], program["embedded_title_terms"])
                if len(content) < program.get("min_chars", 100) or program["expected_text"].casefold() not in content.casefold():
                    raise ValueError("Program icerigi dogrulanamadi; onceki durum korundu")
                if program.get("image_selector"):
                    images = soup.select(program["image_selector"])
                    if not images or len(images) > 8:
                        raise ValueError("Program gorselleri dogrulanamadi")
                    for img in images:
                        image_url = urljoin(response.url, img.get("src", ""))
                        if urlsplit(image_url).netloc != urlsplit(response.url).netloc:
                            raise ValueError("Program gorseli beklenmeyen alan adinda")
                        image_response = requests.get(image_url, timeout=20)
                        image_response.raise_for_status()
                        content += " " + image_url + " " + hashlib.sha256(image_response.content).hexdigest()
                fingerprint = hashlib.sha256(content.encode()).hexdigest()
                job = {"title": program["name"] + " — program sayfası değişti",
                       "company": program["company"], "program": program["name"],
                       "location": "Türkiye", "source": "program", "url": program["url"],
                       "note": "Başvuru tarihleri veya koşulları değişmiş olabilir. Açılış teyidi için sayfayı kontrol et."}
                database.program_event(program["url"], fingerprint, job)
                self.source_results.append({"company": program["company"], "name": program["name"], "url": program["url"], "status": "ok"})
            except Exception as exc:
                self.source_results.append({"company": program["company"], "name": program["name"], "url": program["url"], "status": "error", "error": str(exc)})
                self.logger.warning("%s program izleme hatasi: %s", program["company"], exc)
            self.random_sleep(1, 3)
        return []
