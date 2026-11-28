#!/usr/bin/env python3
"""산킷 뉴스 한 장 카드(kit.html).  python3 pipeline/news_card.py <출력폴더> [YYYY-MM-DD]

디자인은 pipeline/assets/card_head.html 의 산킷 체계를 따른다.
종이 #F4F2EC · 먹 #141615 · 러스트 #8a5521 · 숫자와 라벨은 DejaVu Sans Mono.
"""
import glob, json, os, re, sys
from datetime import date

WD = ['월','화','수','목','금','토','일']

# 2026-11-28 운영자 지시: 뉴스 배경을 매일 다르게 — 운영자 드라이브의 산·스키장 사진(assets/news_bg).
# 날짜로 고르므로 같은 날은 같은 사진, 다음 날은 다음 사진(사진 수만큼 돌고 반복).
def pick_bg(d0, outdir):
    bgs = sorted(glob.glob('assets/news_bg/*.jpg'))
    if not bgs or os.environ.get('NEWS_NO_BG') == '1':
        return None
    return os.path.relpath(bgs[d0.toordinal() % len(bgs)], outdir)

BG_CSS = '''
.card.photo{{background:#141615;color:#F4F2EC}}
.card.photo .bgimg{{position:absolute;inset:0;width:100%;height:100%;object-fit:cover}}
.card.photo .shade{{position:absolute;inset:0;background:linear-gradient(180deg,rgba(14,16,15,.12) 0%,rgba(14,16,15,.32) {h1}px,rgba(14,16,15,.76) {h2}px,rgba(14,16,15,.82) 100%)}}
.card.photo .rule{{background:#F4F2EC}}
.card.photo .kick,.card.photo .sec,.card.photo .no{{color:#F2C94C}}
.card.photo .sec span::after{{background:rgba(244,242,236,.28)}}
.card.photo u{{color:#fff}}
.card.photo .head,.card.photo .wm,.card.photo .kit{{text-shadow:0 2px 14px rgba(0,0,0,.45)}}
.card.photo .foot{{color:rgba(244,242,236,.75);border-top-color:#F4F2EC}}
'''

def main(outdir, d0, story=False):
    n = json.load(open('data/latest/news_lines.json'))
    lines = n['lines'][:13]
    base = n.get('base','')
    when = f"{base[8:10]}시" if len(base) >= 10 else "—"

    # 줄 간격은 브라우저가 배분한다(flex space-between). 글자 폭을 추정하지 않는다.
    body = [l for l in lines if not l.startswith('## ')]
    if story:
        CW, CH, TOP, BOT = 1080, 1920, 560, 1640   # 위아래 인스타 UI를 피한다
        fs = 38 if len(body) <= 9 else (34 if len(body) <= 11 else 30)
    else:
        CW, CH, TOP, BOT = 1080, 1350, 398, 1232
        fs = 34 if len(body) <= 9 else (30 if len(body) <= 11 else 27)
    bg = pick_bg(d0, outdir)
    rows, k = [], 0
    for l in lines:
        if l.startswith('## '):
            rows.append(f'<div class="sec"><span class="mono">{l[3:]}</span></div>')
            continue
        k += 1
        t = l.replace('<b>', '<u>').replace('</b>', '</u>')
        rows.append(f'<div class="nr"><span class="no mono">{k:02d}</span><span>{t}</span></div>')

    extra_css = BG_CSS.format(h1=(330 if not story else 500), h2=(430 if not story else 600)).replace('{{','{').replace('}}','}') if bg else ''
    bg_html = f'<img class="bgimg" src="{bg}"><div class="shade"></div>' if bg else ''
    doc = f'''<!doctype html>
<html lang="ko"><head><meta charset="utf-8"><style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:#ccc;font-family:'Noto Sans CJK KR','Noto Sans CJK JP','Noto Color Emoji',sans-serif;padding:40px;width:1160px}}
.card{{width:{CW}px;height:{CH}px;position:relative;overflow:hidden;background:#F4F2EC;color:#141615}}
.mono{{font-family:'DejaVu Sans Mono',monospace}}
.wm{{position:absolute;left:56px;top:56px;font-size:30px;font-weight:900;letter-spacing:10px}}
.wm i{{font-style:normal;font-weight:300;letter-spacing:4px;margin-left:10px;font-size:.55em;vertical-align:middle}}
.kit{{position:absolute;right:56px;top:62px;font-size:20px;letter-spacing:3px}}
.rule{{position:absolute;left:56px;right:56px;height:3px;background:#141615}}
.kick{{position:absolute;left:56px;font-size:22px;letter-spacing:3px;color:#8a5521;font-weight:700}}
.head{{position:absolute;left:56px;font-weight:800;letter-spacing:-2px;line-height:1.1;font-size:78px}}
.head em{{font-style:normal;font-size:46px;font-weight:800;letter-spacing:-1px;margin-left:12px}}
.list{{position:absolute;left:56px;right:52px;top:{TOP}px;bottom:{CH-BOT}px;display:flex;flex-direction:column;justify-content:space-between}}
.sec{{display:flex;align-items:center;gap:14px;font-size:19px;letter-spacing:4px;color:#8a5521;font-weight:700;margin:2px 0 -2px}}
.sec span::after{{content:'';display:inline-block;vertical-align:middle;width:760px;height:2px;background:#d8d3c6;margin-left:14px}}
.nr{{display:flex;align-items:flex-start;gap:4px;font-weight:700;line-height:1.36;letter-spacing:-1px;font-size:{fs}px}}
.no{{flex:0 0 58px;font-size:.72em;font-weight:700;letter-spacing:1px;color:#8a5521;padding-top:.3em}}
u{{text-decoration:none;font-weight:900;color:#141615}}
.foot{{position:absolute;left:56px;right:56px;bottom:46px;display:flex;justify-content:space-between;
      font-size:19px;letter-spacing:2px;color:#666;border-top:2px solid #141615;padding-top:16px}}
{extra_css}</style></head><body>
<div class="card{' photo' if bg else ''}" id="s1">{bg_html}
  <div class="wm">SANKIT<i>산킷</i></div>
  <div class="kit mono">NEWS</div>
  <div class="rule" style="top:{132 if not story else 300}px"></div>
  <div class="kick" style="top:{176 if not story else 344}px">스키장 날씨 · 국내외 업계 소식</div>
  <div class="head" style="top:{216 if not story else 384}px">{d0.month}월 {d0.day}일<em>{WD[d0.weekday()]}요일</em></div>
  <div class="rule" style="top:{350 if not story else 512}px;height:2px"></div>
  <div class="list">{''.join(rows)}</div>
  <div class="foot"><span class="mono">SANKIT · NEWS</span><span>기상청 단기예보 {when} 발표 기준 · 출발 전 공식 공지 확인{' · 배경 ⓒ SANKIT' if bg else ''}</span></div>
</div>
</body></html>'''
    name = 'story.html' if story else 'kit.html'
    open(f'{outdir}/{name}', 'w', encoding='utf-8').write(doc)
    print('ok', len(lines), 'lines, font', fs, '(story)' if story else '')

if __name__ == '__main__':
    d0 = date.fromisoformat(sys.argv[2]) if len(sys.argv) > 2 else date.today()
    main(sys.argv[1], d0)
