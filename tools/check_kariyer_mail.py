"""İş Habercisi e-posta akisini kimlik bilgisi olmadan veya salt okunur IMAP ile dener.

Iki kip vardir:

  python tools/check_kariyer_mail.py ornek.eml
      Kaydedilmis bir e-postayi okur, okuyucunun hangi baglantiyi neden kabul/ret ettigini yazar.
      Ag baglantisi kurmaz, kimlik bilgisi istemez.

  python tools/check_kariyer_mail.py --imap
      .env icindeki KARIYER_IMAP_* degerleriyle salt okunur baglanir; klasoru acar, mesaj sayar ve
      son mesajlardan cikan ilanlari ozetler. Mesaj silmez, okundu isaretlemez, parola yazdirmaz.
"""
import argparse
import os
import sys
from email import message_from_bytes
from email.policy import default
from pathlib import Path
from urllib.parse import urlsplit

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("LOG_PATH", os.devnull)
from scrapers.kariyer_mail import KariyerMailScraper
from watchlist import relevant

BUTTON_TEXTS = ("hemen başvur", "başvur", "ilanı incele")


def explain(raw):
    """Mesajdaki her baglantiyi okuyucunun kurallarina gore siniflandirir."""
    message = message_from_bytes(raw, policy=default)
    rows, html_parts = [], 0
    for part in message.walk():
        if part.get_content_type() != "text/html" or part.get_content_disposition() == "attachment":
            continue
        html_parts += 1
        soup = BeautifulSoup(part.get_content(), "html.parser")
        for link in soup.select("a[href]"):
            href = link["href"]
            url = urlsplit(href)
            title = link.get_text(" ", strip=True)
            host = (url.hostname or "").lower()
            if url.scheme != "https":
                reason = "https degil"
            elif host not in ("kariyer.net", "www.kariyer.net"):
                reason = "farkli alan adi (yonlendirme/takip baglantisi cozulmez)"
            elif not url.path.startswith("/is-ilani/"):
                reason = "ilan adresi degil"
            elif len(title) < 5 or title.lower() in BUTTON_TEXTS:
                reason = "baglanti metni baslik degil (buton)"
            else:
                reason = "KABUL"
            rows.append({"host": host or "-", "path": url.path[:60], "title": title[:60], "reason": reason})
    return message, html_parts, rows


def report(raw, label):
    message, html_parts, rows = explain(raw)
    jobs = KariyerMailScraper.parse_message(raw)
    print("=" * 70)
    print("Kaynak:", label)
    print("Konu  :", (message.get("Subject") or "")[:90])
    print("Gonderen:", (message.get("From") or "")[:90])
    print("HTML bolum sayisi:", html_parts, "| baglanti:", len(rows), "| okuyucunun buldugu ilan:", len(jobs))
    if not html_parts:
        print("UYARI: mesajda text/html bolum yok; okuyucu yalniz HTML bolumleri okur.")
    hosts = {}
    for row in rows:
        hosts.setdefault(row["reason"], []).append(row)
    for reason, group in sorted(hosts.items(), key=lambda item: item[0] != "KABUL"):
        print(f"\n  [{reason}] {len(group)} baglanti")
        for row in group[:6]:
            print(f"    {row['host']:24s} {row['path']:60s} {row['title']}")
    if jobs:
        print("\n  Profil filtresinden gecenler:")
        for job in jobs:
            mark = "UYGUN" if relevant(job["title"]) else "elendi"
            print(f"    [{mark}] {job['title'][:70]}")
            print(f"            {job['url']}")
    print()
    return jobs


def imap_check():
    import imaplib
    host = os.getenv("KARIYER_IMAP_HOST")
    user = os.getenv("KARIYER_IMAP_USER")
    password = os.getenv("KARIYER_IMAP_PASSWORD")
    folder = os.getenv("KARIYER_IMAP_FOLDER")
    missing = [name for name, value in
               (("KARIYER_IMAP_HOST", host), ("KARIYER_IMAP_USER", user),
                ("KARIYER_IMAP_PASSWORD", password), ("KARIYER_IMAP_FOLDER", folder)) if not value]
    if missing:
        raise SystemExit("Eksik ayar: " + ", ".join(missing))
    print("Baglaniliyor:", host, "kullanici:", user, "klasor:", folder)
    with imaplib.IMAP4_SSL(host, timeout=25) as client:
        client.login(user, password)
        status, boxes = client.list()
        names = [line.decode("utf-8", "replace").split(' "/" ')[-1].strip('"') for line in boxes or []]
        print("Sunucudaki klasorler:", ", ".join(names[:25]))
        status, _ = client.select('"' + folder.replace('"', "") + '"', readonly=True)
        if status != "OK":
            raise SystemExit("Klasor acilamadi: " + folder + " — yukaridaki adlardan biriyle birebir eslesmeli.")
        status, data = client.uid("search", None, "ALL")
        uids = data[0].split()
        print("Klasordeki mesaj sayisi:", len(uids))
        if not uids:
            raise SystemExit("Klasor bos. Is Habercisi kuralinin bu klasore tasidigi mesaj yok.")
        for uid in uids[-3:]:
            status, parts = client.uid("fetch", uid, "(BODY.PEEK[])")
            for part in parts:
                if isinstance(part, tuple):
                    report(part[1], "IMAP uid " + uid.decode())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("eml", nargs="*", help="Kaydedilmis .eml dosyalari")
    parser.add_argument("--imap", action="store_true", help="Salt okunur IMAP baglantisini dene")
    args = parser.parse_args()
    if args.imap:
        imap_check()
        return
    if not args.eml:
        raise SystemExit("Bir .eml dosyasi verin veya --imap kullanin.")
    total = 0
    for path in args.eml:
        total += len(report(Path(path).read_bytes(), path))
    print("Toplam bulunan ilan:", total)


if __name__ == "__main__":
    main()
