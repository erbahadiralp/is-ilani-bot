"""Tarayici destekli kaynak kesfi. Anonim Chromium ile kamuya acik kariyer sayfalarini acar,
ATS yonlendirmelerini ve sayfanin kendi ilan veri cagrilarini kaydeder. Basvuru veya giris yapmaz."""
import argparse
import json
import re
import sys
from pathlib import Path
from urllib.parse import urljoin, urlsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from discover_sources import ATS_PATTERNS, CAREER_WORDS, fingerprint

OUT = ROOT / ".source-audit"
# Ilan listesi olma ihtimali olan yanit adresleri; olcut yalniz on elemedir, kanit degildir.
DATA_HINT = re.compile(r"job|ilan|position|pozisyon|career|kariyer|vacanc|opening|recruit|search", re.I)
TITLE_KEYS = ("title", "jobtitle", "name", "text", "positionname", "ilanadi", "jobname", "baslik")
# Cerez onayi ve icerik yonetimi cagrilari da baslik tasir; ilan kaydini ayirmak icin ikinci bir
# is alani aranir.
JOB_KEYS = ("location", "city", "sehir", "konum", "department", "departman", "birim", "pozisyon",
            "position", "joblocation", "jobid", "ilanno", "applyurl", "basvuruurl", "worktype",
            "employmenttype", "calismasekli", "publishdate", "yayintarihi", "deadline", "sonbasvuru")


def job_shape(payload):
    """Yanitin ilan listesine benzeyip benzemedigini yapisal olarak olcer."""
    def looks_like_job(row):
        keys = {k.lower() for k in row}
        return any(k in TITLE_KEYS for k in keys) and any(k in JOB_KEYS for k in keys)

    def rows(value, depth=0):
        if depth > 4:
            return None
        if isinstance(value, list):
            objects = [v for v in value if isinstance(v, dict)]
            if len(objects) >= 2 and any(looks_like_job(o) for o in objects):
                return objects
            return None
        if isinstance(value, dict):
            for child in value.values():
                found = rows(child, depth + 1)
                if found:
                    return found
        return None
    found = rows(payload)
    if not found:
        return None
    sample = []
    for row in found[:3]:
        title = next((str(row[k])[:70] for k in row if k.lower() in TITLE_KEYS and row[k]), "")
        if title:
            sample.append(title)
    return {"rows": len(found), "sample": sample, "keys": sorted(found[0])[:14]} if sample else None


def inspect(page_url, browser, record, timeout):
    calls = []

    def on_response(response):
        # Adres ipucu yerine yanitin yapisi elenir; ilan listeleri her zaman is/ilan adresinde durmaz.
        if response.request.resource_type not in ("xhr", "fetch"):
            return
        try:
            if "json" not in (response.header_value("content-type") or ""):
                return
            payload = response.json()
        except Exception:
            return
        shape = job_shape(payload)
        if shape:
            calls.append({"url": response.url[:300], "method": response.request.method,
                          "status": response.status, "hinted": bool(DATA_HINT.search(response.url)), **shape})

    page = browser.new_page(locale="tr-TR")
    page.on("response", on_response)
    page.set_default_timeout(timeout)
    try:
        page.goto(page_url, wait_until="domcontentloaded")
        page.wait_for_timeout(5000)
        html = page.content()
        record["pages"].append({"url": page.url, "status": 200, "title": (page.title() or "")[:110]})
        record["hits"] += fingerprint(html, page.url)
        links = []
        for anchor in page.query_selector_all("a[href]"):
            href = anchor.get_attribute("href") or ""
            text = (anchor.inner_text() or "")[:80]
            if href and not href.startswith(("#", "mailto:", "tel:", "javascript:")) and CAREER_WORDS.search(href + " " + text):
                links.append(urljoin(page.url, href))
        record["calls"] += calls
        return links
    except Exception as exc:
        record["errors"].append({"url": page_url, "error": type(exc).__name__ + ": " + str(exc)[:120]})
        record["calls"] += calls
        return []
    finally:
        page.close()


def discover(entry, browser, timeout):
    record = {"name": entry["name"], "home": entry["home"], "pages": [], "hits": [], "calls": [], "errors": []}
    visited = set()
    queue = [entry["home"]]
    for _ in range(4):
        if not queue:
            break
        url = queue.pop(0)
        if url in visited:
            continue
        visited.add(url)
        found = inspect(url, browser, record, timeout)
        # Yalniz adresinde de is/ilan gecen bir veri cagrisi gezinmeyi bitirir; kalan kayitlar
        # (cerez onayi, icerik yonetimi) taramayi erken kesmemeli.
        if record["hits"] or any(call.get("hinted") for call in record["calls"]):
            break
        host = urlsplit(entry["home"]).netloc
        queue += [u for u in found if u not in visited][:6]
        queue.sort(key=lambda u: urlsplit(u).netloc == host)
    unique = {}
    for hit in record["hits"]:
        unique.setdefault((hit["ats"], tuple(hit["groups"])), hit)
    record["hits"] = list(unique.values())
    record["ats"] = sorted({h["ats"] for h in record["hits"]})
    seen = set()
    record["calls"] = [c for c in record["calls"] if not (c["url"] in seen or seen.add(c["url"]))]
    return record


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("seed")
    parser.add_argument("--timeout", type=int, default=30000)
    parser.add_argument("--out", default=str(OUT / "discovered_browser.json"))
    args = parser.parse_args()
    entries = json.loads(Path(args.seed).read_text(encoding="utf-8"))
    from playwright.sync_api import sync_playwright
    rows = []
    OUT.mkdir(exist_ok=True)
    with sync_playwright() as runtime:
        browser = runtime.chromium.launch(headless=True)
        try:
            for entry in entries:
                row = discover(entry, browser, args.timeout)
                rows.append(row)
                print(json.dumps({"name": row["name"], "ats": row["ats"],
                                  "calls": [c["url"][:110] for c in row["calls"]][:3],
                                  "pages": len(row["pages"]), "errors": len(row["errors"])},
                                 ensure_ascii=False), flush=True)
                Path(args.out).write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        finally:
            browser.close()
    print(json.dumps({"total": len(rows), "with_ats": sum(bool(r["ats"]) for r in rows),
                      "with_data_call": sum(bool(r["calls"]) for r in rows)}, ensure_ascii=True))


if __name__ == "__main__":
    main()
