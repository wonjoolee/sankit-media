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

# (지역, 분야, 매체, [후보 주소...])
# 분야: 스키 · 하이킹 · 자전거 · 공통(아웃도어 업계 전반)
# 뺀 곳(403, 자동 접근 거부 — 우회하지 않는다): PlanetSKI · Snow-Forecast · ALPIN ·
#   Pinkbike · Rennrad-News. 필요하면 프레스 메일로 수신 허락을 받는다.
SOURCES = [
    # ── 한국 ──────────────────────────────────────────────
    # 국내 주력은 RSS가 아니라 네이버 뉴스 검색이다(pipeline/fetch_news_kr.py).
    # 국내 매체는 RSS 주소가 자주 바뀌고 없는 곳도 많다. 아래는 보조.
    # 뺀 곳: 자전거생활·한국스키장경영협회 — 도메인이 조회되지 않는다.
    # 종합 매체는 NEED 로 주제어를 걸러 받는다. 전문지는 그대로 받는다.
    ('한국', '공통',   '연합뉴스 스포츠',      ['https://www.yna.co.kr/rss/sports.xml']),
    ('한국', '공통',   '연합뉴스 산업',        ['https://www.yna.co.kr/rss/industry.xml']),
    ('한국', '공통',   '연합뉴스 경제',        ['https://www.yna.co.kr/rss/economy.xml']),
    ('한국', '공통',   '연합뉴스 지역',        ['https://www.yna.co.kr/rss/local.xml']),
    ('한국', '하이킹', '아웃도어뉴스',         ['https://www.outdoornews.co.kr/rss/allArticle.xml',
                                               'http://www.outdoornews.co.kr/rss/allArticle.xml']),
    ('한국', '공통',   '스포츠경향 레저',      ['https://sports.khan.co.kr/rss/rssdata/kh_sports.xml']),
    ('한국', '공통',   '국립공원공단',         ['https://www.knps.or.kr/rss/news.xml',
                                               'https://www.knps.or.kr/front/portal/rss/newsRss.do']),
    ('한국', '공통',   '산림청',               ['https://www.forest.go.kr/kfsweb/rss/kfs_news.xml',
                                               'https://www.forest.go.kr/rss/news.xml']),
    # ── 스키 ──
    ('미국', '스키',   'SnowBrains',          ['https://snowbrains.com/feed/']),
    ('미국', '스키',   'Unofficial Networks', ['https://unofficialnetworks.com/feed/']),
    ('미국', '스키',   'Freeskier',           ['https://freeskier.com/feed']),
    ('미국', '스키',   'SKI Magazine',        ['https://www.skimag.com/feed/']),
    ('미국', '스키',   'Blister',             ['https://blisterreview.com/feed']),
    ('영국', '스키',   'InTheSnow',           ['https://www.inthesnow.com/feed/']),
    ('영국', '스키',   'Ski Club GB',         ['https://www.skiclub.co.uk/rss']),
    ('독일', '스키',   'Skiinfo DE',          ['https://www.skiinfo.de/news/rss']),
    ('호주', '스키',   'Mountainwatch',       ['https://www.mountainwatch.com/feed/']),
    ('호주', '스키',   'SnowsBest',           ['https://www.snowsbest.com/feed/']),
    ('일본', '스키',   'Traicy',              ['https://www.traicy.com/feed']),
    # ── 하이킹·등산 ──
    ('영국', '하이킹', 'grough',              ['https://www.grough.co.uk/mountain/rss',
                                               'https://www.grough.co.uk/rss.xml']),
    ('영국', '하이킹', 'UKClimbing',          ['https://www.ukclimbing.com/news/rss/',
                                               'https://www.ukclimbing.com/rss/']),
    ('호주', '하이킹', 'Wild Magazine',       ['https://wild.com.au/feed/']),
    ('미국', '하이킹', 'Backpacker',          ['https://www.backpacker.com/feed/']),
    ('미국', '하이킹', 'SectionHiker',        ['https://sectionhiker.com/feed/']),
    ('일본', '하이킹', 'YAMAKEI',             ['https://www.yamakei-online.com/news/feed',
                                               'https://www.yamakei-online.com/rss.xml']),
    # ── 자전거 ──
    ('국제', '자전거', 'Bike Europe',         ['https://www.bike-eu.com/rss.xml',
                                               'https://www.bike-eu.com/feed/']),
    ('미국', '자전거', 'Bicycle Retailer',    ['https://www.bicycleretailer.com/rss.xml',
                                               'https://www.bicycleretailer.com/feed']),
    ('미국', '자전거', 'Bikerumor',           ['https://bikerumor.com/feed/']),
    ('미국', '자전거', 'Singletracks',        ['https://www.singletracks.com/feed/']),
    ('영국', '자전거', 'road.cc',             ['https://road.cc/rss']),
    ('영국', '자전거', 'BikeRadar',           ['https://www.bikeradar.com/rss.xml',
                                               'https://www.bikeradar.com/feed/']),
    ('영국', '자전거', 'Cyclingnews',         ['https://www.cyclingnews.com/rss/']),
    ('독일', '자전거', 'MTB-News',            ['https://www.mtb-news.de/news/feed/']),
    ('일본', '자전거', 'Cyclowired',          ['https://www.cyclowired.jp/rss.xml',
                                               'https://www.cyclowired.jp/feed']),
    ('호주', '자전거', 'Flow Mountain Bike',  ['https://flowmountainbike.com/feed/']),
    # ── 공통 (아웃도어 업계 전반 — 신제품·수입사·M&A) ──
    ('미국', '공통',   'Outside Business Jrnl', ['https://www.outsidebusinessjournal.com/feed/']),
    ('미국', '공통',   'SGB Media',           ['https://sgbonline.com/feed/']),
    ('미국', '공통',   'GearJunkie',          ['https://gearjunkie.com/feed']),
    ('국제', '공통',   'Outdoor Industry',    ['https://outdoorindustry.org/feed/']),
    ('국제', '공통',   'MountainBlog',        ['https://www.mountainblog.it/feed/']),
    ('독일', '공통',   'ISPO',                ['https://www.ispo.com/en/feed',
                                               'https://www.ispo.com/feed']),
    ('독일', '공통',   'outdoor-magazin',     ['https://www.outdoor-magazin.com/rss.xml']),
    ('독일', '공통',   'Bergzeit Magazin',    ['https://www.bergzeit.de/magazin/feed/']),
    ('중국', '공통',   '中国新闻网 体育',       ['https://www.chinanews.com.cn/rss/sports.xml']),
]



