# 공공누리 제1유형 사진 보관함 채우기 (한국관광공사 포토코리아)
# 사용: python3 pipeline/fetch_photos.py [최대받을장수]
# 받은 사진은 assets/library/, 출처는 assets/library/index.json
import urllib.request, urllib.parse, json, os, re, sys, time
def _key():
    for c in ('/home/claude/anmok/kto/.key', os.path.expanduser('~/anmok/kto/.key'), os.environ.get('KTO_KEY', '')):
        if c and os.path.exists(c): return open(c).read().strip()
        if c and not os.path.sep in c: return c
    raise SystemExit('KTO 키를 찾지 못했습니다')
K = _key()
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
LIB = os.path.join(ROOT, 'assets', 'library')
IDX = os.path.join(LIB, 'index.json')
WANT = ['스키','스노우','설경','설산','눈꽃','상고대','겨울','설천','빙벽','썰매','리조트',
        '등산','산행','트레킹','둘레길','능선','정상','암벽','클라이밍','야영','캠핑','백패킹',
        '국립공원','자연휴양림','케이블카','단풍','계곡','봉','산']
SKIP = ['축제','공연','음식','먹거리','시장','카페','호텔','박물관','미술관','사찰','해수욕장','해변','항구','야경','도심']

def call(page, n=300):
    p = {'serviceKey': K, 'numOfRows': n, 'pageNo': page, 'MobileOS': 'ETC',
         'MobileApp': 'SANKIT', '_type': 'json', 'arrange': 'A'}
    u = "https://apis.data.go.kr/B551011/PhotoGalleryService1/galleryList1?" + urllib.parse.urlencode(p)
    for a in range(4):
        try:
            return json.loads(urllib.request.urlopen(u, timeout=30).read().decode('utf-8', 'replace'))
        except Exception:
            if a == 3: raise
            time.sleep(3 + a * 4)

def slug(s):
    s = re.sub(r'[^0-9A-Za-z가-힣]+', '_', (s or '')).strip('_')
    return (s[:28] or 'photo')

def wanted(it):
    hay = ' '.join(str(it.get(k) or '') for k in ('galTitle', 'galSearchKeyword', 'galPhotographyLocation'))
    if any(b in hay for b in SKIP): return False
    return any(w in hay for w in WANT)

def main(limit=400):
    os.makedirs(LIB, exist_ok=True)
    idx = json.load(open(IDX)) if os.path.exists(IDX) else {}
    have = {v.get('id') for v in idx.values()}
    first = call(1, 1); total = first['response']['body'].get('totalCount', 0)
    print('포토코리아 전체', total, '장 / 보관함', len(idx), '장')
    got = 0; page = 1
    while got < limit and (page - 1) * 300 < total:
        try: b = call(page)['response']['body']
        except Exception as e:
            print('페이지', page, '실패', str(e)[:60]); page += 1; continue
        items = b.get('items') or {}
        items = items.get('item') or []
        if isinstance(items, dict): items = [items]
        for it in items:
            cid = str(it.get('galContentId') or '')
            if not cid or cid in have or not wanted(it): continue
            url = it.get('galWebImageUrl') or ''
            if not url.startswith('https://'): continue
            name = f"{slug(it.get('galTitle'))}_{it.get('galPhotographyMonth') or '000000'}_{cid}.jpg"
            path = os.path.join(LIB, name)
            if os.path.exists(path): have.add(cid); continue
            try:
                data = urllib.request.urlopen(url, timeout=30).read()
            except Exception:
                continue
            if len(data) < 40000: continue
            open(path, 'wb').write(data)
            idx[name] = {'id': cid, 'title': it.get('galTitle'), 'photographer': it.get('galPhotographer'),
                         'month': it.get('galPhotographyMonth'), 'place': it.get('galPhotographyLocation'),
                         'keywords': it.get('galSearchKeyword'), 'license': '공공누리 제1유형',
                         'source': '한국관광공사 포토코리아'}
            have.add(cid); got += 1
            if got >= limit: break
        print('페이지', page, '누적', got); page += 1
    json.dump(idx, open(IDX, 'w'), ensure_ascii=False, indent=1)
    print('새로 받은 사진', got, '장 / 보관함 합계', len(idx))

if __name__ == '__main__':
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 400)
