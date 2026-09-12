"""Official company/ATS job sources. Public job searches only; no application submission."""
import json
import logging
import os
import re
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from urllib.parse import urljoin, urlsplit, urlunsplit, parse_qsl, urlencode

import requests
from bs4 import BeautifulSoup
from watchlist import read_radar, relevant, program_name, matches, TECH, SENIOR, normalize
from .base import BaseScraper
from .verified_tls import get_isbank

COMPANIES_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "companies.json")
TR_LOCATIONS = ["tr", "turkey", "turkiye", "istanbul", "ankara", "izmir", "antalya", "bursa", "kocaeli",
                "gebze", "eskisehir", "mersin", "iskenderun", "tekirdag", "tur", "sariyer", "atasehir", "kucukyali", "maltepe", "pendik"]


def plain(value):
    return BeautifulSoup(str(value or ""), "html.parser").get_text(" ", strip=True)


def expired(value):
    if not value:
        return False
    try:
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(value)):
            return datetime.fromisoformat(str(value)).date() < datetime.now(ZoneInfo("Europe/Istanbul")).date()
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt < datetime.now(timezone.utc)
    except ValueError:
        return False


def canonical(url):
    p = urlsplit(url)
    query = [(k,v) for k,v in parse_qsl(p.query, keep_blank_values=True)
             if not k.lower().startswith("utm_") and k.lower() not in ("gh_src", "lever-source", "lever-origin", "trk")]
    return urlunsplit((p.scheme, p.netloc.lower(), p.path, urlencode(query), ""))


def jsonld(soup):
    def walk(value):
        if isinstance(value, list):
            for item in value:
                yield from walk(item)
        elif isinstance(value, dict):
            types = value.get("@type", [])
            if "JobPosting" in (types if isinstance(types, list) else [types]):
                yield value
            else:
                for child in value.values():
                    if isinstance(child, (list, dict)):
                        yield from walk(child)
    for script in soup.select('script[type="application/ld+json"]'):
        try:
            yield from walk(json.loads(script.string or script.get_text()))
        except (ValueError, TypeError):
            continue


