"""Read anonymous SuccessFactors classic listings; no account or application actions."""
import re
from urllib.parse import urlsplit, parse_qs, urlencode, urlunsplit
from bs4 import BeautifulSoup


def parse_page(html, source_url, tenant):
    soup = BeautifulSoup(html, "html.parser")
    headings = soup.select('[role="heading"][aria-level="2"], h2')
    counts = [re.search(r"(\d+)\s+(?:jobs?|iş)\b", h.get_text(" ", strip=True), re.I) for h in headings]
    counts = [int(m.group(1)) for m in counts if m]
    if len(set(counts)) != 1:
        raise ValueError("SuccessFactors result count missing or ambiguous")
    total = counts[0]
    rows = []
    for link in soup.select("a.jobTitle[href]"):
        query = parse_qs(urlsplit(link["href"]).query)
        pid = query.get("career_job_req_id", [""])[0]
        if query.get("company") != [tenant] or not pid.isdigit():
            raise ValueError("SuccessFactors unexpected company or job ID")
        parts = urlsplit(source_url)
        url = urlunsplit((parts.scheme, parts.netloc, "/career", urlencode({"career_ns": "job_listing", "company": tenant, "career_job_req_id": pid}), ""))
        rows.append((link.get_text(" ", strip=True), url))
    if (not rows and total) or len(rows) > total:
        raise ValueError("SuccessFactors incomplete result page")
    return rows, total


def read_jobs(company):
    from playwright.sync_api import sync_playwright
    with sync_playwright() as runtime:
        browser = runtime.chromium.launch(headless=True)
        try:
            page = browser.new_page(locale="tr-TR")
            page.set_default_timeout(45000)
            page.goto(company["url"], wait_until="domcontentloaded")
            # Ayni klasik portal kiraciya gore Turkce veya Ingilizce arama dugmesi gosterir.
            names = company.get("search_button_names", ["İş Ara", "Search Jobs", "Ara", "Search"])
            for index, name in enumerate(names):
                try:
                    page.get_by_role("button", name=name, exact=True).click(timeout=8000)
                    break
                except Exception:
                    if index == len(names) - 1:
                        raise ValueError("SuccessFactors search button not found: " + ", ".join(names))
            jobs, seen = [], set()
            for _ in range(company.get("max_pages", 30)):
                page.wait_for_function(r"""() => [...document.querySelectorAll('[role="heading"][aria-level="2"],h2')].some(h => /\d+\s*(jobs?|iş)/i.test(h.innerText))""")
                rows, total = parse_page(page.content(), company["url"], company["tenant"])
                for title, url in rows:
                    if url in seen:
                        raise ValueError("SuccessFactors pagination repeated a job")
                    seen.add(url)
                    jobs.append((title, url))
                if len(jobs) >= total:
                    return jobs
                next_page = page.locator('li[id$=":_next"]:not(.disabledArrow)').first
                if not next_page.count():
                    raise ValueError("SuccessFactors pagination ended before result count")
                first_href = page.locator("a.jobTitle").first.get_attribute("href")
                next_page.click()
                page.wait_for_function("old => document.querySelector('a.jobTitle')?.getAttribute('href') !== old", arg=first_href)
            raise ValueError("SuccessFactors page limit reached")
        finally:
            browser.close()
