"""Toplu resmi kariyer kaynagi kesfi. Yalniz kamuya acik sayfalari okur; basvuru gondermez."""
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

CAREER_WORDS = re.compile(r"kariyer|career|insan-?kaynak|human-?resource|acik-?pozisyon|open-?position|"
                          r"is-?ilan|jobs?|basvur|yetenek|talent|is-?firsat|join-?us|bize-?katil", re.I)

# Kamuya acik ATS panolarinin adres imzalari. Yakalanan gruplar pano kimligidir.
ATS_PATTERNS = [
    ("lever", re.compile(r"https?://jobs\.(?:eu\.)?lever\.co/([A-Za-z0-9_.-]+)", re.I)),
    ("greenhouse", re.compile(r"https?://(?:boards|job-boards)\.(?:eu\.)?greenhouse\.io/(?:embed/job_board\?for=)?([A-Za-z0-9_.-]+)", re.I)),
    ("greenhouse", re.compile(r"greenhouse\.io/embed/job_board/js\?for=([A-Za-z0-9_.-]+)", re.I)),
    ("ashby", re.compile(r"https?://jobs\.ashbyhq\.com/([A-Za-z0-9_.-]+)", re.I)),
    ("workday", re.compile(r"https?://([a-z0-9-]+)\.(wd\d+)\.myworkdayjobs\.com/(?:wday/cxs/[a-z0-9-]+/)?(?:[a-z]{2}-[A-Z]{2}/)?([A-Za-z0-9_-]+)", re.I)),
    ("smartrecruiters", re.compile(r"https?://(?:careers|jobs)\.smartrecruiters\.com/([A-Za-z0-9_.-]+)", re.I)),
    ("recruitee", re.compile(r"https?://([a-z0-9-]+)\.recruitee\.com", re.I)),
    ("teamtailor", re.compile(r"https?://([a-z0-9-]+)\.teamtailor\.com", re.I)),
    ("workable", re.compile(r"https?://(?:apply|jobs)\.workable\.com/([A-Za-z0-9_.-]+)", re.I)),
    ("personio", re.compile(r"https?://([a-z0-9-]+)\.jobs\.personio\.(?:de|com)", re.I)),
    ("successfactors", re.compile(r"https?://career\d*\.(?:successfactors|sapsf)\.(?:eu|com)/[^\"'\s<>]*company=([A-Za-z0-9_]+)", re.I)),
    ("successfactors", re.compile(r"https?://performancemanager\d*\.successfactors\.(?:eu|com)/[^\"'\s<>]*company=([A-Za-z0-9_]+)", re.I)),
    ("hrpeak", re.compile(r"https?://([a-z0-9-]+)\.hrpeak\.com", re.I)),
    ("flowq", re.compile(r"https?://jobs\.flowq\.com/(?:view/)?([A-Za-z0-9_-]+)", re.I)),
    ("jobvite", re.compile(r"https?://jobs\.jobvite\.com/([A-Za-z0-9_.-]+)", re.I)),
    ("bamboohr", re.compile(r"https?://([a-z0-9-]+)\.bamboohr\.com/(?:careers|jobs)", re.I)),
    ("icims", re.compile(r"https?://([a-z0-9-]+)\.icims\.com", re.I)),
    ("taleo", re.compile(r"https?://([a-z0-9-]+)\.taleo\.net", re.I)),
    ("oracle_cloud", re.compile(r"https?://([a-z0-9-]+\.oraclecloud\.com)/hcmUI/CandidateExperience", re.I)),
    ("peoplise", re.compile(r"https?://([a-z0-9-]+)\.peoplise\.com", re.I)),
    ("eightfold", re.compile(r"https?://([a-z0-9.-]+)/careers/job/\d+", re.I)),
    ("kariyernet", re.compile(r"https?://(?:www\.)?kariyer\.net/(?:is-ilanlari/|firma/)([A-Za-z0-9_.-]+)", re.I)),
    ("yenibiris", re.compile(r"https?://(?:www\.)?yenibiris\.com/([A-Za-z0-9_./-]+)", re.I)),
    ("linkedin", re.compile(r"https?://(?:[a-z]{2,3}\.)?linkedin\.com/company/([A-Za-z0-9_.%-]+)/jobs", re.I)),
]

