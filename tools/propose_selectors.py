"""Kariyer sayfalarindaki tekrar eden ilan kartlarini bulup generic adapter ayari onerir.

Cikti adaydir, kanit degildir: onerilen ayar `tools/add_sources.py` ile eklenip
`tools/verify_candidates.py` ile gercek okuyucuda dogrulanmadan etkinlestirilmemelidir.
"""
import argparse
import json
import re
import sys
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import urljoin, urlsplit

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from watchlist import SENIOR, TECH, matches

OUT = ROOT / ".source-audit"
HEADERS = {"User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                          "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"),
           "Accept-Language": "tr,en;q=0.8"}
# Ilan basligina benzemeyen tekrar eden bloklari (haber, urun, menu) elemek icin.
NOISE = re.compile(r"cerez|çerez|cookie|haber|news|blog|urun|ürün|kampanya|bülten|bulten|iletisim|iletişim", re.I)
ROLE_WORDS = TECH + ["uzman", "muhendis", "mühendis", "specialist", "engineer", "analyst", "analist",
                     "asistan", "assistant", "yonetici", "yönetici", "sorumlu", "danisman", "danışman",
                     "temsilci", "operator", "operatör", "tekniker", "technician", "stajyer", "intern"]


def get(url, tries=3):
    last = None
    for _ in range(tries):
        try:
            response = requests.get(url, headers=HEADERS, timeout=25)
            if response.encoding is None or response.encoding.lower() in ("iso-8859-1", "latin-1"):
                response.encoding = response.apparent_encoding or "utf-8"
            return response
        except requests.RequestException as exc:
            last = exc
            time.sleep(0.6)
    raise last


def signature(tag):
    classes = [c for c in (tag.get("class") or []) if not re.fullmatch(r"[a-z]*\d{3,}[a-z0-9]*", c)]
    return tag.name + ("." + ".".join(sorted(classes)) if classes else "")


def candidates(soup, page_url):
    """Ayni imzayi tasiyan, her biri tek ilan bagi ve basligi olan kardes bloklari toplar."""
    host = urlsplit(page_url).netloc
    groups = Counter()
    members = {}
    for tag in soup.find_all(True):
        links = tag.select("a[href]")
        if len(links) != 1:
            continue
        text = tag.get_text(" ", strip=True)
        if not 8 <= len(text) <= 300 or NOISE.search(text):
            continue
        url = urljoin(page_url, links[0].get("href", ""))
        if urlsplit(url).netloc != host or urlsplit(url).path.rstrip("/") == urlsplit(page_url).path.rstrip("/"):
            continue
        key = (signature(tag), signature(tag.parent) if tag.parent else "")
        groups[key] += 1
        members.setdefault(key, []).append((text[:90], url))
    results = []
    for (sig, parent_sig), count in groups.most_common(12):
        if count < 3 or "." not in sig:
            continue
        rows = members[(sig, parent_sig)]
        titles = [t for t, _ in rows]
        if len({u for _, u in rows}) < 3:
            continue
        roles = sum(any(matches(t, w) for w in ROLE_WORDS) or any(matches(t, w) for w in SENIOR) for t in titles)
        results.append({"selector": sig, "parent": parent_sig, "count": count,
                        "role_like": roles, "sample": titles[:4],
                        "sample_urls": [u for _, u in rows[:3]]})
    results.sort(key=lambda r: (-r["role_like"], -r["count"]))
    return results


def analyze(entry):
    record = {"name": entry["name"], "url": entry["url"], "proposals": []}
    try:
        response = get(entry["url"])
    except requests.RequestException as exc:
        record["error"] = type(exc).__name__
        return record
    record["status"] = response.status_code
    if response.status_code >= 400 or "html" not in response.headers.get("content-type", ""):
        return record
    soup = BeautifulSoup(response.text, "html.parser")
    for tag in soup.select("script, style, nav, footer, header"):
        tag.decompose()
    record["title"] = soup.title.get_text(strip=True)[:110] if soup.title else ""
    record["proposals"] = candidates(soup, response.url)
    return record


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("pages", help='JSON: [{"name": ..., "url": ...}]')
    parser.add_argument("--workers", type=int, default=10)
    parser.add_argument("--out", default=str(OUT / "selector_proposals.json"))
    args = parser.parse_args()
    entries = json.loads(Path(args.pages).read_text(encoding="utf-8"))
    OUT.mkdir(exist_ok=True)
    rows = []
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        for row in pool.map(analyze, entries):
            rows.append(row)
            if row["proposals"]:
                best = row["proposals"][0]
                print(json.dumps({"name": row["name"], "url": row["url"], "selector": best["selector"],
                                  "count": best["count"], "role_like": best["role_like"],
                                  "sample": best["sample"][:3]}, ensure_ascii=False), flush=True)
    Path(args.out).write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"pages": len(rows), "with_proposal": sum(bool(r["proposals"]) for r in rows)},
                     ensure_ascii=True))


if __name__ == "__main__":
    main()
