#!/usr/bin/env python3
"""해외 스키·아웃도어 업계 소식을 RSS로 매일 긁어 모은다.

  python3 pipeline/fetch_news.py [--days 14]

결과: research/news_feed.csv (수집일,발행일,지역,매체,제목,링크)
이건 '후보 풀'이다. 뉴스 카드에 실리는 줄은 research/news_industry.csv 에
사람이 확인한 뒤 옮겨 적는다. 이 파일을 그대로 싣지 않는다.

에이전트 프록시 때문에 로컬에서는 대부분 막힌다. GitHub Actions 러너에서 돈다.
"""
import csv, os, re, sys, urllib.request, urllib.error
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime

DAYS = int(sys.argv[sys.argv.index('--days')+1]) if '--days' in sys.argv else 14
OUT = 'research/news_feed.csv'
UA = {'User-Agent': 'Mozilla/5.0 (compatible; SANKIT-magazine/1.0; +https://instagram.com/sankitmag)'}

# (지역, 매체, 피드)  — 지역은 뉴스 줄의 국가 이모지를 고르는 데 쓴다
SOURCES = [
    ('미국', 'SnowBrains',            'https://snowbrains.com/feed/'),
    ('미국', 'Unofficial Networks',   'https://unofficialnetworks.com/feed/'),
    ('미국', 'Outside Business Jrnl', 'https://www.outsidebusinessjournal.com/feed/'),
    ('미국', 'SGB Media',             'https://sgbonline.com/feed/'),
    ('미국', 'GearJunkie',            'https://gearjunkie.com/feed'),
    ('미국', 'Blister',               'https://blisterreview.com/feed'),
    ('미국', 'Freeskier',             'https://freeskier.com/feed'),
    ('유럽', 'PlanetSKI',             'https://planetski.eu/feed/'),
    ('유럽', 'InTheSnow',             'https://www.inthesnow.com/feed/'),
    ('유럽', 'J2Ski',                 'https://www.j2ski.com/ski-news/rss.xml'),
    ('유럽', 'Snow-Forecast',         'https://www.snow-forecast.com/whiteroom/feed'),
    ('유럽', 'ISPO',                  'https://www.ispo.com/en/rss.xml'),
    ('국제', 'FIS',                   'https://www.fis-ski.com/DB/general/rss.html'),
    ('국제', 'Outdoor Industry',      'https://outdoorindustry.org/feed/'),
    ('일본', 'SnowJapan',             'https://www.snowjapan.com/feed'),
    ('일본', 'Traicy',                'https://www.traicy.com/feed'),
]

def txt(e, *tags):
    for t in tags:
        x = e.find(t)
        if x is not None:
            if x.text and x.text.strip():
                return x.text.strip()
            if t.endswith('link') and x.get('href'):
                return x.get('href')
    return ''

def when(s):
    if not s: return None
    try: return parsedate_to_datetime(s)
    except Exception: pass
    for f in ('%Y-%m-%dT%H:%M:%S%z', '%Y-%m-%dT%H:%M:%SZ', '%Y-%m-%d'):
        try:
            d = datetime.strptime(s.strip()[:len(f)+6 if '%z' in f else len(s.strip())], f)
            return d if d.tzinfo else d.replace(tzinfo=timezone.utc)
        except Exception: continue
    return None

def pull(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=25) as r:
        root = ET.fromstring(r.read())
    ns = {'a': 'http://www.w3.org/2005/Atom'}
    out = []
    for it in root.iter():
        tag = it.tag.split('}')[-1]
        if tag not in ('item', 'entry'):
            continue
        title = txt(it, 'title', '{http://www.w3.org/2005/Atom}title')
        link = txt(it, 'link', '{http://www.w3.org/2005/Atom}link')
        if not link:
            l = it.find('{http://www.w3.org/2005/Atom}link')
            link = l.get('href') if l is not None else ''
        pub = when(txt(it, 'pubDate', 'published', 'updated',
                       '{http://www.w3.org/2005/Atom}published',
                       '{http://www.w3.org/2005/Atom}updated'))
        title = re.sub(r'\s+', ' ', title).strip()
        if title and link:
            out.append((pub, title, link.strip()))
    return out

def main():
    today = datetime.now(timezone.utc).date()
    cut = datetime.now(timezone.utc) - timedelta(days=DAYS)

    old = []
    if os.path.exists(OUT):
        with open(OUT, encoding='utf-8') as f:
            old = list(csv.DictReader(f))
    seen = {r['링크'] for r in old}

    fresh, report = [], []
    for region, name, url in SOURCES:
        try:
            items = pull(url)
        except Exception as e:
            report.append(f'  {name:<22} 실패  {type(e).__name__} {str(e)[:60]}')
            continue
        n = 0
        for pub, title, link in items[:30]:
            if pub and pub < cut:
                continue
            if link in seen:
                continue
            seen.add(link)
            fresh.append({'수집일': today.isoformat(),
                          '발행일': pub.date().isoformat() if pub else '',
                          '지역': region, '매체': name, '제목': title, '링크': link})
            n += 1
        report.append(f'  {name:<22} 항목 {len(items):>3}개 · 새 글 {n:>3}개')

    keep = [r for r in old
            if not r.get('수집일') or
            (datetime.fromisoformat(r['수집일']).date() + timedelta(days=DAYS)) >= today]
    rows = fresh + keep
    rows.sort(key=lambda r: (r.get('발행일') or r.get('수집일') or ''), reverse=True)

    os.makedirs('research', exist_ok=True)
    with open(OUT, 'w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, ['수집일', '발행일', '지역', '매체', '제목', '링크'])
        w.writeheader(); w.writerows(rows)

    print('\n'.join(report))
    ok = sum(1 for l in report if '실패' not in l)
    print(f'\n매체 {ok}/{len(SOURCES)} 성공 · 새 글 {len(fresh)}개 · 보관 {len(rows)}개 -> {OUT}')

if __name__ == '__main__':
    main()
