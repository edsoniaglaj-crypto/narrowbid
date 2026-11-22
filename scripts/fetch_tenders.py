#!/usr/bin/env python3
"""Fetch recent UK Find a Tender OCDS releases into a transparent static data feed.

Designed for scheduled GitHub Actions. Only published government notices are used.
No AI-generated opportunities or claims. The official source is definitive.
"""
from __future__ import annotations
import datetime as dt
import json
import os
import re
import sys
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlparse, parse_qs
from urllib.request import Request, urlopen

BASE = "https://www.find-tender.service.gov.uk/api/1.0/ocdsReleasePackages"
DATA = Path(__file__).resolve().parents[1] / 'data' / 'tenders.json'
NOW = dt.datetime.now(dt.timezone.utc)
GOOD_WORDS = {
    'web': ('website', 'web development', 'web design', 'digital platform', 'application development', 'software development', 'user experience', 'ui/ux', 'content management system', 'software engineering', 'digital service', 'it consultancy'),
    'marketing': ('marketing', 'public relations', 'communications', 'advertising', 'campaign', 'social media', 'media planning', 'digital engagement', 'content strategy'),
    'design': ('graphic design', 'branding', 'brand identity', 'creative design', 'visual design', 'illustration', 'publication design'),
    'video': ('video production', 'filmmaking', 'photography', 'animation', 'film production', 'videography', 'audiovisual', 'audio-visual'),
    'research': ('market research', 'customer research', 'user research', 'audience research', 'public opinion', 'usability research', 'research survey'),
}
# CPV prefix categories, used as supporting indicators, never as eligibility claims.
CPV_PREFIXES = {
    'web': ('724130', '72212', '72262'),
    'marketing': ('7934', '79416'),
    'design': ('7982', '7993'),
    'video': ('9211', '79961'),
    'research': ('7931', '7932'),
}


def utcstamp(d: dt.datetime) -> str:
    return d.strftime('%Y-%m-%dT%H:%M:%S')


def request_json(url: str, tries=3) -> dict:
    if urlparse(url).hostname != 'www.find-tender.service.gov.uk':
        raise ValueError('Refusing to fetch outside official Find a Tender hostname')
    err = None
    for i in range(tries):
        try:
            req = Request(url, headers={'Accept': 'application/json', 'User-Agent': 'NarrowBidOpenDataPrototype/0.1 (+https://www.gov.uk/government/publications/open-contracting)'})
            with urlopen(req, timeout=35) as response:
                if response.status != 200:
                    raise RuntimeError(f'HTTP {response.status}')
                data = response.read(15_000_001)
                if len(data)>15_000_000: raise RuntimeError('API page too large')
                return json.loads(data)
        except (HTTPError, URLError, TimeoutError, ValueError, RuntimeError) as exc:
            err=exc
            if i<tries-1: time.sleep((i+1)*3)
    raise RuntimeError(f'API unavailable: {err}')


def text_clean(value, max_len=400) -> str:
    s = re.sub(r'<[^>]*>', ' ', str(value or ''))
    s = re.sub(r'\s+', ' ', s).strip()
    return s[:max_len]


def iso_date(value: str | None) -> str | None:
    if not value: return None
    try:
        d=dt.datetime.fromisoformat(value.replace('Z', '+00:00'))
        if d.tzinfo is None: d=d.replace(tzinfo=dt.timezone.utc)
        return d.astimezone(dt.timezone.utc).isoformat().replace('+00:00','Z')
    except (ValueError, AttributeError):
        return None


def get_cpv(tender: dict) -> list[str]:
    codes=[]
    items = [tender] + [i for i in tender.get('items', []) if isinstance(i, dict)]
    for obj in items:
        classes=([obj.get('classification')] if obj.get('classification') else []) + (obj.get('additionalClassifications') or [])
        for cls in classes:
            if isinstance(cls, dict):
                code=str(cls.get('id') or '').replace('-','').strip()
                scheme=str(cls.get('scheme') or 'CPV').lower()
                if code.isdigit() and ('cpv' in scheme or scheme == ''): codes.append(code)
    return sorted(set(codes))


def find_buyer(r: dict) -> str:
    tender = r.get('tender') or {}
    buyer = r.get('buyer') or {}
    if buyer.get('name'): return text_clean(buyer['name'], 140)
    buyer_id = buyer.get('id')
    for p in r.get('parties') or []:
        if not isinstance(p, dict): continue
        if buyer_id and p.get('id')==buyer_id: return text_clean(p.get('name'), 140)
        if 'buyer' in (p.get('roles') or []): return text_clean(p.get('name'), 140)
    return text_clean(tender.get('procuringEntity',{}).get('name'), 140) or 'Not disclosed'


def categories(r: dict) -> list[str]:
    t=r.get('tender') or {}
    title=text_clean(t.get('title') or '',400).lower()
    # Match the title or specific service classifications to limit incidental matches.
    cpvs=get_cpv(t)
    result=[]
    for cat,words in GOOD_WORDS.items():
        if any(re.search(r'(?<!\w)' + re.escape(w) + r'(?!\w)', title) for w in words): result.append(cat)
        elif any(c.startswith(prefix) for c in cpvs for prefix in CPV_PREFIXES[cat]): result.append(cat)
    return result