GUESS_PATHS = ["/kariyer", "/tr/kariyer", "/careers", "/career", "/en/careers",
               "/insan-kaynaklari", "/tr/insan-kaynaklari", "/acik-pozisyonlar", "/jobs"]


def fetch(session, url, tries=2, timeout=25):
    last = None
    for _ in range(tries):
        try:
            return session.get(url, headers=HEADERS, timeout=timeout, allow_redirects=True)
        except requests.RequestException as exc:
            last = exc
    raise last


def fingerprint(text, page_url):
    """Sayfa kaynagindaki ATS adreslerini bul. JS icine gomulu adresler de yakalanir."""
    found = {}
    for kind, pattern in ATS_PATTERNS:
        for match in pattern.finditer(text or ""):
            groups = tuple(g for g in match.groups() if g)
            found.setdefault((kind, groups), {"ats": kind, "groups": list(groups),
                                              "evidence": match.group(0)[:160], "found_on": page_url})
    return list(found.values())


def page_title(response):
    if response.status_code >= 400 or "html" not in response.headers.get("content-type", ""):
        return ""
    tag = BeautifulSoup(response.text, "html.parser").title
    return tag.get_text(strip=True)[:120] if tag else ""


def career_links(response, limit=8):
    soup = BeautifulSoup(response.text, "html.parser")
    host = urlsplit(response.url).netloc
    links, seen = [], set()
    for anchor in soup.select("a[href]"):
        href = anchor.get("href", "").strip()
        if not href or href.startswith(("#", "mailto:", "tel:", "javascript:")):
            continue
        if not CAREER_WORDS.search(href + " " + anchor.get_text(" ", strip=True)):
            continue
        url = urljoin(response.url, href)
        if urlsplit(url).scheme not in ("http", "https") or url in seen:
            continue
        seen.add(url)
        # Dis kariyer alan adlari once denenir; ATS yonlendirmesi genelde oradadir.
        links.append((0 if urlsplit(url).netloc != host else 1, url))
    links.sort()
    return [url for _, url in links[:limit]]


def discover(entry):
    name, home = entry["name"], entry["home"]
    record = {"name": name, "home": home, "pages": [], "hits": [], "errors": []}

    def visit(session, url, record):
        page = fetch(session, url)
        record["pages"].append({"url": page.url, "status": page.status_code, "title": page_title(page)})
        if page.status_code >= 400:
            return page, []
        record["hits"] += fingerprint(page.text, page.url)
        return page, career_links(page)

    with requests.Session() as session:
        visited = {home}
        try:
            first, queue = visit(session, home, record)
        except requests.RequestException as exc:
            record["errors"].append({"url": home, "error": type(exc).__name__})
            first, queue = None, []
        if not queue:
            queue = [urljoin(home, path) for path in GUESS_PATHS[:6]]
        for url in queue[:8]:
            if record["hits"]:
                break
            if url in visited:
                continue
            visited.add(url)
            try:
                _, deeper = visit(session, url, record)
            except requests.RequestException as exc:
                record["errors"].append({"url": url, "error": type(exc).__name__})
                continue
            for sub in deeper[:4]:
                if record["hits"] or sub in visited:
                    break
                visited.add(sub)
                try:
                    visit(session, sub, record)
                except requests.RequestException:
                    continue
    unique = {}
    for hit in record["hits"]:
        unique.setdefault((hit["ats"], tuple(hit["groups"])), hit)
    record["hits"] = list(unique.values())
    record["ats"] = sorted({h["ats"] for h in record["hits"]})
    return record


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("seed", help='JSON: [{"name": ..., "home": ...}]')
    parser.add_argument("--workers", type=int, default=12)
    parser.add_argument("--out", default=str(OUT / "discovered.json"))
    args = parser.parse_args()
    entries = json.loads(Path(args.seed).read_text(encoding="utf-8"))
    OUT.mkdir(exist_ok=True)
    rows = []
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        for row in pool.map(discover, entries):
            rows.append(row)
            print(json.dumps({"name": row["name"], "ats": row["ats"],
                              "hits": [h["groups"] for h in row["hits"]][:4],
                              "pages": len(row["pages"]), "errors": len(row["errors"])},
                             ensure_ascii=True), flush=True)
    Path(args.out).write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"total": len(rows), "with_ats": sum(bool(r["ats"]) for r in rows)}, ensure_ascii=True))


if __name__ == "__main__":
    main()
