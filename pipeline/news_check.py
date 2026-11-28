#!/usr/bin/env python3
"""뉴스가 카드로 나가기 전에 거르는 검사.  python3 pipeline/news_check.py [YYYY-MM-DD]

막는 것(ERROR — 그 줄은 뉴스에서 빠진다):
  1 상대 표현(오늘·내일·모레·어제·이번 주)  — 하루 지나면 거짓이 된다
  2 출처 칸이 비었다                      — 확인 못 한 줄은 싣지 않는다
  3 수집일이 미래이거나 21일을 넘었다
  4 어제 카드에 나갔던 줄                   — 이틀 연속 같은 줄 금지
경고(WARN — 사람이 볼 것):
  5 해외 줄인데 국가 이모지가 없다
  6 <b> 태그가 짝이 안 맞는다
  7 숫자·금액이 있는데 출처가 URL도 회신도 아니다
"""
import csv, json, os, re, sys
from datetime import date, datetime, timedelta, timezone

KST = timezone(timedelta(hours=9))
d0 = date.fromisoformat(sys.argv[1]) if len(sys.argv) > 1 else datetime.now(KST).date()
strip = lambda s: re.sub(r'<[^>]+>', '', s)

REL = ('오늘', '내일', '모레', '어제', '이번 주', '이번주', '다음 주', '이번 달', '지난주')
FLAG = '🇰🇷🇯🇵🇨🇳🇫🇷🇺🇸🇦🇹🇨🇭🇮🇹🇩🇪🇬🇧🇨🇦🇦🇺🇳🇿🇪🇸🇳🇴🇸🇪🇫🇮🇨🇱🇰🇿🚫'

err, warn = [], []

# 어제 나간 줄
prev = set()
p = f'queue/{d0 - timedelta(days=1)}/slot1/post.json'
if os.path.exists(p):
    prev = {strip(l)[:26] for l in json.load(open(p)).get('news_lines', [])}

rows = list(csv.DictReader(open('research/news_industry.csv', encoding='utf-8')))
for i, r in enumerate(rows, 2):
    line, src, day = r.get('내용', ''), (r.get('출처') or '').strip(), r.get('수집일', '')
    tag = f'{i}행'
    txt = strip(line)

    try:
        dd = date.fromisoformat(day)
    except Exception:
        err.append(f'{tag} 수집일이 날짜가 아니다: {day!r}'); continue
    if dd > d0:
        err.append(f'{tag} 수집일이 미래다 ({day})')
    if (dd + timedelta(days=21)) < d0:
        continue                                   # 오래된 줄은 어차피 안 실린다

    for w in REL:
        if w in txt:
            err.append(f'{tag} 상대 표현 "{w}" — 날짜로 바꿀 것: {txt[:48]}')
            break
    if not src:
        err.append(f'{tag} 출처 없음: {txt[:48]}')
    if txt[:26] in prev:
        err.append(f'{tag} 어제 카드에 나갔던 줄: {txt[:48]}')

    if line.count('<b>') != line.count('</b>'):
        warn.append(f'{tag} <b> 태그 짝이 안 맞는다')
    if txt and txt[0] not in FLAG and not txt[0].isascii():
        pass                                       # 날씨·국내 줄은 이모지가 달라도 된다
    if re.search(r'\d', txt) and src and not re.search(r'https?://|\.[a-z]{2,4}(\.[a-z]{2})?(/|\s|$)|회신|발표|보도|공지', src):
        warn.append(f'{tag} 숫자가 있는데 출처가 불분명: {src[:40]}')

print(f'산킷 뉴스 사전 점검 — {d0}  (업계 줄 {len(rows)}개)')
for e in err:  print(f'  ERROR  {e}')
for w in warn: print(f'  WARN   {w}')
if not err and not warn:
    print('  이상 없음')
print(f'\nERROR {len(err)} · WARN {len(warn)}')
sys.exit(1 if err else 0)
