#!/usr/bin/env python3
"""산킷 뉴스 한 장을 끝까지 만든다 — 줄 뽑기 → 카드 → 사진 → 캡션 → 쓰레드 글.

  python3 pipeline/news_build.py queue/2026-11-26/slot1 [YYYY-MM-DD]

GitHub Actions에서 사람 없이 돌리기 위한 것이다. 숫자는 전부 data/latest 에서 온다.
"""
import json, os, re, subprocess, sys, unicodedata
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import news, news_card

WD = ['월','화','수','목','금','토','일']
BASE_TAGS = ['#산킷뉴스', '#스키장날씨', '#등산날씨', '#스키시즌', '#겨울산', '#아웃도어']
KNOWN = ['용평','하이원','휘닉스','비발디파크','알펜시아','웰리힐리','곤지암','지산',
         '설악산','지리산','한라산','북한산','덕유산','오대산','태백산','소백산']

strip = lambda s: re.sub(r'<[^>]+>', '', s)

def th_len(s):
    n = 0
    for c in s:
        o = ord(c)
        e = (unicodedata.category(c) == "So" or o in (0xFE0F, 0xFE0E, 0x200D)
             or 0x1F000 <= o <= 0x1FAFF or 0x1F3FB <= o <= 0x1F3FF)
        n += len(c.encode("utf-8")) if e else 1
    return n

def main(outdir, d0):
    os.makedirs(outdir, exist_ok=True)
    lines, base = news.build(d0)
    json.dump({"date": d0.isoformat(), "base": base, "lines": lines},
              open('data/latest/news_lines.json', 'w'), ensure_ascii=False, indent=1)
    news_card.main(outdir, d0)

    # 카드 사진
    shot = os.path.join(outdir, '01.png')
    subprocess.run(['node', '-e', f'''
const {{chromium}}=require('playwright');
(async()=>{{const b=await chromium.launch();const p=await b.newPage({{viewport:{{width:1200,height:1500}}}});
await p.goto('file://{os.path.abspath(outdir)}/kit.html');await p.waitForTimeout(900);
await p.locator('#s1').screenshot({{path:'{shot}'}});await b.close();}})()'''], check=True)
    from PIL import Image
    Image.open(shot).convert('RGB').save(os.path.join(outdir, '01.jpg'), 'JPEG', quality=92)
    os.remove(shot)

    wx  = [strip(l) for l in lines if not l.startswith('## ')][:news.WX_N]
    etc = [strip(l) for l in lines if not l.startswith('## ')][news.WX_N:]
    head = f"산킷 뉴스 {d0.month}월 {d0.day}일 {WD[d0.weekday()]}요일 ⛰️"

    hit = [k for k in KNOWN if any(k in l for l in wx + etc)][:5]
    tags = ' '.join(BASE_TAGS + [f"#{k}" for k in hit])

    cap = (f"{head}\n{wx[0].split(' ',1)[-1] if wx else '오늘의 산과 스키장'}\n\n"
           "산킷이 매일 아침 모으는 스키장 날씨와 국내외 업계 소식입니다.\n\n"
           + "\n\n".join(wx) + "\n\n"
           + "— 업계 · 행사 —\n\n" + "\n\n".join(etc) + "\n\n"
           "날씨 숫자는 기상청 단기예보를 그대로 옮긴 것입니다. "
           "산에 가시기 전 공식 공지를 한 번 더 확인하세요.\n\n"
           "매일 아침 이 한 장으로 정리해 드립니다. 저장해 두시면 출발 전에 꺼내 보기 좋습니다.\n\n"
           + tags)

    th = head + "\n\n" + "\n\n".join((wx + etc)[:4]) + "\n\n오늘 어디 가십니까?"
    while th_len(th) > 490 and th.count('\n\n') > 3:
        th = th.rsplit('\n\n', 2)[0] + "\n\n오늘 어디 가십니까?"

    json.dump({"caption": cap, "tags": [], "role": "broad", "format": "E"},
              open(os.path.join(outdir, 'post.json'), 'w'), ensure_ascii=False, indent=1)
    json.dump({"text": th, "image": "01.jpg"},
              open(os.path.join(outdir, 'threads.json'), 'w'), ensure_ascii=False, indent=1)
    print(f"NEWS built {outdir}  날씨 {len(wx)} · 업계 {len(etc)}  쓰레드 {th_len(th)}자")

if __name__ == '__main__':
    d0 = date.fromisoformat(sys.argv[2]) if len(sys.argv) > 2 else date.today()
    main(sys.argv[1], d0)
