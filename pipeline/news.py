#!/usr/bin/env python3
"""산킷 뉴스 — 하루치 한 장 카드의 줄을 데이터에서 뽑는다.

사용법:
  python3 pipeline/news.py              오늘 날짜로 줄 뽑아 출력
  python3 pipeline/news.py 2026-11-25   날짜 지정

원칙
- 숫자는 전부 data/latest/*.json 에서 가져온다. 손으로 쓰지 않는다.
- 예보가 없으면 그 줄을 빼고, 있는 척하지 않는다.
- 각 줄은 "주체 + 무엇"으로 쓰고, 핵심 수치만 강조한다(<b>로 감싼다).
"""
import json, sys
from datetime import date, timedelta

WX_N, ETC_N = 3, 7      # 한 장에 싣는 날씨 줄 / 업계·행사 줄 수 (3:7)

SKI = ['용평','하이원','휘닉스','비발디파크','알펜시아','웰리힐리','무주덕유산',
       '곤지암','지산','엘리시안강촌','오크밸리','오투']
MTN = ['설악산','지리산','한라산','북한산','덕유산','속리산','오대산','태백산','소백산']

def load(name):
    return json.load(open(f'data/latest/{name}.json'))

EMO = [
    # (앞에서부터 먼저 맞는 것 하나를 쓴다)
    (('기온 급등','급등'), '🌡️'),
    (('비 예보','비'), '🌧️'),
    (('눈',), '❄️'),
    (('가장 추운',), '🥶'),
    (('최저','영하'), '🎿'),
    (('산불','통제','금지'), '⛔'),
    (('마감','까지'), '⏰'),
    (('헬멧','과태료','의무'), '⛑️'),
    (('개막','부스','박람회','전시'), '🏕️'),
    (('축제','페스티벌'), '🎪'),
    (('리프트','개장','슬로프'), '🚡'),
    (('바람','풍속'), '💨'),
]

def emoji(line):
    t = line.replace('<b>','').replace('</b>','')
    for words, e in EMO:
        if any(w in t for w in words):
            return e
    return '⛰️'

def f(x):
    try: return float(x)
    except (TypeError, ValueError): return None

