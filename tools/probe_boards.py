"""Aday kariyer adreslerinde gercek ilan listesi arar. Kamuya acik GET; basvuru veya giris yapmaz."""
import argparse
import json
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import urljoin, urlsplit

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

OUT = ROOT / ".source-audit"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
HEADERS = {"User-Agent": UA, "Accept-Language": "tr,en;q=0.8",
           "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"}

SUBDOMAINS = ["kariyer", "careers", "career", "ik", "jobs", "basvuru", "hr", "is"]
PATHS = ["/", "/search/?q=&startrow=0", "/jobs", "/acik-pozisyonlar", "/ilanlar",
         "/kariyer/acik-pozisyonlar", "/tr/kariyer/acik-pozisyonlar", "/is-ilanlari",
         "/acik-pozisyonlarimiz", "/open-positions", "/careers/open-positions"]
JOB_LINK = re.compile(r"/(?:job|jobs|ilan|is-ilani|pozisyon|position|vacancy|kariyer/[^/]*ilan)[/\-=]", re.I)
LOGIN = re.compile(r"(?:account/)?login|giris-yap|oturum a|sign in|kullanici adi|password", re.I)


def fetch(session, url, tries=2, timeout=20):
    last = None
    for _ in range(tries):
        try:
            return session.get(url, headers=HEADERS, timeout=timeout, allow_redirects=True)
        except requests.RequestException as exc:
            last = exc
    raise last


def classify(response):
    """Sayfanin gercek ilan listesi olup olmadigini kanit turleriyle isaretler."""
    if response.status_code >= 400 or "html" not in response.headers.get("content-type", ""):
        return None
    soup = BeautifulSoup(response.text, "html.parser")
    text = soup.get_text(" ", strip=True)
    signals = {}
    if soup.select("tr.data-row a.jobTitle-link[href]"):
        signals["successfactors_csb"] = len(soup.select("tr.data-row"))
    tiles = {m.group(1) for m in (re.search(r"/job/[^/]+/(\d+)/", a.get("href", "")) for a in soup.select("a[href]")) if m}
    if tiles:
        signals.setdefault("successfactors_csb", len(tiles))
    schema = [s for s in soup.select('script[type="application/ld+json"]') if "JobPosting" in (s.string or "")]
    if schema:
        signals["jsonld_jobposting"] = len(schema)
    if "hrpeak" in response.text.lower() or "bizdekariyer" in response.url:
        signals["hrpeak"] = 1
    links = {urljoin(response.url, a["href"]) for a in soup.select("a[href]") if JOB_LINK.search(a["href"])}
    links = {u for u in links if urlsplit(u).netloc == urlsplit(response.url).netloc}
    if len(links) >= 3:
        signals["job_links"] = len(links)
    return {"url": response.url, "status": response.status_code, "signals": signals,
            "login_wall": bool(LOGIN.search(text[:2000])),
            "title": (soup.title.get_text(strip=True)[:110] if soup.title else ""),
            "sample_links": sorted(links)[:5]}


def candidates(entry, discovered):
    home = entry["home"]
    root = urlsplit(home)
    domain = root.netloc.replace("www.", "")
    urls = []
    for page in discovered.get(entry["name"], {}).get("pages", []):
        if page.get("status", 500) < 400:
            urls.append(page["url"])
            urls.append(urljoin(page["url"], "/search/?q=&startrow=0"))
    for sub in SUBDOMAINS:
        urls.append("https://" + sub + "." + domain + "/")
        urls.append("https://" + sub + "." + domain + "/search/?q=&startrow=0")
    for path in PATHS:
        urls.append(urljoin(home, path))
    unique, seen = [], set()
    for url in urls:
        if url not in seen:
            seen.add(url)
            unique.append(url)
    return unique[:40]


def probe(job):
    entry, discovered = job
    record = {"name": entry["name"], "home": entry["home"], "found": []}
    with requests.Session() as session:
        for url in candidates(entry, discovered):
            try:
                response = fetch(session, url)
            except requests.RequestException:
                continue
            result = classify(response)
            if result and result["signals"]:
                record["found"].append(result)
            if any("successfactors_csb" in r["signals"] for r in record["found"]):
                break
    return record


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("seed")
    parser.add_argument("--discovered", default=str(OUT / "discovered.json"))
    parser.add_argument("--workers", type=int, default=14)
    parser.add_argument("--out", default=str(OUT / "boards.json"))
    args = parser.parse_args()
    entries = json.loads(Path(args.seed).read_text(encoding="utf-8"))
    discovered = {}
    if Path(args.discovered).exists():
        discovered = {r["name"]: r for r in json.loads(Path(args.discovered).read_text(encoding="utf-8"))}
    rows = []
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        for row in pool.map(probe, [(e, discovered) for e in entries]):
            rows.append(row)
            if row["found"]:
                best = max(row["found"], key=lambda r: sum(r["signals"].values()))
                print(json.dumps({"name": row["name"], "url": best["url"], "signals": best["signals"],
                                  "login": best["login_wall"]}, ensure_ascii=False), flush=True)
    Path(args.out).write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"total": len(rows), "with_board": sum(bool(r["found"]) for r in rows)}, ensure_ascii=True))


if __name__ == "__main__":
    main()
