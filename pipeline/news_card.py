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

    plain = lambda x: re.sub(r'<[^>]+>', '', x)
    TOP, BOT = 404, 1232
    fs = 33 if len(lines) <= 10 else 30
    per = 38 if fs == 33 else 42
    wraps = [max(1, -(-len(plain(l)) // per)) for l in lines]
    unit = (BOT - TOP) / sum(wraps)
    fs = max(26, min(fs, int(unit * 0.44)))

    rows, y = [], TOP
    for i, l in enumerate(lines):
        t = l.replace('<b>', '<u>').replace('</b>', '</u>')
        rows.append(f'<div class="nr" style="top:{int(y)}px;font-size:{fs}px">'
                    f'<span class="no mono">{i+1:02d}</span>{t}</div>')
        y += unit * wraps[i]

    doc = f'''<!doctype html>
<html lang="ko"><head><meta charset="utf-8"><style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:#ccc;font-family:'Noto Sans CJK KR','Noto Sans CJK JP',sans-serif;padding:40px;width:1160px}}
.card{{width:1080px;height:1350px;position:relative;overflow:hidden;background:#F4F2EC;color:#141615}}
.mono{{font-family:'DejaVu Sans Mono',monospace}}
.wm{{position:absolute;left:56px;top:56px;font-size:30px;font-weight:900;letter-spacing:10px}}
.wm i{{font-style:normal;font-weight:300;letter-spacing:4px;margin-left:10px;font-size:.55em;vertical-align:middle}}
.kit{{position:absolute;right:56px;top:62px;font-size:20px;letter-spacing:3px}}
.rule{{position:absolute;left:56px;right:56px;height:3px;background:#141615}}
.kick{{position:absolute;left:56px;font-size:22px;letter-spacing:3px;color:#8a5521;font-weight:700}}
.head{{position:absolute;left:56px;font-weight:800;letter-spacing:-2px;line-height:1.1;font-size:78px}}
.head em{{font-style:normal;font-size:46px;font-weight:800;letter-spacing:-1px;margin-left:12px}}
.nr{{position:absolute;left:56px;right:52px;font-weight:700;line-height:1.36;letter-spacing:-1px}}
.no{{display:inline-block;width:62px;font-size:.72em;font-weight:700;letter-spacing:1px;color:#8a5521;vertical-align:1px}}
u{{text-decoration:none;border-bottom:3px solid #8a5521;padding-bottom:2px}}
.foot{{position:absolute;left:56px;right:56px;bottom:46px;display:flex;justify-content:space-between;
      font-size:19px;letter-spacing:2px;color:#666;border-top:2px solid #141615;padding-top:16px}}
</style></head><body>
<div class="card" id="s1">
  <div class="wm">SANKIT<i>산킷</i></div>
  <div class="kit mono">NEWS</div>
  <div class="rule" style="top:132px"></div>
  <div class="kick" style="top:176px">오늘의 숫자 · 기상청 단기예보 {when} 발표</div>
  <div class="head" style="top:216px">{d0.month}월 {d0.day}일<em>{WD[d0.weekday()]}요일</em></div>
  <div class="rule" style="top:350px;height:2px"></div>
  {''.join(rows)}
  <div class="foot"><span class="mono">SANKIT · NEWS</span><span>숫자는 기상청 발표 그대로 · 출발 전 공식 공지 확인</span></div>
</div>
</body></html>'''
    open(f'{outdir}/kit.html', 'w', encoding='utf-8').write(doc)
    print('ok', len(lines), 'lines, font', fs)

if __name__ == '__main__':
    d0 = date.fromisoformat(sys.argv[2]) if len(sys.argv) > 2 else date.today()
    main(sys.argv[1], d0)