def extract_url(r: dict) -> str | None:
    # Prefer actual published official notice URI (not an inferred procurement portal).
    candidates=[r.get('uri'),r.get('url')]
    t=r.get('tender') or {}
    candidates += [d.get('url') for d in t.get('documents',[]) if isinstance(d,dict)]
    candidates += [d.get('url') for d in r.get('documents',[]) if isinstance(d,dict)]
    for c in candidates:
        if not isinstance(c,str): continue
        p=urlparse(c)
        if p.scheme=='https' and p.hostname=='www.find-tender.service.gov.uk' and ('/Notice/' in p.path or '/notice/' in p.path): return c
    # Only known official reference form can be used to construct the canonical source link.
    # Do NOT use this fallback when the release ID isn't a recognizable notice number.
    for identifier in [r.get('id'), (r.get('tender') or {}).get('id')]:
        if not isinstance(identifier,str): continue
        m=re.search(r'(\d{6}-20\d{2})',identifier)
        if m: return 'https://www.find-tender.service.gov.uk/Notice/'+m.group(1)
    return None


def normalize(r: dict) -> dict | None:
    if not isinstance(r,dict):return None
    tags=r.get('tag') or []
    if not isinstance(tags,list) or not any(t in tags for t in ('tender','tenderUpdate')):return None
    if any(t in tags for t in ('tenderCancellation','cancellation','award','contract','planning')):return None
    t=r.get('tender') or {}
    if t.get('status') in ('cancelled','unsuccessful','complete','withdrawn'):return None
    title=text_clean(t.get('title'),180)
    if not title:return None
    cats=categories(r)
    if not cats:return None
    deadline=iso_date((t.get('tenderPeriod') or {}).get('endDate'))
    if deadline and dt.datetime.fromisoformat(deadline.replace('Z','+00:00')) < NOW:return None
    url=extract_url(r)
    if not url:return None
    # Value is a buyer's estimate, not a guarantee; store only in GBP.
    val=(t.get('value') or {})
    amount=val.get('amount') if val.get('currency')=='GBP' else None
    try: amount=float(amount) if amount is not None and float(amount)>0 else None
    except (ValueError,TypeError):amount=None
    ident=text_clean(r.get('id') or r.get('ocid'),110)
    if not ident:return None
    published=iso_date(r.get('date'))
    # Location only when explicitly present.
    regions=[]
    for it in t.get('items',[]) or []:
        for loc in (it.get('deliveryAddresses') or []):
            if isinstance(loc,dict) and loc.get('region'):regions.append(text_clean(loc['region'],80))
    region=', '.join(dict.fromkeys(regions))[:150] or None
    return dict(id=ident,ocid=text_clean(r.get('ocid'),120),title=title,description=text_clean(t.get('description'),900),buyer=find_buyer(r),published=published,deadline=deadline,value=amount,region=region,tags=cats,cpv=get_cpv(t),url=url)


def collect_days(days: int) -> list[dict]:
    since=NOW-dt.timedelta(days=days)
    start=utcstamp(since)
    end=utcstamp(NOW)
    query=urlencode({'updatedFrom':start,'updatedTo':end,'limit':100,'stages':'tender'})
    url=BASE+'?'+query
    rows=[]
    seen_pages=set()
    for page in range(120):
        if url in seen_pages:raise RuntimeError('API repeated a cursor URL')
        seen_pages.add(url)
        resp=request_json(url)
        rows.extend(resp.get('releases') or [])
        nxt=(resp.get('links') or {}).get('next')
        if not nxt:break
        if isinstance(nxt,dict):nxt=nxt.get('href')
        if not isinstance(nxt,str):break
        if nxt.startswith('?'): url=BASE+nxt
        elif nxt.startswith('/'):url='https://www.find-tender.service.gov.uk'+nxt
        else:url=nxt
    else:
        raise RuntimeError('Pagination cap reached; refusing partial update')
    return rows


def main():
    original={'tenders':[]}
    try:original=json.loads(DATA.read_text(encoding='utf-8'))
    except (FileNotFoundError, ValueError):pass
    days=21 if not original.get('updated_at') else 3
    # Refuse to overwrite last good data after an API error.
    raw=collect_days(days)
    records={}
    cutoff=NOW-dt.timedelta(days=95)
    for d in original.get('tenders',[]):
        try:
            if (not d.get('deadline') or dt.datetime.fromisoformat(d['deadline'].replace('Z','+00:00'))>NOW) and (not d.get('published') or dt.datetime.fromisoformat(d['published'].replace('Z','+00:00'))>cutoff):
                records[d.get('ocid') or d['id']]=d
        except (KeyError,ValueError,TypeError):continue
    count=0
    for release in sorted(raw, key=lambda r: iso_date(r.get('date')) or ''):
        key = text_clean(release.get('ocid') or release.get('id'), 120)
        tender = release.get('tender') or {}
        tags = release.get('tag') or []
        if ('tenderCancellation' in tags or 'cancellation' in tags
            or tender.get('status') in ('cancelled', 'unsuccessful', 'complete', 'withdrawn')):
            records.pop(key, None)
            continue
        d=normalize(release)
        if d:
            records[d.get('ocid') or d['id']]=d
            count+=1
    # Guard against publish of an empty feed caused by an unexpected API schema.
    if raw and not count and not records:
        raise RuntimeError('API returned releases, but no valid matching notices: refusing empty overwrite')
    result=sorted(records.values(),key=lambda d:d.get('published') or '',reverse=True)[:500]
    out={'updated_at':NOW.isoformat().replace('+00:00','Z'),'source':BASE,'tenders':result,'info':{'matched_in_latest_sync':count,'raw_releases_checked':len(raw),'lookback_days':days,'note':'Only verified official notices; source documents determine eligibility.'}}
    tmp=DATA.with_suffix('.tmp')
    tmp.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    tmp.replace(DATA)
    print(f'Published {len(result)} verified matches from {len(raw)} official releases (new/updated: {count}).')

if __name__=='__main__':
    try:main()
    except Exception as exc:
        print('Tender feed refresh FAILED:',exc,file=sys.stderr)
        sys.exit(1)