# ── 잡음 거르기 (2026-11-28) ────────────────────────────────────────────
# 커머스 글. "deal" 한 단어로 거르면 "Eldora $120M deal" 같은 진짜 업계 뉴스가
# 같이 날아가므로, 상거래 표현만 콕 집는다.
DROP = ('black friday', 'cyber monday', 'gift guide', 'best gifts', 'holiday gift',
        '% off', 'discount code', 'coupon', 'deals:', 'deal of the day', 'on sale',
        'best deals', 'deals for', 'ブラックフライデー', '블랙프라이데이')

# 종합 매체는 우리 주제가 제목에 있어야 받는다.
# (中国新闻网 체육은 농구·축구·무술까지 다 나오고, Traicy는 항공·호텔 매체다)
NEED = {
    '中国新闻网 体育': ('滑雪', '滑冰', '雪', '冰', '登山', '徒步', '自行车', '骑行',
                      '单板', '双板', '越野', '冬奥', '冬运', '索道', '户外'),
    '연합뉴스 스포츠': ('스키', '스노보드', '설상', '빙상', '등산', '산악', '자전거', '사이클',
                      '국립공원', '아웃도어', '캠핑', '동계', '리프트', '슬로프', '설악', '한라', '지리산'),
    '연합뉴스 산업':   ('스키', '아웃도어', '등산', '자전거', '캠핑', '레저', '스포츠용품',
                      '영원무역', '코오롱', '블랙야크', 'K2', '네파', '디스커버리'),
    '연합뉴스 경제':   ('스키', '아웃도어', '등산', '자전거', '캠핑', '레저', '스포츠용품',
                      '영원무역', '코오롱', '블랙야크', '리조트'),
    '연합뉴스 지역':   ('스키장', '설악', '한라', '지리산', '국립공원', '둘레길', '자전거길',
                      '등산', '산행', '케이블카', '눈축제', '빙어'),
    '스포츠경향 레저': ('스키', '스노보드', '등산', '산행', '자전거', '캠핑', '아웃도어', '국립공원'),
    '국립공원공단':   ('탐방', '등산', '산', '설악', '지리', '한라', '입산', '통제', '적설', '안전'),
    '산림청':         ('등산', '산행', '숲길', '입산', '산불', '적설', '둘레길', '휴양림', '안전'),
    'Traicy':        ('スキー', 'スノー', '雪', 'ゲレンデ', '登山', '山', 'アウトドア',
                      '自転車', 'サイクリング', 'リフト', '白馬', 'ニセコ'),
}

