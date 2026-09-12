"""Amazon's public search API in an anonymous Chromium session."""
from contextlib import contextmanager

@contextmanager
def search_api(url):
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            page = browser.new_page()
            response = page.goto(url, wait_until="domcontentloaded", timeout=30000)
            if response is None or response.status != 200:
                raise ValueError("Amazon public page unavailable")
            def fetch(start):
                body = {"accessLevel": "EXTERNAL", "excludeFacets": [{"name": "isConfidential", "values": [{"name": "1"}]}],
                        "filterFacets": [], "includeFacets": [], "jobTypeFacets": [],
                        "locationFacets": [[{"name": "country", "requestedFacetCount": 9999, "values": [{"name": "TR"}]}]],
                        "query": "", "size": 10, "start": start, "treatment": "OM", "sort": {"sortOrder": "DESCENDING", "sortType": "SCORE"}}
                result = page.evaluate("""async body => {
                    const controller = new AbortController();
                    const timeout = setTimeout(() => controller.abort(), 25000);
                    try {
                        const r = await fetch('/api/jobs/search?is_als=true', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(body), signal: controller.signal});
                        if (!r.ok) throw new Error('Amazon HTTP ' + r.status);
                        return await r.json();
                    } finally { clearTimeout(timeout); }
                }""", body)
                return result
            yield fetch
        finally:
            browser.close()
