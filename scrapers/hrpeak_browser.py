"""Anonymous HRPeak public listings rendered by Chromium; no candidate login."""
from urllib.parse import urljoin, urlsplit
from bs4 import BeautifulSoup
from watchlist import normalize


def parse_list(html, url, expected_company):
    soup = BeautifulSoup(html, "html.parser")
    # Portalin iki temasi ayni listeyi farkli sinif adlariyla yayinlar.
    heading = soup.select_one(".page-menu-title, .menuSayfa")
    if heading is None or normalize(expected_company) not in normalize(heading.get_text(" ", strip=True)):
        raise ValueError("HRPeak company heading missing or changed")
    table = soup.select_one("#C_G")
    if table is None:
        raise ValueError("HRPeak listing table missing")
    # Never silently return a partial list if the portal introduces pagination.
    if table.select(".GP a, .pager a, .pagination a, a[href*=Page]"):
        raise ValueError("HRPeak pagination requires review; partial list rejected")
    rows = []
    for card in table.select("tr.GR, tr.GAR"):
        link = card.select_one("a.PL[href]")
        if link is None:
            raise ValueError("HRPeak job link missing")
        target = urljoin(url, link["href"])
        if urlsplit(target).netloc != urlsplit(url).netloc or not urlsplit(target).path.lower().endswith(".job"):
            raise ValueError("HRPeak unexpected job URL")
        title = link.get_text(" ", strip=True)
        if not title:
            raise ValueError("HRPeak empty title")
        location = card.select_one(".location")
        rows.append(dict(title=title, url=target, location=location.get_text(" ", strip=True) if location else "Türkiye"))
    empty = table.select_one(".no-record, .kayitBulunamadi")
    if not rows and not (empty and "yayınlanmış bir açık pozisyon bulunamadı" in empty.get_text(" ", strip=True).casefold()):
        raise ValueError("HRPeak empty state not confirmed")
    if len({r["url"] for r in rows}) != len(rows):
        raise ValueError("HRPeak duplicate job rows")
    return rows


def parse_detail(html, expected_title):
    soup = BeautifulSoup(html, "html.parser")
    title = soup.select_one(".ilan h3")
    content = soup.select_one(".ilanMetni")
    if title is None or normalize(title.get_text(" ", strip=True)) != normalize(expected_title) or content is None:
        raise ValueError("HRPeak job detail missing or redirected")
    description = content.get_text(" ", strip=True)
    if len(description) < 50:
        raise ValueError("HRPeak job description incomplete")
    return description


def read_jobs(url, expected_company):
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            page = browser.new_page(locale="tr-TR")
            page.set_default_timeout(30000)
            def visit(target):
                response = page.goto(target, wait_until="domcontentloaded")
                if response is None or response.status != 200:
                    raise ValueError("HRPeak HTTP response: " + str(response.status if response else None))
                if urlsplit(page.url).netloc != urlsplit(url).netloc:
                    raise ValueError("HRPeak redirected outside source")
                return page.content()
            rows = parse_list(visit(url), url, expected_company)
            for row in rows:
                row["description"] = parse_detail(visit(row["url"]), row["title"])
            return rows
        finally:
            browser.close()
