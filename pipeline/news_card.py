#!/usr/bin/env python3
"""산킷 뉴스 한 장 카드(kit.html)를 만든다.  python3 pipeline/news_card.py <출력폴더> [날짜]"""
import json, sys, html
from datetime import date

CIRC = "①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭"
WD = ['월','화','수','목','금','토','일']

def main(outdir, d0):
    n = json.load(open('data/latest/news_lines.json'))
    lines = n['lines'][:14]
    base = n.get('base','')
    when = f"{base[8:10]}시 발표" if len(base) >= 10 else ""

    # 글자 수로 줄바꿈을 예측해 칸을 나눈다 — 긴 줄이 아랫줄을 덮지 않게.
    import re as _re
    def plain(x): return _re.sub(r'<[^>]+>', '', x)
    fs = 34 if len(lines) <= 10 else 31
    per = 40 if fs == 34 else 44           # 한 줄에 들어가는 대략의 글자 수
    wraps = [max(1, -(-len(plain(l)) // per)) for l in lines]
    top, avail = 300, 1230 - 300
    unit = avail / sum(wraps)
    fs = max(27, min(fs, int(unit * 0.42)))
    rows, y = [], top
    for i, l in enumerate(lines):
        t = l.replace('<b>', '<u>').replace('</b>', '</u>')
        rows.append(f'<div class="nr" style="top:{int(y)}px;font-size:{fs}px">'
                    f'<span class="no">{CIRC[i]}</span>{t}</div>')
        y += unit * wraps[i]

    doc = f'''<!doctype html><meta charset="utf-8">
<style>
@font-face{{font-family:N;src:local("Noto Sans CJK KR")}}
body{{margin:0;background:#ccc;font-family:'Noto Sans CJK KR',sans-serif;padding:40px;width:1160px}}
.card{{width:1080px;height:1350px;position:relative;overflow:hidden;background:#EDEDEB;color:#141615}}
.ttl{{position:absolute;left:60px;top:150px;font-size:66px;font-weight:900;letter-spacing:-2px}}
.src{{position:absolute;left:62px;top:238px;font-size:24px;font-weight:600;color:#7b7f7c;letter-spacing:-.5px}}
.nr{{position:absolute;left:60px;right:56px;font-weight:700;line-height:1.38;letter-spacing:-1.1px}}
.no{{display:inline-block;width:46px;color:#141615;font-weight:800}}
u{{text-decoration:none;border-bottom:4px solid #141615;padding-bottom:1px}}
.wm{{position:absolute;right:56px;bottom:52px;font-size:34px;font-weight:900;letter-spacing:-1px;opacity:.9}}
.wm i{{font-style:normal;font-size:22px;font-weight:700;margin-left:8px;opacity:.65}}
.ft{{position:absolute;left:60px;bottom:58px;font-size:22px;font-weight:600;color:#7b7f7c;letter-spacing:-.5px;line-height:1.45}}
</style>
<div class="card" id="s1">
  <div class="ttl">( 산킷 뉴스 {d0.month}월 {d0.day}일 )</div>
  <div class="src">{WD[d0.weekday()]}요일 · 기상청 단기예보 {when} 기준</div>
  {''.join(rows)}
  <div class="ft">숫자는 기상청 발표를 그대로 옮긴 것입니다.<br>산에 가시기 전 공식 공지를 한 번 더 확인하세요.</div>
  <div class="wm">SANKIT<i>산킷</i></div>
</div>'''
    open(f'{outdir}/kit.html','w',encoding='utf-8').write(doc)
    print('ok', len(lines), 'lines')

if __name__ == '__main__':
    out = sys.argv[1]
    d0 = date.fromisoformat(sys.argv[2]) if len(sys.argv) > 2 else date.today()
    main(out, d0)
