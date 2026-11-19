# 스키장 주변 캠핑장 뽑기 (한국관광공사 고캠핑 API, 기존 KTO 키 사용)
# 사용: python3 pipeline/fetch_camping.py "휘닉스 평창" [반경km]
#       python3 pipeline/fetch_camping.py --all      (스키장 전체 요약)
import urllib.request, urllib.parse, json, os, sys, math

def _key():
    for c in ('/home/claude/anmok/kto/.key', os.path.expanduser('~/anmok/kto/.key')):
        if os.path.exists(c): return open(c).read().strip()
    raise SystemExit('KTO 키를 찾지 못했습니다')
K = _key()

RESORTS = {
    '휘닉스 평창': (128.3267, 37.5833), '모나 용평': (128.6803, 37.6444),
    '하이원': (128.8295, 37.2042), '알펜시아': (128.6726, 37.6619),
    '비발디파크': (127.6836, 37.6417), '웰리힐리파크': (128.2461, 37.4408),
    '오크밸리': (127.8747, 37.3503), '곤지암': (127.3100, 37.3406),
    '엘리시안 강촌': (127.6239, 37.8375), '무주 덕유산': (127.7430, 35.8870),
    '지산포레스트': (127.2714, 37.2142), '에덴밸리': (129.0206, 35.4181),
}

def call(op, **kw):
    p = {'serviceKey': K, 'numOfRows': kw.pop('n', 100), 'pageNo': kw.pop('page', 1),
         'MobileOS': 'ETC', 'MobileApp': 'SANKIT', '_type': 'json'}
    p.update(kw)
    u = f"https://apis.data.go.kr/B551011/GoCamping/{op}?" + urllib.parse.urlencode(p)
    import time
    for a in range(4):
        try:
            return json.loads(urllib.request.urlopen(u, timeout=30).read().decode('utf-8', 'replace'))['response']['body']
        except Exception:
            if a == 3: raise
            time.sleep(3 + a * 4)

def items(b):
    it = (b.get('items') or {}).get('item') or []
    return [it] if isinstance(it, dict) else it

def km(x1, y1, x2, y2):
    return math.hypot((x2 - x1) * 88.8, (y2 - y1) * 111.0)

def near(name, radius_km=15):
    x, y = RESORTS[name]
    rows = items(call('locationBasedList', mapX=x, mapY=y, radius=int(radius_km * 1000), n=100))
    out = []
    for r in rows:
        if r.get('manageSttus') != '운영': continue
        try: d = km(x, y, float(r['mapX']), float(r['mapY']))
        except Exception: continue
        out.append({
            '이름': r.get('facltNm'), '거리km': round(d, 1), '유형': r.get('induty'),
            '입지': r.get('lctCl'), '주소': r.get('addr1'), '한줄': r.get('lineIntro'),
            '시설': r.get('sbrsCl'), '운영일': r.get('operDeCl'),
            '화장실': r.get('toiletCo'), '샤워실': r.get('swrmCo'),
            '소화기': r.get('extshrCo'), '화재감지기': r.get('fireSensorCo'),
            '보험': r.get('insrncAt'), '갱신일': r.get('modifiedtime'),
        })
    out.sort(key=lambda r: r['거리km'])
    return out

if __name__ == '__main__':
    a = sys.argv[1:]
    if not a or a[0] == '--all':
        for n in RESORTS:
            rs = near(n)
            mt = [r for r in rs if r['입지'] in ('산', '숲')]
            print(f"{n:12} 운영중 {len(rs):3}곳 (산·숲 {len(mt):2}곳) 가장 가까운 곳 {rs[0]['이름'] if rs else '-'} {rs[0]['거리km'] if rs else ''}km")
    else:
        n = a[0]; r = float(a[1]) if len(a) > 1 else 15
        for c in near(n, r):
            print(f"{c['거리km']:5.1f}km {c['이름'][:22]:24} {str(c['입지']):4} {str(c['유형'])[:8]:9} "
                  f"화{c['화장실']}/샤{c['샤워실']}/소화기{c['소화기']}/감지기{c['화재감지기']} 보험{c['보험']} {str(c['시설'])[:28]}")
