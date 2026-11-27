#!/usr/bin/env python3
"""그날 모은 뉴스를 한 장으로 정리한다.  python3 pipeline/news_digest.py [YYYY-MM-DD]

- research/news_feed.csv  : RSS로 자동 수집한 후보 풀
- research/news_industry.csv : 사람이 확인해 뽑아 둔 줄
- data/latest/news_lines.json : 오늘 카드에 실제로 실린 줄
결과는 research/digest_YYYY-MM-DD.md 로 저장하고 화면에도 찍는다.
"""
import csv, json, os, re, sys, collections
from datetime import date, datetime, timedelta, timezone

KST = timezone(timedelta(hours=9))          # 러너는 UTC다. 날짜는 반드시 KST로 잡는다.
d0 = date.fromisoformat(sys.argv[1]) if len(sys.argv) > 1 else datetime.now(KST).date()
strip = lambda s: re.sub(r'<[^>]+>', '', s)

feed = list(csv.DictReader(open('research/news_feed.csv', encoding='utf-8'))) \
       if os.path.exists('research/news_feed.csv') else []
ind = list(csv.DictReader(open('research/news_industry.csv', encoding='utf-8'))) \
      if os.path.exists('research/news_industry.csv') else []
lines = json.load(open('data/latest/news_lines.json'))['lines'] \
        if os.path.exists('data/latest/news_lines.json') else []

today = [r for r in feed if r['수집일'] == d0.isoformat()]
recent = [r for r in feed if r.get('발행일', '') >= (d0 - timedelta(days=2)).isoformat()]
used = {strip(r['내용'])[:24] for r in ind}

out = [f'# 산킷 뉴스 수집 요약 — {d0}', '']
out.append(f'자동 수집 **{len(feed)}건 보관** · 오늘 새로 **{len(today)}건** · 최근 48시간 발행 **{len(recent)}건**')
by = collections.Counter(r['지역'] for r in recent)
out.append('지역별(48시간): ' + ' · '.join(f'{k} {v}' for k, v in by.most_common()) or '없음')
out.append('')

out.append('## 오늘 카드에 실린 줄')
if lines:
    for l in lines:
        out.append(('### ' + l[3:]) if l.startswith('## ') else f'- {strip(l)}')
else:
    out.append('- (news_lines.json 없음)')
out.append('')

out.append('## 아직 안 쓴 후보 — 최근 48시간')
n = 0
for r in sorted(recent, key=lambda x: x.get('발행일', ''), reverse=True):
    if any(k and k[:16].lower() in r['제목'].lower() for k in used):
        continue
    out.append(f"- [{r['지역']}·{r['매체']}] {r['제목']}  \n  {r['링크']}")
    n += 1
    if n >= 25:
        break
if n == 0:
    out.append('- 없음')
out.append('')
out.append(f'> 이 목록은 **후보**다. 사실 확인 전에는 카드에 싣지 않는다.')

txt = '\n'.join(out)
os.makedirs('research', exist_ok=True)
open(f'research/digest_{d0}.md', 'w', encoding='utf-8').write(txt)
print(txt)