class CompanyScraper(BaseScraper):
    SOURCE_NAME = "company"
    _detail_cache = {}

    def __init__(self):
        super().__init__()
        with open(COMPANIES_FILE, encoding="utf-8") as f:
            self.companies = json.load(f)
        names = {normalize(c["name"]) for c in read_radar()[0]}
        self.companies = [c for c in self.companies if c.get("extra_source", False) or any(normalize(n) in names for n in [c["name"], *c.get("aliases", [])])]
        self.source_results = []
        self.raw_count = 0

    def _get_request(self, url, **kwargs):
        getter = get_isbank if urlsplit(url).hostname == "ik.isbank.com.tr" else requests.get
        response = getter(url, timeout=kwargs.pop("timeout", 25), **kwargs)
        response.raise_for_status()
        # requests defaults text/html without charset to latin-1, corrupting Turkish titles.
        if response.encoding is None or response.encoding.lower() in ("iso-8859-1", "latin-1"):
            response.encoding = response.apparent_encoding or "utf-8"
        return response

    def scrape_company(self, company):
        self.raw_count = 0
        method = getattr(self, "_scrape_" + company.get("type", "generic"), None)
        if method is None:
            raise ValueError("Unsupported source type: " + company.get("type", ""))
        return list({job["url"]: job for job in method(company)}.values())

    def scrape(self):
        self.source_results = []
        jobs = {}
        def check(company):
            worker = CompanyScraper()
            worker._detail_cache = {}
            try:
                found = worker.scrape_company(company)
                return found, {"name": company["name"], "status": "ok", "raw": worker.raw_count, "eligible": len(found)}
            except Exception as exc:
                return [], {"name": company["name"], "status": "error", "error": str(exc)}
        enabled = [c for c in self.companies if c.get("enabled", True)]
        with ThreadPoolExecutor(max_workers=4) as pool:
            for found, result in pool.map(check, enabled):
                self.source_results.append(result)
                jobs.update({job["url"]: job for job in found})
                if result["status"] == "ok":
                    self.logger.info("%s: %d ilan okundu, %d uygun", result["name"], result["raw"], result["eligible"])
                else:
                    self.logger.error("%s: kaynak okunamadi: %s", result["name"], result["error"])
        return list(jobs.values())

    def _job(self, company, title, url, location="", description="", deadline="", published=""):
        if not title or urlsplit(url).scheme not in ("https", "http") or expired(deadline):
            return None
        if not relevant(title, plain(description)):
            return None
        if company.get("country_scope") == "TR":
            known_tr = any(matches(location, k) for k in TR_LOCATIONS)
            if not known_tr and not (not location and company.get("local_only", False)):
                return None
        return {"title": title.strip(), "company": company["name"], "source": "company",
                "location": location or "Belirtilmemiş", "url": canonical(url), "program": program_name(title),
                "application_deadline": deadline, "published_at": published}

    def _scrape_lever(self, company):
        data = self._get_request(company["api_url"]).json()
        if not isinstance(data, list):
            raise ValueError("Lever jobs response is not a list")
        self.raw_count += len(data)
        jobs = []
        for item in data:
            description = " ".join(str(item.get(k) or "") for k in ("descriptionPlain", "description", "additionalPlain"))
            description += " " + " ".join(str(x.get("content", "")) for x in item.get("lists", []))
            job = self._job(company, item.get("text", ""), item.get("hostedUrl") or item.get("applyUrl") or "",
                            item.get("categories", {}).get("location", ""), description)
            if job:
                jobs.append(job)
        return jobs

    def _scrape_greenhouse(self, company):
        url = company["api_url"]
        url += ("&" if "?" in url else "?") + "content=true" if "content=true" not in url else ""
        data = self._get_request(url).json()
        if not isinstance(data, dict) or not isinstance(data.get("jobs"), list):
            raise ValueError("Greenhouse jobs response has no jobs list")
        self.raw_count += len(data["jobs"])
        jobs = []
        for item in data["jobs"]:
            job = self._job(company, item.get("title", ""), item.get("absolute_url", ""),
                            item.get("location", {}).get("name", ""), item.get("content", ""))
            if job:
                jobs.append(job)
        return jobs

    def _scrape_ashby(self, company):
        data = self._get_request(company["api_url"]).json()
        if not isinstance(data, dict) or not isinstance(data.get("jobs"), list):
            raise ValueError("Ashby response has no jobs list")
        self.raw_count += len(data["jobs"])
        jobs = []
        for item in data["jobs"]:
            if not item.get("isListed", True):
                continue
            locations = [item.get("location", "")] + [x.get("location", "") for x in item.get("secondaryLocations", [])]
            job = self._job(company, item.get("title", ""), item.get("jobUrl") or item.get("applyUrl") or "",
                            "; ".join(locations), item.get("descriptionPlain") or item.get("descriptionHtml", ""),
                            published=item.get("publishedAt", ""))
            if job:
                jobs.append(job)
        return jobs

    def _scrape_workday(self, company):
        if company.get("additional_boards"):
            primary = {k:v for k,v in company.items() if k != "additional_boards"}
            jobs = self._scrape_workday(primary)
            for board in company["additional_boards"]:
                jobs.extend(self._scrape_workday({**primary, **board}))
            return jobs
        base = company["api_url"].rstrip("/")
        def query(offset, facets):
            # Workday uses POST for read-only searches, not application submission.
            response = requests.post(base + "/jobs", json={"limit":20, "offset":offset,
                "searchText":"", "appliedFacets":facets}, timeout=25)
            response.raise_for_status()
            data = response.json()
            if not isinstance(data.get("jobPostings"), list) or not isinstance(data.get("total"), int):
                raise ValueError("Workday list schema changed")
            return data
        initial = query(0, {})
        if initial["total"] == 0:
            return []
        def countries(facets):
            for facet in facets:
                if "countr" in ((facet.get("descriptor") or "") + " " + (facet.get("facetParameter") or "")).lower():
                    yield facet
                yield from countries(facet.get("values", []))
        country_facets = list(countries(initial.get("facets", [])))
        selected = {}
        for facet in country_facets:
            ids = [v["id"] for v in facet.get("values", []) if normalize(v.get("descriptor", "")) in ("turkey", "turkiye", "turkey (turkiye)")]
            if ids and facet.get("facetParameter"):
                selected = {facet["facetParameter"]:ids}
                break
        if not selected and not country_facets:
            def locations(facets):
                for facet in facets:
                    if facet.get("facetParameter") == "locations":
                        yield facet
                    yield from locations(facet.get("values", []))
            location_facets = list(locations(initial.get("facets", [])))
            for facet in location_facets:
                ids = [v["id"] for v in facet.get("values", []) if any(matches(v.get("descriptor", ""), k) for k in TR_LOCATIONS)]
                if ids:
                    selected = {"locations":ids}
                    break
            if not selected:
                if location_facets:
                    return []  # No known Turkey location in the published location filter.
                raise ValueError("Workday has no country facet or location filter")
        if not selected:
            return []  # Country facet has no open positions in Turkey.
        jobs, seen, offset = [], set(), 0
        for _ in range(company.get("max_pages", 100)):
            data = query(offset, selected)
            rows = data["jobPostings"]
            if not rows and offset < data["total"]:
                raise ValueError("Workday pagination ended early")
            for item in rows:
                path = item.get("externalPath", "")
                if not path.startswith("/job/") or path in seen:
                    raise ValueError("Workday missing or repeated job path")
                seen.add(path)
                self.raw_count += 1
                title = item.get("title", "")
                if any(matches(title, k) for k in SENIOR):
                    continue
                if not (relevant(title) or any(matches(title, k) for k in TECH)):
                    continue
                detail = self._get_request(base + path).json().get("jobPostingInfo")
                if not isinstance(detail, dict) or not detail.get("jobDescription"):
                    raise ValueError("Workday job description missing")
                job = self._job(company, title, company["url"].rstrip("/") + path,
                    "Türkiye — " + (detail.get("location") or item.get("locationsText", "")),
                    detail["jobDescription"], detail.get("endDate", ""), detail.get("startDate", ""))
                if job:
                    jobs.append(job)
            offset += len(rows)
            if offset >= data["total"]:
                return jobs
        raise ValueError("Workday page limit reached")

    def _scrape_smartrecruiters(self, company):
        jobs, seen, offset = [], set(), 0
        for _ in range(company.get("max_pages", 100)):
            parts = urlsplit(company["api_url"])
            params = dict(parse_qsl(parts.query))
            params.update(country="tr", limit="100", offset=str(offset))
            data = self._get_request(urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(params), ""))).json()
            if not isinstance(data.get("content"), list) or not isinstance(data.get("totalFound"), int):
                raise ValueError("SmartRecruiters list schema changed")
            rows = data["content"]
            if not rows and offset < data["totalFound"]:
                raise ValueError("SmartRecruiters pagination ended before totalFound")
            for item in rows:
                if not item.get("id") or item["id"] in seen:
                    raise ValueError("SmartRecruiters repeated or missing ID")
                seen.add(item["id"])
                self.raw_count += 1
                loc = item.get("location", {})
                if loc.get("country", "").lower() != "tr":
                    continue
                if company.get("brand") and not any(x.get("fieldLabel") == "Brands" and x.get("valueLabel") == company["brand"] for x in item.get("customField", [])):
                    continue
                title = item.get("name", "")
                if any(matches(title, k) for k in SENIOR):
                    continue
                if not (relevant(title) or any(matches(title, k) for k in TECH)):
                    continue
                detail_url = parts.scheme + "://" + parts.netloc + parts.path + "/" + item["id"]
                detail = self._get_request(detail_url).json()
                if detail.get("active") is False:
                    continue
                sections = detail.get("jobAd", {}).get("sections", {})
                if not sections:
                    raise ValueError("SmartRecruiters job description missing")
                description = " ".join(str(x.get("text", "")) for x in sections.values() if isinstance(x, dict))
                if item.get("experienceLevel", {}).get("id") == "entry_level":
                    description += " New graduates are welcome"
                job = self._job(company, title, detail.get("postingUrl", ""),
                                loc.get("fullLocation") or (loc.get("city", "") + ", Türkiye"), description,
                                published=item.get("releasedDate", ""))
                if job:
                    jobs.append(job)
            offset += len(rows)
            if offset >= data["totalFound"]:
                return jobs
        raise ValueError("SmartRecruiters page limit reached")

    def _scrape_baykar(self, company):
        jobs, seen, visited = [], set(), set()
        url = company["api_url"]
        for _ in range(company.get("max_pages", 100)):
            if url in visited or urlsplit(url).netloc != urlsplit(company["api_url"]).netloc:
                raise ValueError("Baykar pagination loop or unexpected host")
            visited.add(url)
            data = self._get_request(url).json()
            if not isinstance(data.get("results"), list) or not isinstance(data.get("count"), int):
                raise ValueError("Baykar list schema changed")
            for item in data["results"]:
                if not item.get("id") or item["id"] in seen:
                    raise ValueError("Baykar repeated or missing ID")
                seen.add(item["id"])
                self.raw_count += 1
                if not item.get("active") or not item.get("visible") or item.get("stop_application"):
                    continue
                title = item.get("text", "")
                if any(matches(title, k) for k in SENIOR):
                    continue
                if not (relevant(title) or any(matches(title, k) for k in TECH)):
                    continue
                if not item.get("new_slug"):
                    raise ValueError("Baykar job URL missing")
                job_url = urljoin(company["url"], "/tr/acik-pozisyonlar/detay/" + item["new_slug"])
                details = self._detail(company, job_url)
                job = self._job(company, title, job_url, "Türkiye", **details)
                if job:
                    jobs.append(job)
                self.random_sleep(0.3, 0.6)
            url = data.get("next")
            if not url:
                if len(seen) != data["count"]:
                    raise ValueError("Baykar pagination count mismatch")
                return jobs
        raise ValueError("Baykar page limit reached")

    def _scrape_akbank(self, company):
        def read(path, payload):
            response = requests.post(company["api_url"] + path, json=payload, timeout=25)
            response.raise_for_status()
            return response.json()
        def date(value):
            return datetime.fromtimestamp(value / 1000, timezone.utc).isoformat() if isinstance(value, (int, float)) else (value or "")
        rows = read("/advert/list", {})
        if not isinstance(rows, list):
            raise ValueError("Akbank list schema changed")
        self.raw_count += len(rows)
        jobs = []
        for item in rows:
            if not item.get("id") or not item.get("title"):
                raise ValueError("Akbank job identity missing")
            if normalize(item.get("experience") or "") == "profesyonelim":
                continue  # Official profile category explicitly requires experienced applicants.
            title = item["title"]
            deadline = date(item.get("applicationDeadLine"))
            if expired(deadline) or any(matches(title, k) for k in SENIOR):
                continue
            if not (relevant(title) or any(matches(title, k) for k in TECH)):
                continue
            detail = read("/advert/detail", {"id":item["id"]})
            if not isinstance(detail, dict) or not (detail.get("jobDescription") or detail.get("jobQualifications")):
                raise ValueError("Akbank job description missing")
            description = " ".join(str(detail.get(k) or "") for k in ("jobDescription", "jobQualifications", "jobSoIsThatAllExplanation"))
            if normalize(item.get("experience") or "") == "yeni mezunum":
                description += " Yeni mezun adaylar"
            job = self._job(company, title, company["url"].rstrip("/") + "/shared/advert-list/" + item["id"],
                item.get("city") or "Türkiye", description, deadline, date(item.get("createDate")))
            if job:
                jobs.append(job)
        return jobs

    def _scrape_qnb(self, company):
        # Same public GET flow as qnbkariyer.com's JavaScript; no user login or application.
        with requests.Session() as session:
            token = session.get(company["api_url"] + "/token", timeout=25)
            token.raise_for_status()
            response = session.get(company["api_url"] + "/ilanlar", timeout=25,
                                   headers={"X-CSRF-TOKEN": token.text.strip()})
            response.raise_for_status()
            data = response.json()
        if not isinstance(data, dict) or not isinstance(data.get("ilanlar"), list):
            raise ValueError("QNB response has no ilanlar list")
        self.raw_count += len(data["ilanlar"])
        jobs = []
        for item in data["ilanlar"]:
            if not item.get("slug") or not item.get("title"):
                raise ValueError("QNB job schema changed")
            title = item["title"]
            if item.get("header") and item["header"] != title:
                title = item["header"] + " — " + title
            job = self._job(company, title, "https://www.qnbkariyer.com/ilan?" + urlencode({"id": item["slug"]}),
                            item.get("city") or "Türkiye", deadline=item.get("end_date", ""))
            if job:
                jobs.append(job)
        return jobs

    def _scrape_turkcell(self, company):
        jobs, seen = [], set()
        for page in range(company.get("max_pages", 30)):
            parts = urlsplit(company["api_url"])
            params = dict(parse_qsl(parts.query, keep_blank_values=True))
            params["PageIndex"] = str(page)
            data = self._get_request(urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(params), ""))).json()
            if not isinstance(data, dict) or not isinstance(data.get("result"), list):
                raise ValueError("Turkcell response has no result list")
            rows = data["result"]
            if not rows:
                return jobs
            fresh = [row for row in rows if row.get("JobID") not in seen]
            if not fresh:
                return jobs  # Handler may return the full list for every PageIndex.
            self.raw_count += len(fresh)
            for item in fresh:
                seen.add(item.get("JobID"))
                job = self._job(company, re.sub(r"^\d+\s*-\s*", "", item.get("JobName", "")),
                                item.get("PortalURL", ""), item.get("Location", ""),
                                item.get("StringJobQualification", ""), item.get("LastApplicationdate", ""),
                                item.get("JobPublishDate", ""))
                if job:
                    jobs.append(job)
        raise ValueError("Turkcell page limit reached; coverage incomplete")

    def _detail(self, company, url):
        cached = self._detail_cache.get(url)
        if cached and time.monotonic() - cached[0] < 900:
            return cached[1]
        response = self._get_request(url)
        soup = BeautifulSoup(response.text, "html.parser")
        for tag in soup.select("script:not([type='application/ld+json']), style, nav, footer, header"):
            tag.decompose()
        schema = list(jsonld(soup))
        if schema:
            value = schema[0]
            result = {"description": value.get("description", ""), "deadline": value.get("validThrough", ""),
                      "published": value.get("datePosted", "")}
        else:
            content = soup.select_one(company.get("detail_selector", "main, article, #job-description, body"))
            if content is None:
                raise ValueError("Job detail selector did not match: " + url)
            result = {"description": content.get_text(" ", strip=True)}
        self._detail_cache[url] = (time.monotonic(), result)
        return result

    def _scrape_albarakatech(self, company):
        response = self._get_request(company["url"])
        soup = BeautifulSoup(response.text, "html.parser")
        panels = soup.select('.tab-pane:has(a.apply-btn[href])')
        if not panels:
            raise ValueError("AlbarakaTech job panels missing; layout or empty state needs checking")
        jobs = []
        for panel in panels:
            heading = soup.find(id=panel.get("aria-labelledby", ""))
            link = panel.select_one("a.apply-btn[href]")
            if heading is None or link is None:
                raise ValueError("AlbarakaTech job title or application link missing")
            self.raw_count += 1
            job = self._job(company, heading.get_text(" ", strip=True),
                            urljoin(response.url, link["href"].strip()), "Türkiye",
                            description=panel.get_text(" ", strip=True))
            if job:
                jobs.append(job)
        return jobs

    def _scrape_successfactors_browser(self, company):
        from .successfactors_browser import read_jobs
        rows = read_jobs(company)
        self.raw_count = len(rows)
        jobs = []
        for title, url in rows:
            if any(matches(title, term) for term in SENIOR):
                continue
            if not relevant(title) and not any(matches(title, term) for term in TECH):
                continue
            details = self._detail(company, url)
            job = self._job(company, title, url, company.get("location", ""), **details)
            if job:
                jobs.append(job)
        return jobs

    def _scrape_eightfold(self, company):
        jobs, seen, start = [], set(), 0
        for page in range(company.get("max_pages", 100)):
            params = {"domain": company["domain"], "location": company["search_location"], "start": start, "num": 10}
            data = self._get_request(company["api_url"] + "?" + urlencode(params)).json()
            rows, total = data.get("positions"), data.get("count")
            if not isinstance(rows, list) or type(total) is not int or total < 0:
                raise ValueError("Eightfold response schema changed")
            if normalize(data.get("location_used", "")) != normalize(company["search_location"]):
                raise ValueError("Eightfold location filter was not applied")
            if not rows and start < total:
                raise ValueError("Eightfold returned incomplete pagination")
            for row in rows:
                pid = row.get("id")
                if not pid or pid in seen:
                    raise ValueError("Eightfold repeated or missing position ID")
                seen.add(pid)
                self.raw_count += 1
                if row.get("isPrivate"):
                    continue
                title = row.get("name", "")
                location = "; ".join(row.get("locations") or [row.get("location", "")])
                if not any(matches(location, term) for term in TR_LOCATIONS):
                    continue
                if any(matches(title, term) for term in SENIOR):
                    continue
                if not relevant(title) and not any(matches(title, term) for term in TECH):
                    continue
                url = row.get("canonicalPositionUrl", "")
                if urlsplit(url).netloc != urlsplit(company["url"]).netloc or not urlsplit(url).path.startswith("/careers/job/"):
                    raise ValueError("Eightfold unexpected detail URL")
                details = self._detail(company, url)
                job = self._job(company, title, url, location, **details)
                if job:
                    jobs.append(job)
                self.random_sleep(0.3, 0.6)
            start += len(rows)
            if start >= total:
                return jobs
        raise ValueError("Eightfold page limit reached; coverage incomplete")

    def _scrape_amazon(self, company):
        from .amazon_browser import search_api
        jobs, seen, start = [], set(), 0
        with search_api(company["url"]) as fetch:
            for _ in range(100):
                data = fetch(start)
                rows, total = data.get("searchHits"), data.get("found")
                if not isinstance(rows, list) or type(total) is not int or total < 0 or data.get("start") != start:
                    raise ValueError("Amazon invalid list or page")
                if not rows and len(seen) < total:
                    raise ValueError("Amazon missing page")
                for hit in rows:
                    fields = hit.get("fields", {})
                    def value(key):
                        parts = fields.get(key, [])
                        if not isinstance(parts, list):
                            raise ValueError("Amazon unexpected field shape")
                        return " ".join(str(v) for v in parts)
                    key = value("icimsJobId")
                    if not re.fullmatch(r"(?:\d+|SF\d+)", key) or key in seen or "TR" not in fields.get("country", []):
                        raise ValueError("Amazon missing/repeated/foreign job")
                    seen.add(key)
                    self.raw_count += 1
                    if value("isConfidential") == "1" or value("isUnsearchable") == "1":
                        continue
                    title, description = value("title"), value("description")
                    if title == "[TITLE HERE]":
                        continue
                    if not key.isdigit():
                        raise ValueError("Amazon alternate job URL requires verification")
                    if not title or not description or "basicQualifications" not in fields:
                        raise ValueError("Amazon job detail incomplete")
                    description += " " + value("basicQualifications") + " " + value("preferredQualifications")
                    job = self._job(company, title, "https://amazon.jobs/en/jobs/" + key, value("city") + ", Türkiye", description)
                    if job:
                        jobs.append(job)
                start += len(rows)
                if len(seen) == total:
                    return jobs
                if len(seen) > total:
                    raise ValueError("Amazon count mismatch")
        raise ValueError("Amazon page limit reached")

    def _scrape_savunma(self, company):
        jobs, seen = [], set()
        for page in range(1, 101):
            response = requests.post(company["api_url"], json={"page": page, "size": 10, "sortDirection": "DESC", "companyId": company["company_id"]}, timeout=25)
            response.raise_for_status()
            payload = response.json()
            data = payload.get("data", {})
            rows, total = data.get("content"), data.get("totalElements")
            if payload.get("isSuccess") is not True or not isinstance(rows, list) or type(total) is not int or total < 0:
                raise ValueError("Savunma Kariyer incomplete listing")
            if not rows and len(seen) < total:
                raise ValueError("Savunma Kariyer missing page")
            for row in rows:
                key = row.get("id", "")
                if not re.fullmatch(r"[a-f0-9]{24}", key) or key in seen or row.get("companyId") != company["company_id"]:
                    raise ValueError("Savunma Kariyer repeated/foreign job")
                seen.add(key)
                self.raw_count += 1
                if row.get("deleted") or row.get("visible") is not True or row.get("applicable") is not True or row.get("jobStatus") != "PUBLISHED":
                    continue
                if row.get("jobType") in ("INTERNSHIP", "SCHOLARSHIP"):
                    continue
                if not row.get("jobDescription") or not row.get("endDate"):
                    raise ValueError("Savunma Kariyer description or deadline missing")
                start = datetime.fromisoformat(row["startDate"])
                if start > datetime.now(timezone.utc):
                    continue
                job = self._job(company, row["jobTitle"], "https://savunmakariyer.com/ilanlar/ilanDetay/" + key,
                                row.get("jobLocation", ""), row["jobDescription"], row["endDate"], row.get("startDate", ""))
                if job:
                    jobs.append(job)
            if len(seen) == total:
                return jobs
            if len(seen) > total:
                raise ValueError("Savunma Kariyer count mismatch")
        raise ValueError("Savunma Kariyer page limit reached")

    def _scrape_pcsx(self, company):
        jobs, seen, start = [], set(), 0
        base = company["api_url"].rstrip("/")
        def read(path, params):
            payload = self._get_request(base + path, params={"domain": company["domain"], **params}).json()
            if payload.get("status") != 200 or not isinstance(payload.get("data"), dict):
                raise ValueError("PCSX response incomplete")
            return payload["data"]
        for _ in range(100):
            data = read("/search", {"query": "", "location": "Turkey", "start": start})
            rows, total = data.get("positions"), data.get("count")
            if not isinstance(rows, list) or type(total) is not int or total < 0 or (not rows and start < total):
                raise ValueError("PCSX list or count missing")
            for row in rows:
                key = str(row.get("id", ""))
                if not key.isdigit() or key in seen:
                    raise ValueError("PCSX missing/repeated job ID")
                seen.add(key)
                self.raw_count += 1
                detail = read("/position_details", {"position_id": key, "hl": "en", "queried_location": "Turkey"})
                if str(detail.get("id")) != key or not detail.get("jobDescription"):
                    raise ValueError("PCSX detail mismatch")
                locations = detail.get("locations")
                if not isinstance(locations, list):
                    raise ValueError("PCSX locations missing")
                location = "; ".join(loc for loc in locations if any(matches(loc, token) for token in TR_LOCATIONS))
                if not location:
                    continue
                url = urljoin(company["url"], detail.get("publicUrl") or detail.get("positionUrl", ""))
                if urlsplit(url).netloc != urlsplit(company["url"]).netloc or not urlsplit(url).path.endswith("/" + key):
                    raise ValueError("PCSX unexpected detail URL")
                job = self._job(company, detail.get("name", ""), url, location, detail["jobDescription"])
                if job:
                    jobs.append(job)
            start += len(rows)
            if start == total:
                return jobs
            if start > total:
                raise ValueError("PCSX count mismatch")
        raise ValueError("PCSX page limit reached")

    def _scrape_hirebridge(self, company):
        response = self._get_request(company["url"])
        soup = BeautifulSoup(response.text, "html.parser")
        if not soup.title or company["expected_company"].casefold() not in soup.title.get_text().casefold():
            raise ValueError("Hirebridge company page mismatch")
        container = soup.select_one("#rightcol")
        if container is None or not container.select("ul.jobs"):
            raise ValueError("Hirebridge list missing; empty state unverified")
        if container.select(".pagination a, a[href*=PageIndex]"):
            raise ValueError("Hirebridge pagination requires review")
        jobs, seen = [], set()
        for group in container.select("ul.jobs"):
            heading = group.find_previous_sibling("span", class_="groupbyname-simple")
            if heading is None:
                raise ValueError("Hirebridge job location missing")
            location = heading.get_text(" ", strip=True)
            for link in group.select(".job a[href]"):
                url = urljoin(response.url, link["href"])
                query = dict(parse_qsl(urlsplit(url).query))
                if query.get("cid") != company["cid"] or not query.get("jid", "").isdigit() or urlsplit(url).netloc != urlsplit(company["url"]).netloc:
                    raise ValueError("Hirebridge job identity mismatch")
                if not any(matches(location, value) for value in TR_LOCATIONS):
                    continue
                if query["jid"] in seen:
                    continue
                seen.add(query["jid"])
                self.raw_count += 1
                title = link.get_text(" ", strip=True)
                detail = self._detail(company, url)
                job = self._job(company, title, url, location, **detail)
                if job:
                    jobs.append(job)
        return jobs

    def _scrape_flowq(self, company):
        jobs, seen, offset = [], set(), 0
        base = company["api_url"].rstrip("/")
        def post(path, body):
            response = requests.post(base + path, json=body, timeout=25)
            response.raise_for_status()
            data = response.json()
            if not isinstance(data, dict):
                raise ValueError("FlowQ response is not an object")
            return data
        for _ in range(100):
            data = post("/jobs", {"board": company["board"], "show_internal": None, "offset": offset,
                                  "h": None, "q": None, "template_ids": None, "cg": None, "ref": False})
            rows, total = data.get("jobs"), data.get("job_count")
            if not isinstance(rows, list) or type(total) is not int or total < 0 or data.get("company", {}).get("slug") != company["board"]:
                raise ValueError("FlowQ list or company mismatch")
            if not rows and len(seen) < total:
                raise ValueError("FlowQ missing pagination results")
            for row in rows:
                key = row.get("link", "")
                if not re.fullmatch(r"[A-Za-z0-9]+", key) or key in seen or row.get("company_slug") != company["board"]:
                    raise ValueError("FlowQ invalid, repeated or foreign job")
                seen.add(key)
                self.raw_count += 1
                detail = post("/job/detail?language=tr", {"link": key, "is_internal": False})
                if detail.get("link") != key or detail.get("company_slug") != company["board"]:
                    raise ValueError("FlowQ detail identity mismatch")
                if detail.get("application_enabled") is False or detail.get("only_internal_board") is True:
                    continue
                body = detail.get("job_template", {}).get("body")
                title = detail.get("job_template", {}).get("title") or detail.get("name")
                if not body or not title or detail.get("application_enabled") is not True:
                    raise ValueError("FlowQ incomplete job detail")
                job = self._job(company, title, "https://jobs.flowq.com/view/" + key, "Türkiye", body)
                if job:
                    jobs.append(job)
            offset += 1
            if len(seen) == total:
                return jobs
            if len(seen) > total:
                raise ValueError("FlowQ total count mismatch")
        raise ValueError("FlowQ pagination limit reached")

    def _scrape_oracle_cloud(self, company):
        """Oracle Recruiting Cloud aday deneyimi API'si; anonim GET, basvuru yok.

        Ulke suzmesi `location_facet` cografya kimligiyle yapilir. Sunucunun facet'i gercekten
        uyguladigi her yanitta dogrulanir; aksi halde tum dunya listesi Turkiye sanilirdi.
        """
        base = company["api_url"].rstrip("/") + "/hcmRestApi/resources/latest"
        site, facet = company["site_number"], str(company["location_facet"])
        jobs, seen, offset = [], set(), 0
        for _ in range(company.get("max_pages", 40)):
            finder = ("findReqs;siteNumber={},selectedLocationsFacet={},limit=25,offset={},"
                      "sortBy=POSTING_DATES_DESC").format(site, facet, offset)
            payload = self._get_request(base + "/recruitingCEJobRequisitions",
                                        params={"onlyData": "true", "finder": finder,
                                                "expand": "requisitionList.secondaryLocations"}).json()
            items = payload.get("items")
            if not isinstance(items, list) or not items:
                raise ValueError("Oracle Cloud response has no items")
            data = items[0]
            if str(data.get("SelectedLocationsFacet") or "") != facet:
                raise ValueError("Oracle Cloud location facet was not applied")
            rows, total = data.get("requisitionList"), data.get("TotalJobsCount")
            if not isinstance(rows, list) or type(total) is not int or total < 0:
                raise ValueError("Oracle Cloud list or count missing")
            if total == 0:
                return jobs
            if not rows and offset < total:
                raise ValueError("Oracle Cloud pagination ended early")
            for row in rows:
                key = str(row.get("Id", ""))
                if not key or key in seen:
                    raise ValueError("Oracle Cloud missing or repeated requisition ID")
                seen.add(key)
                self.raw_count += 1
                title = row.get("Title", "")
                if any(matches(title, term) for term in SENIOR):
                    continue
                if not relevant(title) and not any(matches(title, term) for term in TECH):
                    continue
                detail = self._get_request(base + "/recruitingCEJobRequisitionDetails",
                                           params={"onlyData": "true", "expand": "all",
                                                   "finder": 'ById;Id="{}",siteNumber={}'.format(key, site)}).json()
                found = detail.get("items") or []
                if not found or str(found[0].get("Id")) != key:
                    raise ValueError("Oracle Cloud detail identity mismatch")
                info = found[0]
                description = " ".join(str(info.get(field) or "") for field in
                                       ("ExternalDescriptionStr", "ExternalQualificationsStr",
                                        "ExternalResponsibilitiesStr", "ShortDescriptionStr"))
                if not description.strip():
                    raise ValueError("Oracle Cloud job description missing")
                url = urljoin(company["url"], "/en/sites/{}/job/{}".format(company.get("site_path", site), key))
                job = self._job(company, title, url,
                                info.get("PrimaryLocation") or row.get("PrimaryLocation", ""),
                                description, info.get("ExternalPostedEndDate", ""),
                                info.get("ExternalPostedStartDate", ""))
                if job:
                    jobs.append(job)
                self.random_sleep(0.3, 0.6)
            offset += len(rows)
            if offset >= total:
                return jobs
        raise ValueError("Oracle Cloud page limit reached")

    def _scrape_successfactors_csb(self, company):
        """SAP SuccessFactors Career Site Builder arama sayfasi; anonim GET, basvuru yok."""
        base = company["url"].rstrip("/")
        host = urlsplit(company["url"]).netloc
        jobs, seen, startrow = [], set(), 0
        for _ in range(company.get("max_pages", 40)):
            # search_params global panolarda ulke facet'ini uygular; yer filtresi ayrica _job icinde calisir.
            response = self._get_request(base + "/search/",
                                         params={"q": "", "startrow": startrow, **company.get("search_params", {})})
            if urlsplit(response.url).netloc != host:
                raise ValueError("SuccessFactors CSB left the configured career host")
            soup = BeautifulSoup(response.text, "html.parser")
            rows = soup.select("tr.data-row")
            label = soup.select_one(".paginationLabel")
            table = soup.select_one("table.searchResults")
            if label is None and table is None:
                # Kart yerlesimli site: sunucudan yalniz ilk grup gelir, sayfalama desteklenmez.
                return self._successfactors_csb_tiles(company, response, soup, host)
            if label is None:
                # Sonuc etiketi olmayan tablo: arama tablosu dururken bos donen sayfa listenin sonudur.
                if not rows:
                    return jobs
                total = None
            else:
                numbers = [int(re.sub(r"[.,]", "", value)) for value in re.findall(r"[\d.,]+", label.get_text(" ", strip=True))]
                if len(numbers) != 3 or numbers[0] != startrow + 1 or numbers[1] < numbers[0] or numbers[2] < numbers[1]:
                    raise ValueError("SuccessFactors CSB result label unreadable: " + label.get_text(" ", strip=True))
                first, last, total = numbers
                if len(rows) != last - first + 1:
                    raise ValueError("SuccessFactors CSB row count does not match the result label")
            for row in rows:
                link = row.select_one("a.jobTitle-link[href]")
                if link is None:
                    raise ValueError("SuccessFactors CSB job link missing")
                url = urljoin(response.url, link["href"])
                key = re.search(r"/job/[^/]+/(\d+)/", urlsplit(url).path)
                if key is None or key.group(1) in seen:
                    raise ValueError("SuccessFactors CSB missing or repeated job ID")
                seen.add(key.group(1))
                self.raw_count += 1
                title = link.get_text(" ", strip=True)
                location = row.select_one(".jobLocation")
                job = self._read_csb_job(company, title, url,
                                         location.get_text(" ", strip=True) if location else "")
                if job:
                    jobs.append(job)
            startrow += len(rows)
            if total is not None and startrow >= total:
                return jobs
        raise ValueError("SuccessFactors CSB page limit reached")

    def _successfactors_csb_tiles(self, company, response, soup, host):
        text = soup.get_text(" ", strip=True)
        counters = [r"Showing\s+[\d.,]+\s+to\s+[\d.,]+\s+of\s+([\d.,]+)\s+Jobs?",
                    r"Showing\s+([\d.,]+)\s+Jobs?",
                    r"([\d.,]+)\s*İşten\s*[\d.,]+\s*[-–]\s*[\d.,]+\s*aras[ıi]ndakiler",
                    r"toplam\s*([\d.,]+)\s*İş\s*Gösteriliyor",
                    r"([\d.,]+)\s*İş\s*Gösteriliyor"]
        shown = next((m for m in (re.search(p, text, re.I) for p in counters) if m), None)
        if shown is None:
            raise ValueError("SuccessFactors CSB result count missing; layout or empty state must be checked")
        total = int(re.sub(r"[.,]", "", shown.group(1)))
        found = {}
        for link in soup.select('a[href*="/job/"]'):
            url = urljoin(response.url, link["href"])
            key = re.search(r"/job/[^/]+/(\d+)/", urlsplit(url).path)
            if key is None or urlsplit(url).netloc != host:
                continue
            found.setdefault(key.group(1), (link.get_text(" ", strip=True), url))
        if len(found) != total:
            raise ValueError("SuccessFactors CSB tile listing is incomplete; pagination needs support")
        jobs = []
        for title, url in found.values():
            self.raw_count += 1
            job = self._read_csb_job(company, title, url, "")
            if job:
                jobs.append(job)
        return jobs

    def _read_csb_job(self, company, title, url, location):
        if any(matches(title, term) for term in SENIOR):
            return None
        if not relevant(title) and not any(matches(title, term) for term in TECH):
            return None
        details = self._detail(company, url)
        self.random_sleep(0.3, 0.6)
        return self._job(company, title, url, location or company.get("location", ""), **details)

    def _scrape_hrpeak_browser(self, company):
        from .hrpeak_browser import read_jobs
        rows = read_jobs(company["url"], company["expected_company"])
        self.raw_count = len(rows)
        return [job for row in rows if (job := self._job(company, **row))]

    def _scrape_generic(self, company):
        url, visited, candidates, jobs = company["url"], set(), set(), []
        for page in range(company.get("max_pages", 20)):
            if url in visited:
                raise ValueError("Pagination loop detected")
            visited.add(url)
            response = self._get_request(url)
            soup = BeautifulSoup(response.text, "html.parser")
            base_url = company.get("link_base_url", response.url)
            cards = soup.select(company["selector"])
            empty = soup.select_one(company["empty_selector"]) if company.get("empty_selector") else None
            confirmed_empty = bool(empty and company.get("empty_text") and company["empty_text"] in empty.get_text(" ", strip=True))
            if not cards and not confirmed_empty:
                raise ValueError("Job selector did not match; empty or changed/JS-only page")
            for card in cards:
                if company.get("company_selector"):
                    brand = card.select_one(company["company_selector"])
                    expected = company.get("expected_company", company["name"])
                    if brand is None or normalize(brand.get_text(" ", strip=True)) != normalize(expected):
                        raise ValueError("Company filter mismatch; source coverage must be checked")
                link = card if card.name == "a" else card.select_one(company.get("link_selector", "a[href]"))
                if link is None:
                    continue
                job_url = urljoin(base_url, link.get("href", ""))
                if urlsplit(job_url).scheme not in ("http", "https"):
                    continue
                if company.get("job_url_pattern") and not re.search(company["job_url_pattern"], job_url):
                    continue
                if canonical(job_url) in candidates:
                    continue
                candidates.add(canonical(job_url))
                self.raw_count += 1
                el = card.select_one(company["title_selector"]) if company.get("title_selector") else link
                title = el.get_text(" ", strip=True) if el else ""
                loc = card.select_one(company["location_selector"]) if company.get("location_selector") else None
                location = loc.get_text(" ", strip=True) if loc else company.get("location", "")
                details = {}
                # Read ambiguous technology titles too: new-grad conditions may be in the description.
                if company.get("fetch_details") and not any(matches(title, k) for k in SENIOR) and (relevant(title) or any(matches(title, k) for k in TECH)):
                    host = urlsplit(job_url).netloc
                    allowed = {urlsplit(company["url"]).netloc, *company.get("detail_hosts", [])}
                    if host not in allowed:
                        raise ValueError("Unconfigured job detail host: " + host)
                    details = self._detail(company, job_url)
                    self.random_sleep(0.3, 0.6)
                employer = company
                if company.get("job_company_selector"):
                    brand = card.select_one(company["job_company_selector"])
                    if brand is None or not brand.get_text(" ", strip=True):
                        raise ValueError("Job employer missing")
                    employer = {**company, "name": brand.get_text(" ", strip=True)}
                job = self._job(employer, title, job_url, location, **details)
                if job:
                    jobs.append(job)
            if not candidates and not confirmed_empty:
                raise ValueError("No job links matched; source layout must be checked")
            next_link = soup.select_one(company["next_selector"]) if company.get("next_selector") else None
            if next_link is None or not next_link.get("href"):
                return jobs
            url = urljoin(response.url, next_link["href"])
            if urlsplit(url).netloc != urlsplit(company["url"]).netloc:
                raise ValueError("Pagination left configured source host")
        raise ValueError("Page limit reached; coverage incomplete")