def keep(name, title):
    t = title.lower()
    if any(d in t for d in DROP):
        return False
    need = NEED.get(name)
    if need and not any(k in title for k in need):
        return False
    return True

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
    for region, field, name, urls in SOURCES:
        items, why = None, ''
        for u in urls:
            try:
                items = pull(u)
                if items:
                    break
                why = '항목 0개'
            except Exception as e:
                why = f'{type(e).__name__} {str(e)[:50]}'
        if not items:
            report.append(f'  {name:<22} 실패  {why}')
            continue
        n = 0
        dropped = 0
        for pub, title, link in items[:30]:
            if pub and pub < cut:
                continue
            if link in seen:
                continue
            if not keep(name, title):
                dropped += 1
                continue
            seen.add(link)
            fresh.append({'수집일': today.isoformat(),
                          '발행일': pub.date().isoformat() if pub else '',
                          '지역': region, '분야': field, '매체': name, '제목': title, '링크': link})
            n += 1
        report.append(f'  {name:<22} 항목 {len(items):>3}개 · 새 글 {n:>3}개'
                      + (f' · 거름 {dropped}개' if dropped else ''))

    # 변수 이름을 keep 으로 두면 모듈의 keep() 함수를 가려
    # 위 루프의 keep(name, title) 이 UnboundLocalError 로 죽는다(2026-11-28에 당했다).
    kept = [r for r in old
            if not r.get('수집일') or
            (datetime.fromisoformat(r['수집일']).date() + timedelta(days=DAYS)) >= today]
    for r in kept:
        r.setdefault('분야', '공통')
    rows = fresh + kept
    rows.sort(key=lambda r: (r.get('발행일') or r.get('수집일') or ''), reverse=True)

    os.makedirs('research', exist_ok=True)
    with open(OUT, 'w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, ['수집일', '발행일', '지역', '분야', '매체', '제목', '링크'])
        w.writeheader(); w.writerows(rows)

    print('\n'.join(report))
    ok = sum(1 for l in report if '실패' not in l)
    print(f'\n매체 {ok}/{len(SOURCES)} 성공 · 새 글 {len(fresh)}개 · 보관 {len(rows)}개 -> {OUT}')
    if ok == 0:
        # continue-on-error 가 실패를 '성공'으로 덮어 버리므로 로그에 못을 박는다
        print('::error::해외 수집이 한 곳도 성공하지 못했다 — 코드나 네트워크를 확인할 것')
        sys.exit(1)

if __name__ == '__main__':
    main()
