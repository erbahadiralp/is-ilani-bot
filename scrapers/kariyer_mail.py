"""Kariyer.net Is Habercisi e-postalari. Siteye HTTP istegi gondermez."""
import email
import imaplib
import os
from email.policy import default
from urllib.parse import urlsplit, urlunsplit
from bs4 import BeautifulSoup
from .base import BaseScraper

class KariyerMailScraper(BaseScraper):
    SOURCE_NAME = "kariyer_mail"

    @staticmethod
    def parse_message(raw):
        message = email.message_from_bytes(raw, policy=default)
        jobs = {}
        for part in message.walk():
            if part.get_content_type() != "text/html" or part.get_content_disposition() == "attachment":
                continue
            soup = BeautifulSoup(part.get_content(), "html.parser")
            for link in soup.select("a[href]"):
                url = urlsplit(link["href"])
                if url.scheme != "https" or (url.hostname or "").lower() not in ("kariyer.net", "www.kariyer.net"):
                    continue
                if not url.path.startswith("/is-ilani/"):
                    continue
                canonical = urlunsplit(("https", "www.kariyer.net", url.path, "", ""))
                title = link.get_text(" ", strip=True)
                if len(title) < 5 or title.lower() in ("hemen başvur", "başvur", "ilanı incele"):
                    continue
                jobs[canonical] = {"title": title, "company": "E-postadaki ilan", "location": "Belirtilmemiş",
                                   "url": canonical, "source": "kariyer"}
        return list(jobs.values())

    def scrape(self):
        host = os.getenv("KARIYER_IMAP_HOST")
        if not host:
            return []
        user = os.environ["KARIYER_IMAP_USER"]
        password = os.environ["KARIYER_IMAP_PASSWORD"]
        folder = os.environ["KARIYER_IMAP_FOLDER"]
        jobs = {}
        with imaplib.IMAP4_SSL(host, timeout=20) as client:
            client.login(user, password)
            status, _ = client.select('"' + folder.replace('"', '') + '"', readonly=True)
            if status != "OK":
                raise RuntimeError("Kariyer posta klasoru acilamadi")
            status, data = client.uid("search", None, "ALL")
            if status != "OK":
                raise RuntimeError("Kariyer posta aramasi basarisiz")
            for uid in data[0].split()[-100:]:
                status, parts = client.uid("fetch", uid, "(BODY.PEEK[])")
                if status != "OK":
                    raise RuntimeError("Kariyer e-postasi okunamadi")
                for part in parts:
                    if isinstance(part, tuple):
                        for job in self.parse_message(part[1]):
                            if self.passes_filter(job["title"]):
                                jobs[job["url"]] = job
        return list(jobs.values())
