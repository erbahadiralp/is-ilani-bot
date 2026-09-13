"""Source parsing regression tests. Synthetic public-page shapes; no network."""
import os
os.environ["LOG_PATH"] = os.devnull
import json
import logging
import unittest
from unittest.mock import Mock, patch
from datetime import datetime
from zoneinfo import ZoneInfo
import requests
from scrapers.company_scraper import CompanyScraper, canonical, expired


def response(url, data):
    r = requests.Response()
    r.status_code = 200
    r.url = url
    r.encoding = "utf-8"
    r._content = (json.dumps(data) if isinstance(data, (list,dict)) else data).encode("utf-8")
    return r


class CompanySourcesTests(unittest.TestCase):
    def setUp(self):
        self.scraper = CompanyScraper.__new__(CompanyScraper)
        self.scraper.raw_count = 0
        self.scraper.logger = logging.getLogger("test.company")
        self.scraper.random_sleep = Mock()
        self.scraper._detail_cache = {}
        self.company = {"name":"Test", "country_scope":"TR", "url":"https://example.com/jobs",
                        "selector":"a.job", "type":"generic"}

    def test_amazon_reads_all_pages_and_required_experience(self):
        from contextlib import contextmanager
        def row(key, experience):
            return {"fields": {"icimsJobId": [key], "country": ["TR"], "city": ["Istanbul"], "title": ["Junior Java Developer"], "description": ["Java backend"], "basicQualifications": [experience]}}
        pages = [{"start": 0, "found": 3, "searchHits": [row("1", "0-2 years experience")]}, {"start": 1, "found": 3, "searchHits": [row("2", "minimum 5 years experience"), {"fields": {"icimsJobId": ["SF250119781"], "country": ["TR"], "title": ["[TITLE HERE]"]}}]}]
        fetch = Mock(side_effect=pages)
        @contextmanager
        def api(url):
            yield fetch
        c = {**self.company, "type": "amazon"}
        with patch("scrapers.amazon_browser.search_api", api):
            jobs = self.scraper.scrape_company(c)
        self.assertEqual(len(jobs), 1)
        self.assertEqual(self.scraper.raw_count, 3)
        self.assertEqual(fetch.call_args_list[1].args, (1,))

    def test_generic_group_employer_and_relative_base_url(self):
        c = {**self.company, "job_company_selector": ".brand", "selector": "article", "title_selector": "h3", "location_selector": ".location", "link_base_url": "https://example.com/careers/"}
        html = '<article><h3>Junior Java Developer</h3><span class="brand">Ford Otosan</span><span class="location">Istanbul</span><a href="jobs/123">Details</a></article>'
        with patch.object(self.scraper, "_get_request", return_value=response(c["url"], html)):
            jobs = self.scraper.scrape_company(c)
        self.assertEqual(jobs[0]["company"], "Ford Otosan")
        self.assertEqual(jobs[0]["url"], "https://example.com/careers/jobs/123")

    def test_pcsx_details_and_country_filter(self):
        c = {**self.company, "type": "pcsx", "api_url": "https://example.com/api", "domain": "test"}
        listing = {"status": 200, "data": {"count": 1, "positions": [{"id": 123}]}}
        detail = {"status": 200, "data": {"id": 123, "name": "Junior Python Developer", "locations": ["London", "Istanbul, Türkiye"], "jobDescription": "Python backend development", "positionUrl": "/careers/job/123"}}
        with patch.object(self.scraper, "_get_request", side_effect=[response(c["url"], d) for d in [listing, detail]]):
            jobs = self.scraper.scrape_company(c)
        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0]["location"], "Istanbul, Türkiye")
        with patch.object(self.scraper, "_get_request", return_value=response(c["url"], {"status": 200, "data": {"count": 1, "positions": []}})), self.assertRaises(ValueError):
            self.scraper.scrape_company(c)

    def test_savunma_excludes_student_and_closed_jobs(self):
        c = {**self.company, "type": "savunma", "api_url": "https://example.com/api", "company_id": "test"}
        row = {"id": "a"*24, "companyId": "test", "jobTitle": "Junior Software Engineer", "jobDescription": "Java backend software development", "jobLocation": "Ankara", "visible": True, "applicable": True, "jobStatus": "PUBLISHED", "startDate": "2020-01-01T00:00:00+03:00", "endDate": "2099-01-01T00:00:00+03:00"}
        rows = [row, {**row, "id": "b"*24, "jobType": "INTERNSHIP"}, {**row, "id": "c"*24, "applicable": False}]
        with patch("scrapers.company_scraper.requests.post", return_value=response(c["url"], {"isSuccess": True, "data": {"content": rows, "totalElements": 3}})):
            jobs = self.scraper.scrape_company(c)
        self.assertEqual(len(jobs), 1)
        self.assertEqual(self.scraper.raw_count, 3)
        with patch("scrapers.company_scraper.requests.post", return_value=response(c["url"], {"isSuccess": True, "data": {"content": [{**row, "companyId": "foreign"}], "totalElements": 1}})), self.assertRaises(ValueError):
            self.scraper.scrape_company(c)

    def test_hirebridge_scopes_locations_and_rejects_foreign_company(self):
        c = {**self.company, "type": "hirebridge", "expected_company": "Sovos", "cid": "6875"}
        def card(jid, cid="6875"):
            return '<ul class="jobs"><li><span class="job"><a href="/JobDetails.aspx?cid='+cid+'&jid='+jid+'">Junior Java Developer</a></span></li></ul>'
        html = '<title>Sovos Career Center</title><div id="rightcol"><span class="groupbyname-simple">London, UK</span>'+card("1")+'<span class="groupbyname-simple">Istanbul, Turkey</span>'+card("2")+'</div>'
        with patch.object(self.scraper, "_get_request", return_value=response(c["url"], html)), patch.object(self.scraper, "_detail", return_value={"description": "Java backend role"}) as detail:
            found = self.scraper.scrape_company(c)
        self.assertEqual(len(found), 1)
        self.assertEqual(self.scraper.raw_count, 1)
        self.assertEqual(detail.call_count, 1)
        self.assertIn("jid=2", found[0]["url"])
        for bad in [html.replace("cid=6875", "cid=9999"), '<title>Sovos Career Center</title><div id="rightcol"></div>']:
            with patch.object(self.scraper, "_get_request", return_value=response(c["url"], bad)), self.assertRaises(ValueError):
                self.scraper.scrape_company(c)

    def test_flowq_pagination_details_and_foreign_company(self):
        c = {**self.company, "type": "flowq", "board": "test", "api_url": "https://example.com/api"}
        page1 = {"job_count": 3, "company": {"slug": "test"}, "jobs": [{"link": "AA1", "company_slug": "test"}, {"link": "AA3", "company_slug": "test"}]}
        page2 = {**page1, "jobs": [{"link": "AA2", "company_slug": "test"}]}
        detail = {"link": "AA1", "company_slug": "test", "application_enabled": True,
                  "job_template": {"title": "Java Developer", "body": "Yeni mezun adaylar başvurabilir."}}
        with patch("scrapers.company_scraper.requests.post", side_effect=[response(c["url"], x) for x in [page1, detail, {**detail, "link": "AA3"}, page2, {**detail, "link": "AA2", "application_enabled": False}]] ) as post:
            jobs = self.scraper.scrape_company(c)
        self.assertEqual(len(jobs), 2)
        self.assertEqual(self.scraper.raw_count, 3)
        self.assertEqual(post.call_args_list[3].kwargs["json"]["offset"], 1)
        for bad in [{**page1, "company": {"slug": "other"}}, {**page1, "jobs": []}]:
            with patch("scrapers.company_scraper.requests.post", return_value=response(c["url"], bad)), self.assertRaises(ValueError):
                self.scraper.scrape_company(c)

    def test_oracle_cloud_requires_applied_location_facet(self):
        c = {**self.company, "type": "oracle_cloud", "url": "https://careers.example.com",
             "api_url": "https://tenant.example.com", "site_number": "CX_1", "location_facet": "3000001"}
        def listing(rows, total, facet="3000001"):
            return {"items": [{"SelectedLocationsFacet": facet, "TotalJobsCount": total, "requisitionList": rows}]}
        def detail(key):
            return {"items": [{"Id": key, "Title": "Junior Java Developer", "PrimaryLocation": "İstanbul, Türkiye",
                               "ExternalDescriptionStr": "Yeni mezun Java geliştirici aranıyor"}]}
        pages = [listing([{"Id": "11", "Title": "Junior Java Developer"}], 2), detail("11"),
                 listing([{"Id": "12", "Title": "Junior Python Developer"}], 2), detail("12")]
        with patch.object(self.scraper, "_get_request", side_effect=[response(c["url"], p) for p in pages]) as get:
            jobs = self.scraper.scrape_company(c)
        self.assertEqual(len(jobs), 2)
        self.assertEqual(jobs[0]["url"], "https://careers.example.com/en/sites/CX_1/job/11")
        self.assertIn("selectedLocationsFacet=3000001", get.call_args_list[0].kwargs["params"]["finder"])
        # Sunucu facet'i uygulamazsa butun dunya listesi Turkiye sanilmamali.
        self.scraper.raw_count = 0
        with patch.object(self.scraper, "_get_request",
                          return_value=response(c["url"], listing([{"Id": "9", "Title": "Junior Java Developer"}], 500, facet=""))), \
             self.assertRaises(ValueError):
            self.scraper.scrape_company(c)
        # Gercek sifir sonuc hata degildir.
        self.scraper.raw_count = 0
        with patch.object(self.scraper, "_get_request", return_value=response(c["url"], listing([], 0))):
            self.assertEqual(self.scraper.scrape_company(c), [])

    def test_successfactors_csb_paginates_table_layout_and_rejects_broken_totals(self):
        c = {**self.company, "type": "successfactors_csb", "url": "https://careers.example.com"}
        def page(first, last, total, ids):
            rows = "".join('<tr class="data-row"><td><a class="jobTitle-link" href="/job/Istanbul-Junior-Java-Developer/'+i+'/">Junior Java Developer</a></td>'
                           '<td><span class="jobLocation">İstanbul, TR</span></td></tr>' for i in ids)
            return '<span class="paginationLabel">Sonuçlar '+str(first)+' – '+str(last)+' - '+str(total)+'</span><table>'+rows+'</table>'
        pages = [page(1, 2, 3, ["11", "12"]), page(3, 3, 3, ["13"])]
        with patch.object(self.scraper, "_get_request", side_effect=[response(c["url"], p) for p in pages]) as get, \
             patch.object(self.scraper, "_detail", return_value={"description": "Yeni mezun Java geliştirici"}):
            jobs = self.scraper.scrape_company(c)
        self.assertEqual(len(jobs), 3)
        self.assertEqual(self.scraper.raw_count, 3)
        self.assertEqual(get.call_args_list[1].kwargs["params"]["startrow"], 2)
        self.assertEqual(jobs[0]["url"], "https://careers.example.com/job/Istanbul-Junior-Java-Developer/11/")
        # Tekrarlanan kimlik, eksik satir ve okunamayan toplam sessiz eksik liste uretmemeli.
        for bad in [page(1, 2, 3, ["11", "11"]), page(1, 5, 9, ["11", "12"]), page(1, 2, 3, ["11", "12"]).replace("Sonuçlar 1 – 2 - 3", "Sonuçlar")]:
            self.scraper.raw_count = 0
            with patch.object(self.scraper, "_get_request", return_value=response(c["url"], bad)), \
                 patch.object(self.scraper, "_detail", return_value={"description": "Java"}), self.assertRaises(ValueError):
                self.scraper.scrape_company(c)

    def test_successfactors_csb_unlabeled_table_pages_until_empty_search_table(self):
        c = {**self.company, "type": "successfactors_csb", "url": "https://careers.example.com"}
        def page(ids):
            rows = "".join('<tr class="data-row"><td><a class="jobTitle-link" href="/job/Istanbul-Junior-Java-Developer/'+i+'/">Junior Java Developer</a></td>'
                           '<td><span class="jobLocation">İstanbul, TR</span></td></tr>' for i in ids)
            return '<table class="searchResults">' + rows + '</table>'
        pages = [page(["21", "22"]), page([])]
        with patch.object(self.scraper, "_get_request", side_effect=[response(c["url"], p) for p in pages]) as get, \
             patch.object(self.scraper, "_detail", return_value={"description": "Yeni mezun Java geliştirici"}):
            jobs = self.scraper.scrape_company(c)
        self.assertEqual(len(jobs), 2)
        self.assertEqual(get.call_args_list[1].kwargs["params"]["startrow"], 2)
        # Arama tablosu da sayim ifadesi de yoksa kaynak sessizce sifir donmemeli.
        with patch.object(self.scraper, "_get_request", return_value=response(c["url"], "<div>Bakım çalışması</div>")), \
             self.assertRaises(ValueError):
            self.scraper.scrape_company(c)

    def test_successfactors_csb_tile_layout_requires_complete_listing(self):
        c = {**self.company, "type": "successfactors_csb", "url": "https://careers.example.com", "local_only": True}
        link = '<a href="/job/Istanbul-Junior-Python-Developer/77/">Junior Python Developer</a>'
        with patch.object(self.scraper, "_get_request", return_value=response(c["url"], "<div>Showing 1 to 1 of 1 Jobs</div>" + link)), \
             patch.object(self.scraper, "_detail", return_value={"description": "Yeni mezun Python geliştirici"}):
            jobs = self.scraper.scrape_company(c)
        self.assertEqual([j["url"] for j in jobs], ["https://careers.example.com/job/Istanbul-Junior-Python-Developer/77/"])
        for bad in ["<div>1 İş Gösteriliyor</div>", "<div>Showing 1 to 25 of 40 Jobs</div>" + link, "<div>Kariyer Fırsatları</div>" + link]:
            self.scraper.raw_count = 0
            with patch.object(self.scraper, "_get_request", return_value=response(c["url"], bad)), \
                 patch.object(self.scraper, "_detail", return_value={"description": "Python"}), self.assertRaises(ValueError):
                self.scraper.scrape_company(c)

    def test_hrpeak_empty_requires_company_and_explicit_message(self):
        from scrapers.hrpeak_browser import parse_list
        html = '<span class="page-menu-title">Test Bankası İş İlanları</span><table id="C_G"><tr><td class="no-record">Yayınlanmış bir açık pozisyon bulunamadı.</td></tr></table>'
        self.assertEqual(parse_list(html, self.company["url"], "Test Bankası"), [])
        for bad in [html.replace("Test Bankası", "Other"), html.replace("Yayınlanmış bir açık pozisyon bulunamadı.", ""), "Access Denied"]:
            with self.assertRaises(ValueError):
                parse_list(bad, self.company["url"], "Test Bankası")

    def test_hrpeak_second_theme_uses_its_own_heading_and_empty_state(self):
        from scrapers.hrpeak_browser import parse_list
        html = ('<div class="menuSayfa">Türk Telekom Kariyer İş İlanları</div><table id="C_G">'
                '<tr><td><table class="kayitBulunamadi"><tr><td>Yayınlanmış bir açık pozisyon bulunamadı.'
                '<a class="PL" href="/uyelik/bireysel/">Özgeçmiş bırakmak için tıklayınız.</a></td></tr></table></td></tr></table>')
        self.assertEqual(parse_list(html, "https://example.com/ilan/site.aspx", "Türk Telekom"), [])
        for bad in [html.replace("Türk Telekom Kariyer", "Başka Şirket"),
                    html.replace("Yayınlanmış bir açık pozisyon bulunamadı.", "")]:
            with self.assertRaises(ValueError):
                parse_list(bad, "https://example.com/ilan/site.aspx", "Türk Telekom")

    def test_hrpeak_jobs_validate_links_details_and_incomplete_pagination(self):
        from scrapers.hrpeak_browser import parse_list, parse_detail
        html = '<span class="page-menu-title">Test İş İlanları</span><table id="C_G"><tr class="GR"><td><a class="PL" href="/abc.job">Junior Java Developer</a><span class="location">İstanbul</span></td></tr></table>'
        rows = parse_list(html, self.company["url"], "Test")
        self.assertEqual(rows[0]["url"], "https://example.com/abc.job")
        detail = '<div class="ilan"><h3>Junior Java Developer</h3><div class="ilanMetni">Yeni mezun bilgisayar mühendisleri Java Spring Boot ekibimize başvurabilir.</div></div>'
        description = parse_detail(detail, rows[0]["title"])
        self.assertTrue(self.scraper._job(self.company, **rows[0], description=description))
        with self.assertRaises(ValueError):
            parse_detail(detail.replace("Junior Java Developer", "Login"), rows[0]["title"])
        for bad in [html.replace('/abc.job', 'https://other.test/abc.job'), html.replace('</table>', '<tr class="GP"><td><a href="?Page=2">2</a></td></tr></table>')]:
            with self.assertRaises(ValueError):
                parse_list(bad, self.company["url"], "Test")

    def test_embedded_program_tracks_details_and_status_without_react_ids(self):
        from scrapers.program_scraper import embedded_program_content
        record = {"title": "Data MT", "content": "New graduates can apply", "isActiveJobAdvert": False}
        def page(data, suffix="render-id"):
            return "Components.ExperienceProgramsLink," + json.dumps(data) + suffix
        parse = lambda html: embedded_program_content(html, "ExperienceProgramsLink", ["Data MT"])
        baseline = parse(page(record))
        self.assertEqual(baseline, parse(page(record, "another-render-id")))
        self.assertNotEqual(baseline, parse(page({**record, "content": "Applications close tomorrow"})))
        self.assertNotEqual(baseline, parse(page({**record, "isActiveJobAdvert": True})))
        with self.assertRaises(ValueError):
            parse("challenge page")

    def test_eightfold_paginates_checks_country_and_reads_experience(self):
        c = {**self.company, "type": "eightfold", "api_url": "https://example.com/api", "domain": "test", "search_location": "Turkey"}
        first = {"positions": [{"id": 1, "name": "Java Developer", "locations": ["Istanbul, Turkey"], "canonicalPositionUrl": "https://example.com/careers/job/1"}], "count": 2, "location_used": "Turkey"}
        second = {"positions": [{"id": 2, "name": "Junior Java Developer", "locations": ["Berlin, Germany"]}], "count": 2, "location_used": "Turkey"}
        self.scraper._get_request = Mock(side_effect=[response(c["url"], first), response(c["url"], second)])
        self.scraper._detail = Mock(return_value={"description": "New graduates are welcome"})
        self.assertEqual(len(self.scraper.scrape_company(c)), 1)
        self.assertIn("start=1", self.scraper._get_request.call_args.args[0])
        self.scraper._detail.assert_called_once()
        self.scraper._get_request = Mock(side_effect=[response(c["url"], first), response(c["url"], first)])
        with self.assertRaisesRegex(ValueError, "repeated"):
            self.scraper.scrape_company(c)

    def test_eightfold_empty_requires_valid_filter_and_count(self):
        c = {**self.company, "type": "eightfold", "api_url": "https://example.com/api", "domain": "test", "search_location": "Turkey"}
        empty = {"positions": [], "count": 0, "location_used": "Turkey"}
        self.scraper._get_request = Mock(return_value=response(c["url"], empty))
        self.assertEqual(self.scraper.scrape_company(c), [])
        for bad in [{}, {**empty, "count": 1}, {**empty, "location_used": ""}]:
            self.scraper._get_request.return_value = response(c["url"], bad)
            with self.assertRaises(ValueError):
                self.scraper.scrape_company(c)

    def test_isbank_tls_keeps_root_and_hostname_verification(self):
        import ssl
        from scrapers.verified_tls import isbank_context
        context = isbank_context()
        self.assertEqual(context.verify_mode, ssl.CERT_REQUIRED)
        self.assertTrue(context.check_hostname)
        self.assertFalse(context.verify_flags & ssl.VERIFY_X509_PARTIAL_CHAIN)

    def test_successfactors_browser_parser_validates_count_tenant_and_stable_url(self):
        from scrapers.successfactors_browser import parse_page
        html = '<h2>Aramanızla 1 iş eşleşti</h2><a class="jobTitle" href="/career?company=softtechya&amp;career_job_req_id=123&amp;_s.crb=temporary">Junior Java Developer</a>'
        rows, total = parse_page(html, "https://career2.successfactors.eu/career", "softtechya")
        self.assertEqual(total, 1)
        self.assertNotIn("_s.crb", rows[0][1])
        for bad in [html.replace("company=softtechya", "company=other"), '<h2>Aramanızla 1 iş eşleşti</h2>', '<h2>Access denied</h2>']:
            with self.assertRaises(ValueError):
                parse_page(bad, "https://career2.successfactors.eu/career", "softtechya")
        self.assertEqual(parse_page('<h2>Aramanızla 0 iş eşleşti</h2>', "https://example.com", "softtechya"), ([], 0))

    def test_program_detects_application_url_change_with_click_here_label(self):
        from scrapers.program_scraper import ProgramScraper
        program = {"company": "Test", "name": "Career", "url": "https://example.com", "selector": "section", "expected_text": "Career", "link_selector": ".apply a[href]"}
        html = '<section>Career ' + 'program details ' * 12 + '<p class="apply"><a href="/old">Click here</a></p></section>'
        reader = ProgramScraper()
        fingerprints = []
        with patch("scrapers.program_scraper.read_radar", return_value=([{"name": "Test"}], [])), patch("scrapers.program_scraper.Path.read_text", return_value=json.dumps([program])), patch.object(reader, "random_sleep"), patch("scrapers.program_scraper.database.program_event", side_effect=lambda url, fp, job: fingerprints.append(fp)), patch("scrapers.program_scraper.requests.get", side_effect=[response(program["url"], html), response(program["url"], html.replace('/old', '/new'))]):
            reader.scrape()
            reader.scrape()
        self.assertEqual(len(fingerprints), 2)
        self.assertNotEqual(*fingerprints)

    def test_generic_rejects_broken_company_filter(self):
        c = {**self.company, "selector": "article", "company_selector": ".brand", "local_only": True}
        html = '<article><p class="brand">Test</p><a href="/1">Junior Java Developer</a></article>'
        self.scraper._get_request = Mock(return_value=response(c["url"], html))
        self.assertEqual(len(self.scraper.scrape_company(c)), 1)
        for bad in [html.replace("Test", "Other"), html.replace('class="brand"', 'class="missing"')]:
            self.scraper._get_request.return_value = response(c["url"], bad)
            with self.assertRaisesRegex(ValueError, "Company filter mismatch"):
                self.scraper.scrape_company(c)

    def test_albarakatech_reads_official_description_without_requesting_application_site(self):
        c = {**self.company, "type": "albarakatech"}
        html = '<button id="tab-0">Java Developer</button><div class="tab-pane" aria-labelledby="tab-0">New graduates are welcome<a class="apply-btn" href="https://www.kariyer.net/is-ilani/example-123   ">Apply</a></div>'
        self.scraper._get_request = Mock(return_value=response(c["url"], html))
        jobs = self.scraper.scrape_company(c)
        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0]["url"], "https://www.kariyer.net/is-ilani/example-123")
        self.scraper._get_request.assert_called_once_with(c["url"])
        self.scraper._get_request.return_value = response(c["url"], html.replace("New graduates are welcome", "Minimum 5 years experience"))
        self.assertEqual(self.scraper.scrape_company(c), [])

    def test_global_ats_excludes_foreign_new_grad_jobs(self):
        self.assertIsNone(self.scraper._job(self.company, "Junior Java Developer", "https://example.com/1", "Berlin"))
        self.assertIsNotNone(self.scraper._job(self.company, "Junior Java Developer", "https://example.com/1", "Istanbul"))
        self.assertIsNone(self.scraper._job(self.company, "Junior Java Developer", "https://example.com/1", "Remote"))

    def test_lever_reads_experience_requirements_from_lists(self):
        c = {**self.company, "type":"lever", "api_url":"https://api.lever.co/v0/postings/test?mode=json"}
        data = [{"text":"Java Developer", "hostedUrl":"https://example.com/1", "categories":{"location":"Istanbul"},
                 "lists":[{"content":"New graduates are welcome"}]}]
        self.scraper._get_request = Mock(return_value=response(c["api_url"], data))
        self.assertEqual(len(self.scraper.scrape_company(c)),1)
        data[0]["lists"] = [{"content":"Minimum 3 years experience"}]
        self.scraper._get_request.return_value = response(c["api_url"],data)
        self.assertEqual(self.scraper.scrape_company(c),[])

    def test_greenhouse_requests_description(self):
        c = {**self.company, "type":"greenhouse", "api_url":"https://boards-api.greenhouse.io/v1/boards/test/jobs"}
        self.scraper._get_request = Mock(return_value=response(c["api_url"], {"jobs":[]}))
        self.assertEqual(self.scraper.scrape_company(c),[])
        self.assertIn("content=true",self.scraper._get_request.call_args.args[0])

    def test_ashby_ignores_unlisted_and_accepts_secondary_turkey(self):
        c = {**self.company, "type":"ashby", "api_url":"https://api.ashbyhq.com/posting-api/job-board/test"}
        job = {"title":"Junior Data Engineer", "location":"London", "secondaryLocations":[{"location":"Istanbul"}],
               "jobUrl":"https://jobs.ashbyhq.com/test/1", "isListed":True}
        self.scraper._get_request = Mock(return_value=response(c["api_url"], {"jobs":[job,{**job,"isListed":False}]}))
        self.assertEqual(len(self.scraper.scrape_company(c)),1)

    def test_html_pagination_and_absolute_relative_duplicate_links(self):
        c = {**self.company, "next_selector":"a.next", "location":"Türkiye"}
        self.scraper._get_request = Mock(side_effect=[
            response(c["url"], '<a class="job" href="/role/1">Junior Java Developer</a><a class="job" href="https://example.com/role/1">Junior Java Developer</a><a class="next" href="?page=2">Next</a>'),
            response(c["url"]+'?page=2','<a class="job" href="/role/2">Junior Data Engineer</a>')])
        self.assertEqual(len(self.scraper.scrape_company(c)),2)
        self.assertEqual(self.scraper.raw_count,2)

    def test_missing_selector_is_error_not_successful_empty_feed(self):
        self.scraper._get_request = Mock(return_value=response(self.company["url"],'<h1>Login</h1>'))
        with self.assertRaises(ValueError):
            self.scraper.scrape_company(self.company)

    def test_explicit_empty_state(self):
        c = {**self.company,"empty_selector":"h2", "empty_text":"There are no open positions"}
        self.scraper._get_request = Mock(return_value=response(c["url"],'<h2>There are no open positions</h2>'))
        self.assertEqual(self.scraper.scrape_company(c),[])
        self.scraper._get_request.return_value=response(c["url"],'<h2>Welcome to our homepage</h2>')
        with self.assertRaises(ValueError):
            self.scraper.scrape_company(c)

    def test_expired_structured_detail_is_not_alerted(self):
        c = {**self.company,"location":"Türkiye", "fetch_details":True}
        detail = '<script type="application/ld+json">'+json.dumps({"@graph":[{"@type":"JobPosting","title":"Junior Java Developer","validThrough":"2000-01-01","description":"New graduates are welcome"}]})+'</script>'
        self.scraper._get_request = Mock(side_effect=[response(c["url"],'<a class="job" href="/role/1">Junior Java Developer</a>'),response('https://example.com/role/1',detail)])
        self.assertEqual(self.scraper.scrape_company(c),[])

    def test_detail_can_establish_new_grad_eligibility(self):
        c = {**self.company,"location":"Türkiye", "fetch_details":True}
        self.scraper._get_request = Mock(side_effect=[response(c["url"],'<a class="job" href="/role/1">Java Developer</a>'),response('https://example.com/role/1','<main>No prior experience required</main>')])
        self.assertEqual(len(self.scraper.scrape_company(c)),1)

    def test_today_deadline_is_open_until_day_end(self):
        self.assertFalse(expired(datetime.now(ZoneInfo("Europe/Istanbul")).date().isoformat()))
        self.assertTrue(expired("2000-01-01"))

    def test_turkcell_pagination_and_deadline(self):
        c = {**self.company, "type":"turkcell", "api_url":"https://example.com/handler?Operation=GetPosts&PageIndex=0"}
        job={"JobID":"1","JobName":"1 - Junior Java Developer", "Location":"Istanbul", "PortalURL":"https://example.com/job/1"}
        self.scraper._get_request = Mock(side_effect=[response(c["api_url"],{"result":[job]}),response(c["api_url"],{"result":[job]})])
        jobs=self.scraper.scrape_company(c)
        self.assertEqual(len(jobs),1)
        self.assertEqual(jobs[0]["title"],"Junior Java Developer")

    def test_qnb_public_get_only_and_empty_schema(self):
        c={**self.company,"type":"qnb", "api_url":"https://api.qnbkariyer.com/api"}
        session=Mock()
        session.__enter__=Mock(return_value=session)
        session.__exit__=Mock(return_value=False)
        session.get.side_effect=[response(c["api_url"]+'/token','public-csrf'),response(c["api_url"]+'/ilanlar',{"ilanlar":[{"title":"Uzman Yardımcısı","header":"BT","slug":"bt-1","city":"Istanbul","end_date":"2099-01-01"}]})]
        with patch("scrapers.company_scraper.requests.Session",return_value=session):
            self.assertEqual(len(self.scraper.scrape_company(c)),1)
        session.post.assert_not_called()
        self.assertEqual(session.get.call_count,2)

    def test_smartrecruiters_paginates_and_reads_detail(self):
        c = {**self.company, "type":"smartrecruiters", "api_url":"https://example.com/postings"}
        item = {"id":"1", "name":"Java Developer", "location":{"country":"tr", "city":"Istanbul"}, "experienceLevel":{"id":"entry_level"}}
        detail = {"postingUrl":"https://example.com/job/1", "jobAd":{"sections":{"qualifications":{"text":"Java and Spring Boot"}}}}
        self.scraper._get_request = Mock(side_effect=[response(c["api_url"],{"totalFound":2,"content":[item]}),response('detail',detail),response('page2',{"totalFound":2,"content":[{**item,"id":"2","location":{"country":"de"}}]})])
        self.assertEqual(len(self.scraper.scrape_company(c)),1)
        self.assertEqual(self.scraper.raw_count,2)
        self.assertIn("offset=1", self.scraper._get_request.call_args.args[0])

    def test_smartrecruiters_brand_gate(self):
        c = {**self.company,"type":"smartrecruiters","api_url":"https://example.com/postings", "brand":"Yemeksepeti"}
        item = {"id":"1","name":"Junior Java Developer","location":{"country":"tr"},"customField":[{"fieldLabel":"Brands","valueLabel":"Other"}]}
        self.scraper._get_request = Mock(return_value=response(c["api_url"],{"totalFound":1,"content":[item]}))
        self.assertEqual(self.scraper.scrape_company(c),[])
        self.assertEqual(self.scraper._get_request.call_count,1)

    def test_baykar_pagination_skips_closed_and_detects_incomplete(self):
        c = {**self.company,"type":"baykar","api_url":"https://example.com/feed"}
        item = {"id":1,"text":"Junior Java Developer","new_slug":"java","active":True,"visible":True,"stop_application":False}
        self.scraper._detail = Mock(return_value={"description":"No experience required"})
        self.scraper._get_request = Mock(side_effect=[response('page1',{"count":2,"next":"https://example.com/feed?page=2","results":[item]}),response('page2',{"count":2,"next":None,"results":[{**item,"id":2,"stop_application":True}]})])
        self.assertEqual(len(self.scraper.scrape_company(c)),1)
        self.scraper._detail.assert_called_once()
        self.scraper._get_request = Mock(return_value=response('page1',{"count":2,"next":None,"results":[item]}))
        with self.assertRaises(ValueError):
            self.scraper.scrape_company(c)

    def test_senior_detail_is_not_fetched(self):
        c = {**self.company,"fetch_details":True,"location":"Türkiye"}
        self.scraper._get_request = Mock(return_value=response(c["url"],'<a class="job" href="/role/1">Senior Java Developer</a>'))
        self.assertEqual(self.scraper.scrape_company(c),[])
        self.assertEqual(self.scraper._get_request.call_count,1)

    def test_workday_country_filter_and_detail(self):
        c = {**self.company,"type":"workday","api_url":"https://example.com/wday/cxs/test/site"}
        initial = {"total":9,"jobPostings":[],"facets":[{"facetParameter":"country","descriptor":"Country","values":[{"id":"TR-ID","descriptor":"Türkiye","count":1}]}]}
        filtered = {"total":1,"jobPostings":[{"title":"Junior Java Developer","externalPath":"/job/Istanbul/Java_1","locationsText":"Istanbul"}]}
        self.scraper._get_request = Mock(return_value=response('detail',{"jobPostingInfo":{"jobDescription":"Java, Spring Boot","location":"Istanbul"}}))
        with patch("scrapers.company_scraper.requests.post",side_effect=[response('initial',initial),response('filtered',filtered)]) as post:
            jobs=self.scraper.scrape_company(c)
            self.assertEqual(len(jobs),1)
            self.assertEqual(post.call_args.kwargs['json']['appliedFacets'],{'country':['TR-ID']})
            self.assertIn('/job/Istanbul/Java_1',jobs[0]['url'])

    def test_workday_nested_location_fallback(self):
        c = {**self.company,"type":"workday","api_url":"https://example.com/api"}
        initial = {"total":8,"jobPostings":[],"facets":[{"facetParameter":"locationMainGroup","values":[{"facetParameter":"locations","values":[{"id":"IST","descriptor":"Istanbul"},{"id":"BER","descriptor":"Berlin"}]}]}]}
        with patch("scrapers.company_scraper.requests.post",side_effect=[response('initial',initial),response('empty',{'total':0,'jobPostings':[]})]) as post:
            self.assertEqual(self.scraper.scrape_company(c),[])
            self.assertEqual(post.call_args.kwargs['json']['appliedFacets'],{'locations':['IST']})

    def test_workday_absent_country_and_missing_schema_are_distinct(self):
        c = {**self.company,"type":"workday","api_url":"https://example.com/api"}
        data={'total':8,'jobPostings':[],'facets':[{'facetParameter':'country','descriptor':'Countries','values':[{'id':'DE','descriptor':'Germany'}]}]}
        with patch("scrapers.company_scraper.requests.post",return_value=response('list',data)) as post:
            self.assertEqual(self.scraper.scrape_company(c),[])
            post.assert_called_once()
        data['facets']=[]
        with patch("scrapers.company_scraper.requests.post",return_value=response('list',data)):
            with self.assertRaises(ValueError):
                self.scraper.scrape_company(c)

    def test_workday_repeated_page_is_error(self):
        c = {**self.company,"type":"workday","api_url":"https://example.com/api"}
        initial={'total':2,'jobPostings':[],'facets':[{'facetParameter':'country','descriptor':'Country','values':[{'id':'TR','descriptor':'Turkey'}]}]}
        page={'total':2,'jobPostings':[{'title':'Senior Java Developer','externalPath':'/job/1'}]}
        with patch("scrapers.company_scraper.requests.post",side_effect=[response('list',initial),response('p1',page),response('p2',page)]):
            with self.assertRaises(ValueError):
                self.scraper.scrape_company(c)

    def test_workday_additional_graduate_board_is_read(self):
        c = {**self.company,"type":"workday","api_url":"https://example.com/main", "additional_boards":[{"url":"https://example.com/graduates","api_url":"https://example.com/graduate-api"}]}
        with patch("scrapers.company_scraper.requests.post",return_value=response('empty',{'total':0,'jobPostings':[]})) as post:
            self.assertEqual(self.scraper.scrape_company(c),[])
            self.assertEqual([call.args[0] for call in post.call_args_list],['https://example.com/main/jobs','https://example.com/graduate-api/jobs'])

    def test_akbank_reads_qualifications_and_epoch_deadline(self):
        c={**self.company,"type":"akbank","api_url":"https://example.com/api"}
        row={"id":"1","title":"Junior Java Developer","city":"Istanbul","applicationDeadLine":4102444800000}
        detail={"jobDescription":"Java and Spring", "jobQualifications":"En az 7 yıl deneyimli"}
        with patch("scrapers.company_scraper.requests.post",side_effect=[response('list',[row]),response('detail',detail)]) as post:
            self.assertEqual(self.scraper.scrape_company(c),[])
            self.assertEqual(post.call_args.kwargs['json'],{'id':'1'})
        detail['jobQualifications']='Yeni mezun adaylar'
        with patch("scrapers.company_scraper.requests.post",side_effect=[response('list',[row]),response('detail',detail)]):
            jobs=self.scraper.scrape_company(c)
            self.assertEqual(len(jobs),1)
            self.assertTrue(jobs[0]['url'].endswith('/shared/advert-list/1'))
        row['applicationDeadLine']=946684800000
        with patch("scrapers.company_scraper.requests.post",return_value=response('list',[row])) as post:
            self.assertEqual(self.scraper.scrape_company(c),[])
            post.assert_called_once()

    def test_akbank_professional_category_is_excluded_before_detail(self):
        c={**self.company,"type":"akbank","api_url":"https://example.com/api"}
        row={"id":"1","title":"Java Developer","experience":"Profesyonelim"}
        with patch("scrapers.company_scraper.requests.post",return_value=response('list',[row])) as post:
            self.assertEqual(self.scraper.scrape_company(c),[])
            post.assert_called_once()

    def test_program_image_change_changes_fingerprint_without_notifications(self):
        from scrapers.program_scraper import ProgramScraper
        program={"company":"Test", "name":"TechTalent", "url":"https://example.com/program", "selector":"main", "expected_text":"TechTalent", "image_selector":"img"}
        page='<main>TechTalent '+('program description '*10)+'</main><img src="/dates.png">'
        fingerprints=[]
        reader=ProgramScraper()
        with patch("scrapers.program_scraper.read_radar",return_value=([{"name":"Test"}],[])), patch("scrapers.program_scraper.Path.read_text",return_value=json.dumps([program])), patch.object(reader,"random_sleep"), patch("scrapers.program_scraper.database.program_event",side_effect=lambda url,fp,job:fingerprints.append(fp)), patch("scrapers.program_scraper.requests.get",side_effect=[response(program['url'],page),response('image','version one'),response(program['url'],page),response('image','version two')]):
            reader.scrape()
            reader.scrape()
        self.assertEqual(len(fingerprints),2)
        self.assertNotEqual(fingerprints[0],fingerprints[1])

    def test_assistant_abbreviated_title(self):
        from watchlist import relevant
        # Kisaltilmis unvan taninir; teknoloji alani yoksa yine elenir.
        self.assertTrue(relevant('Yazılım Uzm.Yrd / Uzmanı'))
        self.assertFalse(relevant('Dijital Pazarlama Uzm.Yrd / Uzmanı'))
        self.assertFalse(relevant('Yazılım Uzm.Yrd / Uzmanı','En az 5 yıl deneyimli'))

    def test_removed_company_is_not_loaded_even_if_config_enabled(self):
        rows = [{"name":"Keep", "enabled":True}, {"name":"Remove", "enabled":True}, {"name":"Extra", "enabled":True, "extra_source":True}]
        from unittest.mock import mock_open
        with patch("scrapers.company_scraper.open", mock_open(read_data=json.dumps(rows))), patch("scrapers.company_scraper.read_radar",return_value=([{"name":"Keep"}],[])):
            reader = CompanyScraper()
        self.assertEqual([c["name"] for c in reader.companies], ["Keep", "Extra"])

    def test_parallel_sources_isolate_errors_and_reset_results(self):
        reader = self.scraper
        reader.companies = [{"name":"Good"}, {"name":"Bad"}, {"name":"Off","enabled":False}]
        def scrape(worker, company):
            if company["name"] == "Bad":
                raise ValueError("broken source")
            worker.raw_count = 1
            return [{"url":"https://example.com/job"}]
        with patch.object(CompanyScraper,"scrape_company",scrape):
            self.assertEqual(len(reader.scrape()),1)
            self.assertEqual(len(reader.scrape()),1)
        self.assertEqual(len(reader.source_results),2)
        self.assertEqual([r["status"] for r in reader.source_results],["ok","error"])

    def test_removed_program_is_not_requested(self):
        from scrapers.program_scraper import ProgramScraper
        program = {"company":"Removed", "url":"https://example.com/program"}
        with patch("scrapers.program_scraper.read_radar",return_value=([{"name":"Keep"}],[])), patch("scrapers.program_scraper.Path.read_text",return_value=json.dumps([program])), patch("scrapers.program_scraper.requests.get") as get:
            ProgramScraper().scrape()
        get.assert_not_called()

    def test_junior_infrastructure_roles_require_early_career(self):
        from watchlist import relevant
        self.assertTrue(relevant("Junior Monitoring Specialist"))
        self.assertTrue(relevant("Junior Network Engineer"))
        self.assertFalse(relevant("Senior Monitoring Specialist"))
        self.assertFalse(relevant("Monitoring Specialist"))
        self.assertFalse(relevant("Junior Network Engineer", "Minimum 5 years experience"))

    def test_short_bank_announcement_validates_page_title(self):
        from scrapers.program_scraper import ProgramScraper
        p = {"company":"Test", "name":"Duyurular", "url":"https://example.com/news", "selector":"main", "expected_text":"", "expected_page_title":"Bankacılık İlanları", "min_chars":20}
        reader = ProgramScraper()
        html = "<title>Bankacılık İlanları</title><main>İlanlarımız için takipte kalın.</main>"
        with patch("scrapers.program_scraper.read_radar",return_value=([{"name":"Test"}],[])), patch("scrapers.program_scraper.Path.read_text",return_value=json.dumps([p])), patch("scrapers.program_scraper.requests.get",return_value=response(p["url"],html)), patch("scrapers.program_scraper.database.program_event") as event, patch.object(reader,"random_sleep"):
            reader.scrape()
            event.assert_called_once()
        with patch("scrapers.program_scraper.read_radar",return_value=([{"name":"Test"}],[])), patch("scrapers.program_scraper.Path.read_text",return_value=json.dumps([p])), patch("scrapers.program_scraper.requests.get",return_value=response(p["url"],html.replace("Bankacılık İlanları","Giriş Yap"))), patch("scrapers.program_scraper.database.program_event") as event:
            reader.scrape()
            event.assert_not_called()

    def test_json_program_content_ignores_volatile_fields_and_other_locales(self):
        from scrapers.program_scraper import json_program_content
        def payload(title, html, stamp):
            return [{"id": "a-" + stamp, "updatedAt": stamp, "translations": [
                {"locale": "tr", "id": "t-" + stamp, "updatedAt": stamp, "title": title, "html": html},
                {"locale": "en", "title": "Students", "html": "English copy " + stamp}]}]
        baseline = json_program_content(payload("Öğrenci & Yeni Mezun", "Başvurular kapalı", "1"), "tr", ["title", "html"])
        # Kayit kimligi, zaman damgasi ve diger dil surumleri parmak izini degistirmemeli.
        self.assertEqual(baseline, json_program_content(payload("Öğrenci & Yeni Mezun", "Başvurular kapalı", "2"), "tr", ["title", "html"]))
        self.assertNotEqual(baseline, json_program_content(payload("Öğrenci & Yeni Mezun", "Başvurular açıldı", "1"), "tr", ["title", "html"]))
        self.assertNotIn("English copy", baseline)
        with self.assertRaises(ValueError):
            json_program_content(payload("x", "y", "1"), "de", ["title", "html"])

    def test_kariyer_mail_accepts_only_direct_job_links(self):
        from scrapers.kariyer_mail import KariyerMailScraper
        def mail(body):
            return ("From: bilgi@kariyer.net\r\nSubject: İş Habercisi\r\nMIME-Version: 1.0\r\n"
                    "Content-Type: text/html; charset=utf-8\r\n\r\n" + body).encode("utf-8")
        body = ('<a href="https://www.kariyer.net/is-ilani/abc-123">Junior Java Developer</a>'
                '<a href="https://www.kariyer.net/is-ilani/abc-123?utm_source=mail">Hemen Başvur</a>'
                '<a href="https://email.kariyer.net/r/xyz">Yazılım Uzman Yardımcısı</a>'
                '<a href="http://www.kariyer.net/is-ilani/def-456">Data Analyst</a>'
                '<a href="https://www.kariyer.net/firma-profil/test">Firma Profili</a>')
        jobs = KariyerMailScraper.parse_message(mail(body))
        self.assertEqual([j["url"] for j in jobs], ["https://www.kariyer.net/is-ilani/abc-123"])
        self.assertEqual(jobs[0]["title"], "Junior Java Developer")
        # Ayni ilan iki kez gecerse tek kayit kalir ve takip parametreleri adresten dusurulur.
        twice = KariyerMailScraper.parse_message(mail(
            '<a href="https://www.kariyer.net/is-ilani/abc-123">Junior Java Developer</a>'
            '<a href="https://www.kariyer.net/is-ilani/abc-123?utm_medium=email">Junior Java Developer</a>'))
        self.assertEqual(len(twice), 1)
        self.assertEqual(KariyerMailScraper.parse_message(mail("<p>HTML var ama ilan yok</p>")), [])

    def test_jobspy_linkedin_failure_does_not_drop_indeed_results(self):
        import sys, types
        from scrapers import jobspy_scraper
        class Frame:
            def __init__(self, rows):
                self.rows = rows
                self.empty = not rows
            def iterrows(self):
                return enumerate(self.rows)
        def fake_scrape_jobs(site_name, **kwargs):
            if site_name == ["linkedin"]:
                raise AttributeError("'NoneType' object has no attribute 'lower'")
            return Frame([{"title": "Junior Java Developer", "company": "Test", "location": "İstanbul",
                           "job_url": "https://tr.indeed.com/viewjob?jk=1", "site": "indeed", "description": ""}])
        fake = types.ModuleType("jobspy")
        fake.scrape_jobs = fake_scrape_jobs
        scraper = jobspy_scraper.JobSpyScraper()
        scraper.random_sleep = Mock()
        with patch.dict(sys.modules, {"jobspy": fake}), patch.object(jobspy_scraper.config, "SEARCH_QUERIES", ["junior java"]):
            jobs = scraper.scrape()
        self.assertEqual([j["source"] for j in jobs], ["indeed"])

    def test_jobspy_linkedin_missing_job_level_is_made_none_safe(self):
        import sys, types
        from scrapers.jobspy_scraper import patch_linkedin_job_level
        package, linkedin = types.ModuleType("jobspy"), types.ModuleType("jobspy.linkedin")
        linkedin.parse_job_level = lambda soup: None
        package.linkedin = linkedin
        with patch.dict(sys.modules, {"jobspy": package, "jobspy.linkedin": linkedin}):
            patch_linkedin_job_level()
            patch_linkedin_job_level()  # ikinci cagri tekrar sarmamali
            self.assertEqual(linkedin.parse_job_level(object()), "")
            self.assertTrue(linkedin.parse_job_level._none_safe)
        linkedin.parse_job_level = lambda soup: "Entry level"
        with patch.dict(sys.modules, {"jobspy": package, "jobspy.linkedin": linkedin}):
            patch_linkedin_job_level()
            self.assertEqual(linkedin.parse_job_level(object()), "Entry level")

    def test_canonical_keeps_job_id(self):
        self.assertEqual(canonical("https://example.com/ilan?id=42&utm_source=test#apply"),"https://example.com/ilan?id=42")

    def test_enabled_sources_declare_every_field_their_reader_needs(self):
        """Kaynak sayisi buyudukce eksik ayar canli taramada sessiz hataya donusmesin."""
        import os
        from scrapers.company_scraper import COMPANIES_FILE
        with open(COMPANIES_FILE, encoding="utf-8") as handle:
            companies = json.load(handle)
        required = {"lever": ["api_url"], "greenhouse": ["api_url"], "ashby": ["api_url"],
                    "workday": ["api_url"], "smartrecruiters": ["api_url"], "eightfold": ["api_url", "domain", "search_location"],
                    "pcsx": ["api_url", "domain"], "flowq": ["api_url", "board"], "savunma": ["api_url", "company_id"],
                    "hirebridge": ["expected_company", "cid"], "hrpeak_browser": ["expected_company"],
                    "successfactors_browser": ["tenant"], "successfactors_csb": [], "generic": ["selector"]}
        names = [c["name"] for c in companies]
        self.assertEqual(len(names), len(set(names)), "companies.json icinde tekrarlanan sirket adi var")
        for company in companies:
            if not company.get("enabled", True):
                continue
            kind = company.get("type", "generic")
            self.assertTrue(hasattr(CompanyScraper, "_scrape_" + kind), company["name"] + ": bilinmeyen kaynak turu " + kind)
            for field in required.get(kind, []):
                self.assertTrue(company.get(field), company["name"] + ": " + kind + " icin " + field + " eksik")
            self.assertTrue(company["url"].startswith("https://"), company["name"] + ": kaynak adresi https olmali")
            if company.get("local_only"):
                self.assertEqual(company.get("country_scope"), "TR", company["name"] + ": local_only yalniz TR kapsaminda kullanilir")

if __name__ == "__main__":
    unittest.main()
