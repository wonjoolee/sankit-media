#!/usr/bin/env python3
"""국내 소식을 네이버 뉴스 검색 API로 모은다.  python3 pipeline/fetch_news_kr.py

국내 매체는 RSS 주소가 자주 바뀌고 없는 곳도 많다. 키워드로 전 매체를 훑는
검색 API 쪽이 빠짐없고 정확하다. 결과는 research/news_feed.csv 에 지역='한국'으로
해외 수집분과 함께 쌓인다(같은 digest, 같은 중복 제거).

필요한 환경변수: NAVER_CLIENT_ID, NAVER_CLIENT_SECRET
없으면 아무것도 하지 않고 조용히 끝낸다(해외 수집은 그대로 돈다).
"""
import csv, html, json, os, re, sys, time, urllib.parse, urllib.request
from datetime import date, datetime, timedelta, timezone
from email.utils import parsedate_to_datetime

ID = os.environ.get('NAVER_CLIENT_ID') or os.environ.get('NCP_API_KEY_ID')
SEC = os.environ.get('NAVER_CLIENT_SECRET') or os.environ.get('NCP_API_KEY')
OUT, DAYS = 'research/news_feed.csv', 14
KST = timezone(timedelta(hours=9))

# (분야, 검색어) — 검색어는 좁게. "스키"만 쓰면 스키점프·연예 기사가 섞인다.
QUERIES = [
    ('스키',   '스키장 개장'), ('스키', '스키장 리프트권'), ('스키', '스노보드 시즌권'),
    ('스키',   '스키 국가대표'), ('스키', '스키장 안전사고'),
    ('하이킹', '국립공원 탐방로'), ('하이킹', '등산 안전사고'), ('하이킹', '산행 통제'),
    ('하이킹', '둘레길 개통'), ('하이킹', '케이블카 산'),
    ('자전거', '자전거길 개통'), ('자전거', '전기자전거 규제'), ('자전거', '자전거 브랜드'),
    ('공통',   '아웃도어 브랜드 수입'), ('공통', '아웃도어 신제품'), ('공통', '등산복 출시'),
    ('공통',   '캠핑 용품 출시'),
]
# 제목에 이것이 없으면 버린다 — 검색어가 본문에만 스쳐 지나간 기사를 막는다
NEED = ('스키', '보드', '설상', '리프트', '슬로프', '등산', '산행', '탐방', '국립공원',
        '둘레길', '케이블카', '자전거', '라이딩', '아웃도어', '캠핑', '등산복', '산악')
DROP = ('분양', '부동산', '주가', '코인', '카지노', '성형', '대출', '보험')

clean = lambda t: html.unescape(re.sub(r'<[^>]+>', '', t)).strip()

# 네이버 검색 API는 두 갈래다.
#  1) NAVER API HUB (네이버 클라우드 플랫폼으로 이전된 신규)  — NCP 헤더
#  2) 구 오픈 API (developers.naver.com)                    — X-Naver 헤더
# 어느 쪽 키인지 알 수 없으므로 둘 다 시도하고, 통하는 쪽을 기억해 쓴다.
ENDPOINTS = [
    ('API HUB', 'https://naverapihub.apigw.ntruss.com/search/v1/news',
     lambda: {'X-NCP-APIGW-API-KEY-ID': ID, 'X-NCP-APIGW-API-KEY': SEC}),
    ('구 오픈API', 'https://openapi.naver.com/v1/search/news.json',
     lambda: {'X-Naver-Client-Id': ID, 'X-Naver-Client-Secret': SEC}),
]
_use = None          # 한 번 통한 엔드포인트를 기억한다

def search(q, display=50):
    global _use
    qs = urllib.parse.urlencode({'query': q, 'display': display, 'sort': 'date'})
    last = None
    for name, base, hdr in ([_use] if _use else ENDPOINTS):
        try:
            r = urllib.request.Request(base + '?' + qs, headers=hdr())
            with urllib.request.urlopen(r, timeout=20) as resp:
                data = json.loads(resp.read())
            if _use is None:
                _use = (name, base, hdr)
                print(f'[네이버] {name} 사용')
            return data.get('items', [])
        except Exception as e:
            last = f'{name}: {type(e).__name__} {str(e)[:60]}'
    raise RuntimeError(last or 'unknown')

def main():
    if not (ID and SEC):
        print('NAVER_CLIENT_ID / NAVER_CLIENT_SECRET 없음 — 국내 수집 건너뜀')
        return
    today = datetime.now(KST).date()
    cut = datetime.now(timezone.utc) - timedelta(days=DAYS)

    old = list(csv.DictReader(open(OUT, encoding='utf-8'))) if os.path.exists(OUT) else []
    seen = {r['링크'] for r in old}

    fresh, report = [], []
    for field, q in QUERIES:
        try:
            items = search(q)
        except Exception as e:
            report.append(f'  {q:<18} 실패 {type(e).__name__} {str(e)[:50]}')
            continue
        n = 0
        for it in items:
            title, link = clean(it.get('title', '')), (it.get('originallink') or it.get('link', ''))
            if not title or not link or link in seen:
                continue
            if not any(k in title for k in NEED) or any(d in title for d in DROP):
                continue
            try:
                pub = parsedate_to_datetime(it.get('pubDate', ''))
            except Exception:
                pub = None
            if pub and pub < cut:
                continue
            seen.add(link)
            host = urllib.parse.urlparse(link).netloc.replace('www.', '')
            fresh.append({'수집일': today.isoformat(),
                          '발행일': pub.date().isoformat() if pub else '',
                          '지역': '한국', '분야': field, '매체': host,
                          '제목': title, '링크': link})
            n += 1
        report.append(f'  {q:<18} 결과 {len(items):>3}개 · 새 글 {n:>3}개')
        time.sleep(0.3)

    keep = [r for r in old if not r.get('수집일') or
            (date.fromisoformat(r['수집일']) + timedelta(days=DAYS)) >= today]
    rows = fresh + keep
    rows.sort(key=lambda r: (r.get('발행일') or r.get('수집일') or ''), reverse=True)
    with open(OUT, 'w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, ['수집일', '발행일', '지역', '분야', '매체', '제목', '링크'])
        w.writeheader(); w.writerows(rows)
    print('\n'.join(report))
    print(f'\n국내 새 글 {len(fresh)}개 · 보관 {len(rows)}개 -> {OUT}')

if __name__ == '__main__':
    main()
