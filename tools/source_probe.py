"""Public career source audit. Never imports bot/notifier or sends alerts."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import json
import re
import hashlib
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

ROOT = Path(__file__).resolve().parents[1]

def probe(url):
    record = {"url": url}
    try:
        r = requests.get(url, timeout=25)
        record.update(status=r.status_code, final_url=r.url)
        key = hashlib.sha256(url.encode()).hexdigest()[:16]
        target = ROOT / '.source-audit' / (key + '.txt')
        target.parent.mkdir(exist_ok=True)
        target.write_text(r.text, encoding='utf-8')
        record['fixture'] = str(target.relative_to(ROOT))
        try:
            data = r.json()
            record['json_shape'] = list(data)[:8] if isinstance(data, dict) else 'list'
            entries = data if isinstance(data, list) else data.get('jobs', data.get('content', []))
            record['count'] = len(entries) if isinstance(entries, list) else None
            if isinstance(entries, list):
                record['sample'] = [{k:item.get(k) for k in ('text','title','name','hostedUrl','absolute_url','url') if item.get(k)} for item in entries[:3] if isinstance(item,dict)]
        except ValueError:
            soup=BeautifulSoup(r.text,'html.parser')
            record['title']=soup.title.get_text(strip=True) if soup.title else ''
            record['links']=[{'text':a.get_text(' ',strip=True)[:90], 'url':urljoin(r.url,a['href'])} for a in soup.select('a[href]') if re.search(r'career|kariyer|job|position|pozisyon|ilan|basvur|başvur|talent|yetenek|graduate|apply|lever|greenhouse|workday', a['href']+' '+a.get_text(),re.I)][:45]
            record['scripts']=[a.get('src') for a in soup.select('script[src]')][-6:]
    except Exception as exc:
        record['error']=str(exc)
    return record

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('urls',nargs='*')
    args=parser.parse_args()
    urls=args.urls or [c.get('api_url') or c['url'] for c in json.loads((ROOT/'companies.json').read_text(encoding='utf-8'))]
    with ThreadPoolExecutor(max_workers=4) as pool:
        for result in pool.map(probe,urls):
            print(json.dumps(result,ensure_ascii=True),flush=True)