def build(d0):
    w = load('weather')
    places = w['data']['places']
    base = w['data'].get('base','')
    k = d0.strftime('%Y%m%d')
    k1 = (d0+timedelta(days=1)).strftime('%Y%m%d')
    k2 = (d0+timedelta(days=2)).strftime('%Y%m%d')
    lines = []
    etc = []
    urgent = []

    def day(name, key):
        return places.get(name,{}).get('days',{}).get(key, {})

    # 날씨 줄은 쓸모 있는 순서로 쌓는다: 변화 → 오늘 기온 → 눈
    # 2) 모레까지 기온 급등 / 비
    jumps = []
    for n in SKI:
        a, b = f(day(n,k).get('TMX')), f(day(n,k2).get('TMX'))
        if a is not None and b is not None and b - a >= 8:
            jumps.append((n, a, b, b-a))
    if jumps:
        jumps.sort(key=lambda t: -t[3])
        n,a,b,_ = jumps[0]
        lines.append(f"모레 기온 급등 — {n} 최고 <b>{a:.0f}℃ → {b:.0f}℃</b>, 스키장 <b>{len(jumps)}곳</b>이 같은 흐름")

    rain2 = [n for n in SKI if '비' in ''.join(day(n,k2).get('PTY',[]))]
    if len(rain2) >= 3:   # 한두 곳이면 뉴스가 아니다
        lines.append(f"모레 비 예보 스키장 <b>{len(rain2)}곳</b> — {' · '.join(rain2[:4])}")

    # 1) 오늘 스키장 기온 폭
    tod = [(n, f(day(n,k).get('TMN')), f(day(n,k).get('TMX'))) for n in SKI if day(n,k)]
    tod = [t for t in tod if t[1] is not None]
    if tod:
        cold = min(tod, key=lambda t: t[1])
        warm = max(tod, key=lambda t: t[2] if t[2] is not None else -99)
        lines.append(f"오늘 스키장 최저 <b>{cold[1]:.0f}℃</b> {cold[0]}, 최고 <b>{warm[2]:.0f}℃</b> {warm[0]}")
        sub = [t for t in tod if t[2] is not None and t[2] <= 0]
        if sub:
            lines.append(f"낮에도 영하라 제설 가능한 스키장 <b>{len(sub)}곳</b> — {' · '.join(t[0] for t in sub[:4])}")
        del tod

    # 2-1) 주말 전망 — 독자는 주말 단위로 움직인다
    wk = []
    for i in range(0, 8):
        d = d0 + timedelta(days=i)
        if d.weekday() in (5, 6):
            wk.append(d)
        if len(wk) == 2:
            break
    if wk:
        tx = []
        for n in SKI:
            v = [f(day(n, w.strftime('%Y%m%d')).get('TMX')) for w in wk]
            v = [x for x in v if x is not None]
            if v:
                tx.append((n, max(v)))
        if tx:
            warm = max(tx, key=lambda t: t[1])
            cold = min(tx, key=lambda t: t[1])
            label = "이번 주말" if wk[0] - d0 <= timedelta(days=6) else "주말"
            if warm[1] >= 5:
                lines.append(f"{label} 스키장 최고 <b>{cold[1]:.0f}℃</b> {cold[0]} ~ <b>{warm[1]:.0f}℃</b> {warm[0]} — 포근합니다")
            else:
                lines.append(f"{label} 스키장 최고 <b>{cold[1]:.0f}℃</b> {cold[0]} ~ <b>{warm[1]:.0f}℃</b> {warm[0]}")

    # 3) 오늘·내일 눈
    for key, word in ((k,'오늘'), (k1,'내일')):
        snow = []
        for n in SKI + MTN:
            dd = day(n,key)
            if dd.get('SNO') or '눈' in ''.join(dd.get('PTY',[])):
                amt = dd.get('SNO')[0] if dd.get('SNO') else ''
                snow.append((n, amt))
        if snow:
            s = ' · '.join(f"{n} {a}".strip() for n,a in snow[:3])
            lines.append(f"{word} 눈 — {s}")

    # 4) 산 최저기온
    mt = [(n, f(day(n,k).get('TMN'))) for n in MTN if day(n,k)]
    mt = [t for t in mt if t[1] is not None]
    if mt:
        mt.sort(key=lambda t: t[1])
        if mt[0][1] <= -5:
            lines.append(f"오늘 가장 추운 산 — {mt[0][0]} <b>{mt[0][1]:.0f}℃</b>, {mt[1][0]} <b>{mt[1][1]:.0f}℃</b>")

    # 5) 축제 — 겨울·산·눈 관련만. 전시·연극·예술제는 산킷 독자의 관심사가 아니다.
    KEY = ('눈','얼음','빙어','산타','스키','스노우','스노보드','겨울','송어','트레킹',
           '등산','산악','해맞이','일출','설경','빙벽','썰매','설산')
    DROP = ('연극','뮤지컬','전시','미술','아트','예술','콘서트','클래식','영화','공연','풍물',
            '도서','북','댄스','버스킹','페인팅','공예')
    try:
        fest = load('festivals')['data'] + load('festivals_local')['data']
        ks = d0.strftime('%Y%m%d')
        ke = (d0+timedelta(days=10)).strftime('%Y%m%d')
        soon = []
        for x in fest:
            t = x.get('title','')
            st = (x.get('start') or '').replace('-','')
            en = (x.get('end') or '').replace('-','')
            if not st or not en or st > ke or en < ks:
                continue
            if any(w in t for w in DROP) or not any(w in t for w in KEY):
                continue
            if (int(en) - int(st)) > 1000:   # 연중 상시는 뉴스가 아니다
                continue
            soon.append((st, en, t, x.get('addr','')))
        soon.sort()
        for st, en, t, addr in soon[:2]:
            area = addr.split()[0].replace('특별자치도','').replace('특별시','').replace('광역시','').replace('도','') if addr else ''
            x = f"{area} {t} — <b>{st[4:6]}.{st[6:8]}~{en[4:6]}.{en[6:8]}</b>".strip()
            etc.append(f"{emoji(x)} {x}")
    except Exception:
        pass

    # 6) 손으로 넣는 일정 — research/calendar.csv (날짜,제목)  이번 주 것만
    try:
        import csv
        with open('research/calendar.csv', encoding='utf-8') as fh:
            for row in csv.DictReader(fh):
                st = row['시작'].replace('-','')
                en = (row.get('종료') or row['시작']).replace('-','')
                if st <= (d0+timedelta(days=7)).strftime('%Y%m%d') and en >= d0.strftime('%Y%m%d'):
                    line = f"{emoji(row['내용'])} {row['내용']}"
                    (urgent if en <= (d0+timedelta(days=3)).strftime('%Y%m%d') else etc).append(line)
    except FileNotFoundError:
        pass

    wx = [f"{emoji(l)} {l}" for l in lines]

    # 7) 업계 소식 — research/news_industry.csv (수집일,내용,출처). 이모지는 파일에 직접 쓴다.
    try:
        import csv
        with open('research/news_industry.csv', encoding='utf-8') as fh:
            rows = [r for r in csv.DictReader(fh)
                    if r['수집일'] <= d0.isoformat()
                    and (date.fromisoformat(r['수집일']) + timedelta(days=21)) >= d0]
        industry = [r['내용'] for r in rows]
    except FileNotFoundError:
        pass

    # 대표님 지시(2026-11-25): 날씨와 업계·행사 소식의 비율은 3:7.
    # 사흘 안에 끝나는 일정은 브랜드 소식보다 앞에 둔다. 나머지 일정은 뒤로.
    industry = locals().get('industry', [])
    out = wx[:WX_N] + ['## 업계 · 행사'] + (urgent + industry + etc)[:ETC_N]
    return out, base

if __name__ == '__main__':
    d0 = date.fromisoformat(sys.argv[1]) if len(sys.argv) > 1 else date.today()
    lines, base = build(d0)
    print(f"# 산킷 뉴스 {d0:%-m월 %-d일}  (기상청 발표 {base})")
    for i, l in enumerate(lines, 1):
        print(f"{i:2}. {l}")
    json.dump({"date": d0.isoformat(), "base": base, "lines": lines},
              open('data/latest/news_lines.json','w'), ensure_ascii=False, indent=1)
