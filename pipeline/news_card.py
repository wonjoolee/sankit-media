#!/usr/bin/env python3
"""산킷 뉴스 한 장 카드(kit.html).  python3 pipeline/news_card.py <출력폴더> [YYYY-MM-DD]

디자인은 pipeline/assets/card_head.html 의 산킷 체계를 따른다.
종이 #F4F2EC · 먹 #141615 · 러스트 #8a5521 · 숫자와 라벨은 DejaVu Sans Mono.
"""
import json, re, sys
from datetime import date

WD = ['월','화','수','목','금','토','일']

def main(outdir, d0):
    n = json.load(open('data/latest/news_lines.json'))
    lines = n['lines'][:13]
    base = n.get('base','')
    when = f"{base[8:10]}시" if len(base) >= 10 else "—"

    # 줄 간격은 브라우저가 배분한다(flex space-between). 글자 폭을 추정하지 않는다.
    body = [l for l in lines if not l.startswith('## ')]
    fs = 34 if len(body) <= 9 else (30 if len(body) <= 11 else 27)
    rows, k = [], 0
    for l in lines:
        if l.startswith('## '):
            rows.append(f'<div class="sec"><span class="mono">{l[3:]}</span></div>')
            continue
        k += 1
        t = l.replace('<b>', '<u>').replace('</b>', '</u>')
        rows.append(f'<div class="nr"><span class="no mono">{k:02d}</span><span>{t}</span></div>')

    doc = f'''<!doctype html>
<html lang="ko"><head><meta charset="utf-8"><style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:#ccc;font-family:'Noto Sans CJK KR','Noto Sans CJK JP','Noto Color Emoji',sans-serif;padding:40px;width:1160px}}
.card{{width:1080px;height:1350px;position:relative;overflow:hidden;background:#F4F2EC;color:#141615}}
.mono{{font-family:'DejaVu Sans Mono',monospace}}
.wm{{position:absolute;left:56px;top:56px;font-size:30px;font-weight:900;letter-spacing:10px}}
.wm i{{font-style:normal;font-weight:300;letter-spacing:4px;margin-left:10px;font-size:.55em;vertical-align:middle}}
.kit{{position:absolute;right:56px;top:62px;font-size:20px;letter-spacing:3px}}
.rule{{position:absolute;left:56px;right:56px;height:3px;background:#141615}}
.kick{{position:absolute;left:56px;font-size:22px;letter-spacing:3px;color:#8a5521;font-weight:700}}
.head{{position:absolute;left:56px;font-weight:800;letter-spacing:-2px;line-height:1.1;font-size:78px}}
.head em{{font-style:normal;font-size:46px;font-weight:800;letter-spacing:-1px;margin-left:12px}}
.list{{position:absolute;left:56px;right:52px;top:398px;bottom:116px;display:flex;flex-direction:column;justify-content:space-between}}
.sec{{display:flex;align-items:center;gap:14px;font-size:19px;letter-spacing:4px;color:#8a5521;font-weight:700;margin:2px 0 -2px}}
.sec span::after{{content:'';display:inline-block;vertical-align:middle;width:760px;height:2px;background:#d8d3c6;margin-left:14px}}
.nr{{display:flex;align-items:flex-start;gap:4px;font-weight:700;line-height:1.36;letter-spacing:-1px;font-size:{fs}px}}
.no{{flex:0 0 58px;font-size:.72em;font-weight:700;letter-spacing:1px;color:#8a5521;padding-top:.3em}}
u{{text-decoration:none;border-bottom:3px solid #8a5521;padding-bottom:2px}}
.foot{{position:absolute;left:56px;right:56px;bottom:46px;display:flex;justify-content:space-between;
      font-size:19px;letter-spacing:2px;color:#666;border-top:2px solid #141615;padding-top:16px}}
</style></head><body>
<div class="card" id="s1">
  <div class="wm">SANKIT<i>산킷</i></div>
  <div class="kit mono">NEWS</div>
  <div class="rule" style="top:132px"></div>
  <div class="kick" style="top:176px">스키장 날씨 · 국내외 업계 소식</div>
  <div class="head" style="top:216px">{d0.month}월 {d0.day}일<em>{WD[d0.weekday()]}요일</em></div>
  <div class="rule" style="top:350px;height:2px"></div>
  <div class="list">{''.join(rows)}</div>
  <div class="foot"><span class="mono">SANKIT · NEWS</span><span>기상청 단기예보 {when} 발표 기준 · 출발 전 공식 공지 확인</span></div>
</div>
</body></html>'''
    open(f'{outdir}/kit.html', 'w', encoding='utf-8').write(doc)
    print('ok', len(lines), 'lines, font', fs)

if __name__ == '__main__':
    d0 = date.fromisoformat(sys.argv[2]) if len(sys.argv) > 2 else date.today()
    main(sys.argv[1], d0)
