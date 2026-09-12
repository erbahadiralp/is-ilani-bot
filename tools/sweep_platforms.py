"""Yaygin kariyer platformlarini sirket alan adlari uzerinde tarar. Once DNS, sonra kamuya acik GET."""
import argparse
import json
import re
import socket
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import urlsplit

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

OUT = ROOT / ".source-audit"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
HEADERS = {"User-Agent": UA, "Accept-Language": "tr,en;q=0.8"}
SUBDOMAINS = ["kariyer", "careers", "career", "ik", "jobs", "hr", "basvuru", "insankaynaklari",
              "kariyerim", "isbasvuru", "ikbasvuru", "join"]
# (yol, adapter turu) — her ikisi de tek GET ile ayirt edilebilen kamuya acik listelerdir.
PROBES = [("/search/?q=&startrow=0", "successfactors_csb"), ("/jobs", "hrpeak_browser"),
          ("/ilan/site.aspx", "hrpeak_browser")]
SHARED_PLATFORMS = False


def resolves(host):
    try:
        socket.getaddrinfo(host, 443, proto=socket.IPPROTO_TCP)
        return host
    except OSError:
        return None


def hosts_for(entry):
    domain = urlsplit(entry["home"]).netloc.replace("www.", "")
    label = domain.split(".")[0]
    names = [sub + "." + domain for sub in SUBDOMAINS]
    # hrpeak.com her alt adrese ayni genel sayfayi dondurur; sirket basligi eslesmedigi surece
    # kanit uretmez ve paylasilan sunucuyu gereksiz mesgul eder. Yalnizca --shared ile denenir.
    if SHARED_PLATFORMS:
        names += [label + ".hrpeak.com", label + ".bizdekariyer.com"]
    # Turkiye'de yaygin marka kariyer alan adlari (ornek: cimsakariyerim.com, sisecamkariyerim.com).
    for suffix in ("kariyerim.com", "kariyer.com", "kariyer.com.tr", "-kariyer.com", "careers.com"):
        names.append(label + suffix)
        names.append("www." + label + suffix)
    names.append("kariyer" + label + ".com")
    return names


SHARED_HOSTS = ("hrpeak.com", "bizdekariyer.com", "sapsf.eu", "successfactors.eu", "successfactors.com")
_HOST_LOCKS = {}
_LOCK_GUARD = threading.Lock()


class _NullGate:
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


_NO_GATE = _NullGate()


def host_gate(host):
    """Paylasilan platform sunucularina (ornegin *.hrpeak.com) ayni anda tek istek gonderilir.

    Kilit yalnizca bilinen platform alan adlarina uygulanir. Ad sonekine bakan genel bir kural
    Turkiye'deki `.com.tr` adreslerinin tamamini tek kuyruga sokar ve taramayi saatlerce uzatir.
    """
    for platform in SHARED_HOSTS:
        if host == platform or host.endswith("." + platform):
            with _LOCK_GUARD:
                return _HOST_LOCKS.setdefault(platform, threading.Lock())
    return _NO_GATE


def get(url, tries=2):
    last = None
    gate = host_gate(urlsplit(url).netloc)
    for _ in range(tries):
        try:
            with gate:
                response = requests.get(url, headers=HEADERS, timeout=15, allow_redirects=True)
                if gate is not _NO_GATE:
                    time.sleep(0.4)
            if response.status_code == 429:
                time.sleep(5)
                continue
            return response
        except requests.RequestException as exc:
            last = exc
            time.sleep(0.5)
    if last:
        raise last
    return response


def inspect(task):
    name, host, path, kind = task
    url = "https://" + host + path
    try:
        response = get(url)
    except requests.RequestException:
        return None
    if response.status_code >= 400 or "html" not in response.headers.get("content-type", ""):
        return None
    soup = BeautifulSoup(response.text, "html.parser")
    title = soup.title.get_text(strip=True)[:110] if soup.title else ""
    if kind == "successfactors_csb":
        ids = {m.group(1) for m in (re.search(r"/job/[^/]+/(\d+)/", a.get("href", "")) for a in soup.select("a[href]")) if m}
        rows = len(soup.select("tr.data-row"))
        if not ids and not rows:
            return None
        return {"name": name, "type": kind, "url": "https://" + host, "title": title,
                "jobs": max(len(ids), rows)}
    heading = soup.select_one(".page-menu-title, .menuSayfa")
    if heading is None or soup.select_one("#C_G") is None:
        return None
    return {"name": name, "type": kind, "url": url, "title": title,
            "heading": heading.get_text(" ", strip=True)[:80], "jobs": len(soup.select("a.PL[href]"))}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("seed")
    parser.add_argument("--workers", type=int, default=24)
    parser.add_argument("--out", default=str(OUT / "platform_sweep.json"))
    parser.add_argument("--shared", action="store_true",
                        help="Paylasilan platform sunucularini da dene (hrpeak.com, bizdekariyer.com)")
    args = parser.parse_args()
    global SHARED_PLATFORMS
    SHARED_PLATFORMS = args.shared
    entries = json.loads(Path(args.seed).read_text(encoding="utf-8"))
    pairs = [(entry["name"], host) for entry in entries for host in hosts_for(entry)]
    with ThreadPoolExecutor(max_workers=64) as pool:
        live = [(name, host) for (name, host), ok in zip(pairs, pool.map(lambda p: resolves(p[1]), pairs)) if ok]
    print(json.dumps({"candidate_hosts": len(pairs), "resolving": len(live)}, ensure_ascii=True), flush=True)
    tasks = [(name, host, path, kind) for name, host in live for path, kind in PROBES]
    rows = []
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        for row in pool.map(inspect, tasks):
            if row:
                rows.append(row)
                print(json.dumps(row, ensure_ascii=False), flush=True)
    Path(args.out).write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"hits": len(rows), "companies": len({r["name"] for r in rows})}, ensure_ascii=True))


if __name__ == "__main__":
    main()
